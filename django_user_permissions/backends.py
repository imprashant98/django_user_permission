from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
from .utils import get_user_permissions_for_object
from .settings import user_permissions_settings


class UserSpecificPermissionBackend(ModelBackend):
    """
    Authentication backend that checks:
    1. Django's built-in global permissions (via super()).
    2. Per-object permissions stored in UserPermission model (if obj is provided).
    
    This backend should be placed BEFORE the default ModelBackend in
    AUTHENTICATION_BACKENDS to allow per-object overrides.
    """

    def has_perm(self, user_obj, perm, obj=None):
        """
        Return True if user has the permission (global or per‑object).
        """
        if not user_obj.is_active:
            return False

        # Superuser has all permissions
        if user_obj.is_superuser:
            return True

        # 1. Check global permissions (includes groups and user.user_permissions)
        if super().has_perm(user_obj, perm, obj=None):
            return True

        # 2. If an object is provided, check per‑object permissions
        if obj is not None:
            # Use cached helper to get all permission codenames for this user on this object
            perms_for_object = get_user_permissions_for_object(user_obj, obj)
            if perm in perms_for_object:
                return True

            # Optional: if the permission is a Django generic permission like
            # "change_{model}" and we have a per‑object permission stored with
            # the same codename, it's already covered above.
            # No extra logic needed.

        return False

    def has_module_perms(self, user_obj, app_label):
        """
        Per‑app permissions: rely on global backend logic.
        For object‑specific permissions, we don't override this.
        """
        if not user_obj.is_active:
            return False
        if user_obj.is_superuser:
            return True
        return super().has_module_perms(user_obj, app_label)

    def get_all_permissions(self, user_obj, obj=None):
        """
        Return a set of all permission codenames for the user, optionally filtered by object.
        Used by Django's permission system.
        """
        if not user_obj.is_active:
            return set()
        if user_obj.is_superuser:
            # Return all permissions known to the system (expensive, but standard)
            # For performance, you might want to cache this per user.
            from django.contrib.auth.models import Permission
            perms = Permission.objects.values_list('codename', flat=True)
            return set(perms)

        # Start with global permissions
        perms = super().get_all_permissions(user_obj, obj=None)

        # Add per‑object permissions if object is given
        if obj is not None:
            perms.update(get_user_permissions_for_object(user_obj, obj))

        return perms