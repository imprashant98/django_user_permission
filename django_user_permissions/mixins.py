from django.db.models import Exists, OuterRef, Q
import logging

from .permissions import UserSpecificPermission
from .settings import user_permissions_settings

logger = logging.getLogger(__name__)

class UserSpecificPermissionMixin:
    permission_classes = [UserSpecificPermission]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, 'permission_classes'):
            self.permission_classes = [UserSpecificPermission]

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self, 'auto_filter_queryset', False):
            return self._filter_queryset_by_permissions(qs)
        return qs

    def _filter_queryset_by_permissions(self, queryset):
        user = self.request.user
        if user.is_superuser:
            return queryset

        model_cls = queryset.model
        model_name = model_cls._meta.model_name
        view_perm_codename = f"view_{model_name}"

        # Global view permission → all objects
        if user.has_perm(view_perm_codename):
            return queryset

        # Otherwise, restrict to objects where the user has:
        #   - a per‑object view permission, OR
        #   - is the owner (if ownership field is defined)
        from .models import UserPermission
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(model_cls)
        per_object_subquery = UserPermission.objects.filter(
            user=user,
            permission__codename=view_perm_codename,
            content_type=content_type,
            object_id=OuterRef('pk')
        )
        q_filter = Q(Exists(per_object_subquery))

        # Add ownership condition
        owner_field = user_permissions_settings.OWNERSHIP_FIELD
        if owner_field and hasattr(model_cls, owner_field):
            q_filter |= Q(**{owner_field: user})

        filtered = queryset.filter(q_filter)

        # Optional performance warning
        if not filtered.exists() and queryset.count() > 1000:
            logger.warning(
                f"User {user.id} has no view permissions for {model_name}, "
                "but a large queryset was scanned. Consider adding global view permission."
            )
        return filtered

    def initialize_request(self, request, *args, **kwargs):
        from .utils import clear_request_cache
        clear_request_cache()
        return super().initialize_request(request, *args, **kwargs)