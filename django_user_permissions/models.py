from django.db import models
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class UserPermission(models.Model):
    """
    Grants a specific permission to a user for a specific object (or globally for a model).
    
    If object_id is None, the permission applies to all objects of the content type.
    This allows model‑wide user permissions beyond what Django's User.user_permissions
    provides (which are global across all models).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='object_permissions',
        help_text="User who receives this permission."
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        help_text="Django permission (e.g., 'view_document', 'change_document')."
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="Content type of the target object."
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Primary key of the target object. If null, permission applies to all objects of this content type."
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = [['user', 'permission', 'content_type', 'object_id']]
        verbose_name = "User Permission"
        verbose_name_plural = "User Permissions"

    def __str__(self):
        obj_info = f" (object {self.object_id})" if self.object_id else " (global)"
        return f"{self.user} | {self.permission.codename} | {self.content_type}{obj_info}"