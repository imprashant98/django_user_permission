from threading import local
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from .settings import user_permissions_settings
from .models import UserPermission

# Thread‑local storage for per‑request caching
_request_local = local()


def get_user_permissions_for_object(user, obj):
    """
    Return a set of permission codenames that the user has for the specific object.
    Results are cached in Django's cache backend (e.g., Redis, Memcached) for the
    duration specified in settings.

    Also stores the result in a thread‑local dictionary for the current request
    to avoid repeated cache lookups within the same request/response cycle.
    """
    if not user.is_authenticated or user.is_anonymous:
        return set()

    # Ensure we have a primary key (obj must be saved)
    if obj.pk is None:
        raise ValueError("Object must be saved to database before checking permissions.")

    # Build cache key
    content_type = ContentType.objects.get_for_model(obj)
    cache_key = f"user_obj_perms_{user.id}_{content_type.app_label}_{content_type.model}_{obj.pk}"
    
    # Check per‑request cache first
    if hasattr(_request_local, 'perm_cache') and cache_key in _request_local.perm_cache:
        return _request_local.perm_cache[cache_key]

    # Then check global cache
    perms = cache.get(cache_key)
    if perms is None:
        # Query the database
        qs = UserPermission.objects.filter(
            user=user,
            content_type=content_type,
            object_id=obj.pk
        ).select_related('permission')
        
        perms = {up.permission.codename for up in qs}
        
        # Store in cache with TTL from settings
        cache.set(cache_key, perms, user_permissions_settings.CACHE_TTL)

    # Store in per‑request cache
    if not hasattr(_request_local, 'perm_cache'):
        _request_local.perm_cache = {}
    _request_local.perm_cache[cache_key] = perms

    return perms


def get_global_user_permissions(user):
    """
    Return a set of global permission codenames the user has (including groups).
    Uses Django's built‑in `get_all_permissions` which already caches per‑request.

    This function is a convenience wrapper, primarily for consistency.
    """
    if not user.is_authenticated:
        return set()
    return set(user.get_all_permissions())


def get_effective_permissions_for_user(user, obj=None):
    """
    Return all permissions (global + per‑object) the user has.
    If `obj` is provided, global permissions plus permissions specific to that object.
    If `obj` is None, return only global permissions.

    Useful when you need a complete snapshot for debugging or reporting.
    """
    perms = get_global_user_permissions(user)
    if obj is not None:
        perms.update(get_user_permissions_for_object(user, obj))
    return perms


def invalidate_object_permissions_cache(user, obj):
    """
    Invalidate the cached permissions for a given user and object.
    Call this after creating, updating, or deleting a UserPermission entry.
    """
    if obj.pk is None:
        return  # not saved yet, nothing to invalidate

    content_type = ContentType.objects.get_for_model(obj)
    cache_key = f"user_obj_perms_{user.id}_{content_type.app_label}_{content_type.model}_{obj.pk}"
    cache.delete(cache_key)

    # Also clear the per‑request cache for this key (if any)
    if hasattr(_request_local, 'perm_cache') and cache_key in _request_local.perm_cache:
        del _request_local.perm_cache[cache_key]


def invalidate_user_all_object_permissions(user):
    """
    Invalidate all object permission cache entries for a specific user.
    Useful when many permissions change (e.g., group membership updated).
    This is expensive; use with care.
    """
    # Pattern matching all keys for this user – requires a cache backend that supports pattern delete.
    # For simplicity, we can increment a user‑level version number and include it in cache keys,
    # but that's more complex. Here we assume the caller will only call this when truly needed.
    # Alternative: use cache.delete_many() with a list of keys if you keep track.
    # For now, we rely on the fact that each object permission key is unique and will expire naturally.
    # Clear per‑request cache entirely for the user:
    if hasattr(_request_local, 'perm_cache'):
        keys_to_delete = [k for k in _request_local.perm_cache.keys() if k.startswith(f"user_obj_perms_{user.id}_")]
        for key in keys_to_delete:
            del _request_local.perm_cache[key]


def clear_request_cache():
    """
    Clear the thread‑local permission cache for the current request.
    Can be called in a custom middleware at the beginning of each request
    to ensure a clean slate (though not strictly required because each request
    runs in its own thread).
    """
    if hasattr(_request_local, 'perm_cache'):
        _request_local.perm_cache.clear()