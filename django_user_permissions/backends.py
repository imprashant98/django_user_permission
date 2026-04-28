from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from .utils import get_user_permissions_for_object


class UserSpecificPermissionBackend(ModelBackend):
    """
    Authentication backend that checks:
    1. Django's built‑in global permissions (user.user_permissions + groups).
    2. Per‑object permissions stored in UserPermission model (if obj is provided).

    This backend should be placed BEFORE the default ModelBackend in
    AUTHENTICATION_BACKENDS, but it is self‑contained and does not call super().
    """

    def has_perm(self, user_obj, perm, obj=None):
        """
        Return True if the user has the specified permission, either globally or
        per‑object.

        Args:
            user_obj: The user instance being checked.
            perm: Permission codename (e.g., 'view_post').
            obj: Optional object instance for object‑level permissions.

        Returns:
            bool: True if the user is allowed, False otherwise.
        """
        if not user_obj.is_active:
            return False

        if user_obj.is_superuser:
            return True

        # 1. Check global permissions (user.user_permissions + groups)
        if perm in self._get_global_permissions(user_obj):
            return True

        # 2. If an object is provided, check per‑object permissions
        if obj is not None:
            if perm in get_user_permissions_for_object(user_obj, obj):
                return True

        return False

    def has_module_perms(self, user_obj, app_label):
        """
        Check if the user has any permission in the given app label.
        """
        if not user_obj.is_active:
            return False
        if user_obj.is_superuser:
            return True
        # Check if any global permission codename starts with app_label
        return any(perm.split('.')[-1] for perm in self._get_global_permissions(user_obj)
                   if perm.startswith(app_label + '.'))

    def get_all_permissions(self, user_obj, obj=None):
        """
        Return a set of all permission codenames (global + per‑object) for the user.
        """
        perms = self._get_global_permissions(user_obj).copy()
        if obj is not None:
            perms.update(get_user_permissions_for_object(user_obj, obj))
        return perms

    def _get_global_permissions(self, user_obj):
        """
        Return a set of permission codenames from user.user_permissions and groups.
        Uses caching via user_obj._perm_cache for performance.
        """
        # Return cached value if present
        if hasattr(user_obj, '_perm_cache') and user_obj._perm_cache is not None:
            return user_obj._perm_cache

        perms = set()
        # Direct user permissions
        perms.update(user_obj.user_permissions.values_list('codename', flat=True))
        # Permissions from groups
        for group in user_obj.groups.all():
            perms.update(group.permissions.values_list('codename', flat=True))

        # Cache for the current request
        user_obj._perm_cache = perms
        return perms