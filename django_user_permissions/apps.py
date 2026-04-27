from django.apps import AppConfig

class DjangoUserPermissionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_user_permissions'
    verbose_name = "Django User Permissions"

    def ready(self):
        # Import signals only when the app is ready
        from . import signals