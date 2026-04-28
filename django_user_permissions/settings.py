from django.conf import settings

DEFAULTS = {
    'ACTION_PERMISSION_MAP': {
        'list': 'view',
        'retrieve': 'view',
        'create': 'add',
        'update': 'change',
        'partial_update': 'change',
        'destroy': 'delete',
    },
    'OWNERSHIP_FIELD': 'user',
    'OWNER_AUTO_PERMISSIONS': ['view', 'change', 'delete'],
    'ALLOW_CREATE_ON_OWNERSHIP': True,
    'ALLOW_OBJECT_LEVEL_ACTIONS': ['retrieve', 'update', 'partial_update', 'destroy'],
    'LIST_ALLOW_EMPTY': True,
    'CACHE_TTL': 300,
    'MODEL_SAFE_METHODS': {},
    'USE_DB_SAFE_METHODS': False,
    'AUTO_CREATE_PERMISSIONS': True,
}

class UserPermissionsSettings:
    def __getattr__(self, name):
        if name in DEFAULTS:
            user_settings = getattr(settings, 'USER_PERMISSIONS', {})
            return user_settings.get(name, DEFAULTS[name])
        raise AttributeError(f"'UserPermissionsSettings' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        raise AttributeError("Settings are read‑only. Use Django's USER_PERMISSIONS dict instead.")

user_permissions_settings = UserPermissionsSettings()