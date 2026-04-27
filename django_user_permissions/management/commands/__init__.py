"""
django_user_permissions – Reusable Django package for user‑specific permissions with per‑object support.

Provides:
- UserPermission model for per‑object and model‑wide user permissions.
- Custom authentication backend that checks per‑object permissions.
- DRF permission class (UserSpecificPermission) and viewset mixin.
- Caching utilities and signal handlers for cache invalidation.
- Management command to sync basic view/add/change/delete permissions.

Usage:
    Add to INSTALLED_APPS, set AUTHENTICATION_BACKENDS, and use the mixin in your DRF viewsets.
    See the documentation for full details.
"""


# Expose main public API
from .models import UserPermission
from .backends import UserSpecificPermissionBackend
from .permissions import UserSpecificPermission
from .mixins import UserSpecificPermissionMixin
from .settings import user_permissions_settings
from .utils import (
    get_user_permissions_for_object,
    get_global_user_permissions,
    get_effective_permissions_for_user,
    invalidate_object_permissions_cache,
    clear_request_cache,
)

__all__ = [
    'UserPermission',
    'UserSpecificPermissionBackend',
    'UserSpecificPermission',
    'UserSpecificPermissionMixin',
    'user_permissions_settings',
    'get_user_permissions_for_object',
    'get_global_user_permissions',
    'get_effective_permissions_for_user',
    'invalidate_object_permissions_cache',
    'clear_request_cache',
]