from django.core.management.base import BaseCommand
from django.contrib.auth.management import create_permissions
from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Create missing view/add/change/delete permissions for all registered models.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apps',
            nargs='+',
            type=str,
            help='Specific app labels to sync (e.g., "myapp" "otherapp"). If not provided, syncs all apps.',
        )
        parser.add_argument(
            '--exclude',
            nargs='+',
            type=str,
            help='App labels to exclude from syncing.',
            default=[],
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List missing permissions without creating them.',
        )

    def handle(self, *args, **options):
        verbosity = options.get('verbosity', 1)
        dry_run = options.get('dry_run', False)
        include_apps = options.get('apps')
        exclude_apps = options.get('exclude', [])

        apps_to_sync = []
        for app_config in apps.get_app_configs():
            app_label = app_config.label
            if include_apps and app_label not in include_apps:
                continue
            if app_label in exclude_apps:
                continue
            # Skip Django's built-in apps unless explicitly included
            if not include_apps and app_label.startswith('django.'):
                continue
            apps_to_sync.append(app_config)

        created_count = 0
        for app_config in apps_to_sync:
            if verbosity >= 2:
                self.stdout.write(f"Scanning app '{app_config.label}'...")
            
            # Use Django's built-in create_permissions to ensure all model permissions exist
            # This respects the `default_permissions` model Meta option.
            if not dry_run:
                # `create_permissions` returns the number of permissions created
                created = create_permissions(app_config, verbosity=verbosity)
                created_count += created
            else:
                # Dry run: simulate what would be created
                missing = self._get_missing_permissions(app_config)
                if missing:
                    self.stdout.write(f"App '{app_config.label}' missing permissions:")
                    for perm in missing:
                        self.stdout.write(f"  - {perm.codename} ({perm.name})")
                    created_count += len(missing)
                elif verbosity >= 2:
                    self.stdout.write(f"App '{app_config.label}' has all permissions.")

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run completed. Would create {created_count} permission(s)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Synced permissions. Created {created_count} new permission(s)."))

    def _get_missing_permissions(self, app_config):
        """Return a list of Permission objects that should exist but don't for models in this app."""
        from django.db.models import Q
        existing_perms = Permission.objects.filter(content_type__app_label=app_config.label)
        missing = []
        for model in app_config.get_models():
            opts = model._meta
            # Default permissions as per Django
            default_perms = getattr(opts, 'default_permissions', ('add', 'change', 'delete', 'view'))
            for perm in default_perms:
                codename = f"{perm}_{opts.model_name}"
                name = f"Can {perm} {opts.verbose_name_raw}"
                # Check if permission already exists for this content type
                if not existing_perms.filter(codename=codename, content_type__model=opts.model_name).exists():
                    # Create a dummy Permission object (not saved) for reporting
                    content_type = ContentType.objects.get_for_model(model)
                    missing.append(Permission(codename=codename, name=name, content_type=content_type))
        return missing