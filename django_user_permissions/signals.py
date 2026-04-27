from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group, User
from .models import UserPermission
from .utils import invalidate_object_permissions_cache

@receiver([post_save, post_delete], sender=UserPermission)
def clear_user_permission_cache(sender, instance, **kwargs):
    if instance.object_id and instance.content_object:
        invalidate_object_permissions_cache(instance.user, instance.content_object)

# Optionally, you can keep group membership signals but execute them asynchronously.
# To avoid performance pitfalls, we comment them out by default, relying on TTL.
# If you need immediate invalidation, uncomment and use Celery.

# @receiver(m2m_changed, sender=User.groups.through)
# def clear_on_group_change(sender, instance, action, **kwargs):
#     if action.startswith('post_'):
#         from .utils import invalidate_user_all_object_permissions
#         invalidate_user_all_object_permissions(instance)