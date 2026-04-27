from django.conf import settings

# Default configuration values for the app
DEFAULTS = {
    # Map DRF actions to Django permission actions
    # Used to convert viewset actions (list, create, update, etc.) into
    # the corresponding permission codename suffix (view, add, change, delete).
    'ACTION_PERMISSION_MAP': {
        'list': 'view',
        'retrieve': 'view',
        'create': 'add',
        'update': 'change',
        'partial_update': 'change',
        'destroy': 'delete',
    },

    # Field name used to determine object ownership (e.g., 'user', 'owner').
    # The permission class will automatically grant permissions defined in
    # OWNER_AUTO_PERMISSIONS to the user who owns the object.
    'OWNERSHIP_FIELD': 'user',

    # Actions (permission types) that owners automatically receive.
    # For example, if OWNERSHIP_FIELD='user', the user who owns the object
    # will be able to view, change, and delete it without explicit permissions.
    'OWNER_AUTO_PERMISSIONS': ['view', 'change', 'delete'],

    # Allow create action if the ownership field in the request data matches
    # the current user's ID. If set to False, create will require the 'add'
    # permission even if the user tries to set themselves as the owner.
    'ALLOW_CREATE_ON_OWNERSHIP': True,

    # Cache TTL for per‑object permissions (in seconds).
    # This affects caching of UserPermission lookups for individual objects.
    'CACHE_TTL': 300,  # 5 minutes

    # Safe methods per model: {model_name: ['list', 'retrieve', ...]}
    # These override permission checks and allow public access to specific
    # actions on a model, even for unauthenticated users.
    # Example: {'publicdocument': ['list', 'retrieve']}
    'MODEL_SAFE_METHODS': {},

    # Whether to automatically create missing permissions (add, change, delete, view)
    # when running migrations. This is handled by the sync_user_permissions command,
    # but the setting can be used to control behaviour programmatically.
    'AUTO_CREATE_PERMISSIONS': True,

    # Enable dynamic safe method lookup from a database model (e.g., your existing
    # ModelMethod table). When True, the permission class will also attempt to fetch
    # safe methods from the database using the _fetch_safe_methods_from_db() method.
    # The results are cached using the same CACHE_TTL. Disabled by default for performance.
    'USE_DB_SAFE_METHODS': False,
}

class UserPermissionsSettings:
    """
    Access app settings with defaults. Usage:
        from django_user_permissions.settings import user_permissions_settings
        ttl = user_permissions_settings.CACHE_TTL

    Settings are read‑only. To change them, define a USER_PERMISSIONS dictionary
    in your project's settings.py. Example:

        USER_PERMISSIONS = {
            'OWNERSHIP_FIELD': 'created_by',
            'CACHE_TTL': 600,
            'USE_DB_SAFE_METHODS': True,
        }
    """
    def __getattr__(self, name):
        if name in DEFAULTS:
            # Check project settings for USER_PERMISSIONS dict
            user_settings = getattr(settings, 'USER_PERMISSIONS', {})
            return user_settings.get(name, DEFAULTS[name])
        raise AttributeError(f"'UserPermissionsSettings' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        raise AttributeError("Settings are read‑only. Use Django's USER_PERMISSIONS dict instead.")

# Singleton instance for easy import
user_permissions_settings = UserPermissionsSettings()