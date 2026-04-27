from rest_framework.permissions import BasePermission
from django.core.cache import cache
from .utils import get_user_permissions_for_object
from .settings import user_permissions_settings


class UserSpecificPermission(BasePermission):
    """
    DRF permission class that enforces:
    - Superuser full access.
    - Global permissions (groups + user.user_permissions) via Django's backend.
    - Per‑object permissions stored in UserPermission model.
    - Ownership rules (e.g., a user can edit their own profile).
    - Safe method overrides (static or dynamic from database).

    Works with any DRF viewset or APIView that uses `get_serializer_class()` or
    has a `queryset` attribute to determine the model.
    """

    def _get_action(self, view, request):
        """
        Determine internal action name from viewset action or HTTP method.
        Returns one of: 'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy',
        or the custom action name (e.g., 'export') if present.
        """
        # If viewset has an .action attribute (e.g., @action decorator)
        if hasattr(view, 'action') and view.action is not None:
            return view.action
        # Otherwise map HTTP method to default actions
        method = request.method.lower()
        method_map = {
            'get': 'retrieve',
            'post': 'create',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
        }
        # Distinguish between list and retrieve for GET
        if method == 'get' and hasattr(view, 'action') and view.action == 'list':
            return 'list'
        if method == 'get':
            return method_map.get(method, method)
        return method_map.get(method, method)

    def get_model_class(self, view):
        """
        Resolve the model class from the view's queryset or serializer Meta.
        """
        if hasattr(view, 'queryset') and view.queryset is not None:
            return view.queryset.model
        if hasattr(view, 'get_serializer_class'):
            serializer = view.get_serializer_class()
            if hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'model'):
                return serializer.Meta.model
        return None

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        action = self._get_action(view, request)
        model_cls = self.get_model_class(view)
        if not model_cls:
            return False

        model_name = model_cls._meta.model_name
        required_action = user_permissions_settings.ACTION_PERMISSION_MAP.get(action)

        if required_action is None:
            return self._check_safe_method_override(request, model_name, action)

        perm_codename = f"{required_action}_{model_name}"

        # Global permission check
        if request.user.has_perm(perm_codename):
            return True

        # Create action with ownership check
        if action == 'create' and user_permissions_settings.ALLOW_CREATE_ON_OWNERSHIP:
            return self._check_create_ownership(request)

        # Safe method override
        if self._check_safe_method_override(request, model_name, action):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        action = self._get_action(view, request)
        model_cls = obj.__class__
        model_name = model_cls._meta.model_name
        required_action = user_permissions_settings.ACTION_PERMISSION_MAP.get(action)

        if required_action is None:
            return self._check_safe_method_override(request, model_name, action)

        perm_codename = f"{required_action}_{model_name}"

        # Global permission
        if request.user.has_perm(perm_codename):
            return True

        # Per‑object permission
        object_perms = get_user_permissions_for_object(request.user, obj)
        if perm_codename in object_perms:
            return True

        # Ownership rule
        owner_field = user_permissions_settings.OWNERSHIP_FIELD
        if owner_field and hasattr(obj, owner_field):
            owner = getattr(obj, owner_field)
            if owner == request.user:
                if required_action in user_permissions_settings.OWNER_AUTO_PERMISSIONS:
                    return True

        # Safe method override
        if self._check_safe_method_override(request, model_name, action):
            return True

        return False

    def _check_safe_method_override(self, request, model_name, action):
        """
        Check static safe methods first (MODEL_SAFE_METHODS setting).
        If enabled (USE_DB_SAFE_METHODS = True), also check dynamic database model.
        Results from DB are cached.
        """
        # 1. Static configuration (default, recommended)
        safe_methods = user_permissions_settings.MODEL_SAFE_METHODS.get(model_name, [])
        if action in safe_methods or request.method.lower() in safe_methods:
            return True

        # 2. Optional dynamic database lookup (disabled by default)
        if user_permissions_settings.USE_DB_SAFE_METHODS:
            cache_key = f"safe_methods_db_{model_name}"
            db_methods = cache.get(cache_key)
            if db_methods is None:
                db_methods = self._fetch_safe_methods_from_db(model_name)
                cache.set(cache_key, db_methods, user_permissions_settings.CACHE_TTL)
            if action in db_methods or request.method.lower() in db_methods:
                return True

        return False

    def _fetch_safe_methods_from_db(self, model_name):
        """
        Override this method to integrate with your existing ModelMethod model.
        Example implementation for your original code with a 'ModelMethod' table:
        
        from setting.models import ModelMethod
        qs = ModelMethod.objects.filter(model_name__model_name__iexact=model_name)
        return list(qs.values_list('method__name', flat=True))
        """
        # Default: return empty list (no dynamic safe methods)
        return []

    def _check_create_ownership(self, request):
        owner_field = user_permissions_settings.OWNERSHIP_FIELD
        if not owner_field:
            return True
        if owner_field in request.data:
            return str(request.data[owner_field]) == str(request.user.id)
        return True