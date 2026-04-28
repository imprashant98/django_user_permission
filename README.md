# django-user-permissions

User-specific permissions with per-object support for Django + Django REST Framework.

A lightweight, API-friendly object permission system that extends Django’s default permission model with:

- **Object-level permissions** – grant a permission for a specific instance
- **Ownership-based access** – automatically grant `view`, `change`, `delete` to owners
- **DRF integration** – plug-and-play support for ViewSets/APIs
- **Public/safe endpoints** – make certain actions public
- **Permission caching** – request-local + shared cache with automatic invalidation
- **Permission syncing** – create missing default permissions automatically

Think of it as a simpler alternative to django-guardian for teams building API-first applications with Django REST Framework.

---

## Why not just use django-guardian?

While `django-guardian` is powerful and battle-tested, it often requires additional setup for DRF-heavy projects.

This package focuses on:

- automatic DRF action mapping
- ownership rules
- safe/public endpoints
- reduced permission boilerplate

---

## Requirements

- Python 3.8+
- Django 3.2+
- Django REST Framework 3.14+

---

# Installation

```bash
pip install django-user-permissions
```

---

# Setup

## Add to installed apps

```python
INSTALLED_APPS = [
    ...
    "django_user_permissions",
]
```

---

## Add authentication backend

Place this before Django’s default backend:

```python
AUTHENTICATION_BACKENDS = [
    "django_user_permissions.backends.UserSpecificPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",
]
```

---

## Run migrations

```bash
python manage.py migrate
```

---

## Sync permissions

Create missing permissions:

```bash
python manage.py sync_user_permissions
```

Dry run:

```bash
python manage.py sync_user_permissions --dry-run
```

---

# Configuration

Add this in `settings.py`:

```python
USER_PERMISSIONS = {
    "OWNERSHIP_FIELD": "user",
    "OWNER_AUTO_PERMISSIONS": ["view", "change", "delete"],
    "ALLOW_CREATE_ON_OWNERSHIP": True,

    # Actions that can be resolved at object level
    "ALLOW_OBJECT_LEVEL_ACTIONS": [
        "retrieve",
        "update",
        "partial_update",
        "destroy"
    ],

    # Allow list endpoints even if final queryset is empty
    "LIST_ALLOW_EMPTY": True,

    "MODEL_SAFE_METHODS": {
        "document": ["list", "retrieve"]
    },

    "CACHE_TTL": 300
}
```

---

# DRF Integration

## Example model

```python
class Document(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
```

---

## Example ViewSet

```python
from django_user_permissions.mixins import UserSpecificPermissionMixin

class DocumentViewSet(UserSpecificPermissionMixin, ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    auto_filter_queryset = True
```

> `auto_filter_queryset=True` filters the queryset to objects the user can view (global or per-object permissions) **plus** objects they own—even without explicit permissions.

---

# DRF Action Mapping

| DRF Action | Permission Required | Example |
|------------|----------------------|---------|
| list | `view_<model_name>` | `view_document` |
| retrieve | `view_<model_name>` | `view_document` |
| create | `add_<model_name>` | `add_document` |
| update | `change_<model_name>` | `change_document` |
| partial_update | `change_<model_name>` | `change_document` |
| destroy | `delete_<model_name>` | `delete_document` |

Example:

```bash
PATCH /documents/1/
```

Requires:

```python
change_document
```

---

# How Permission Checks Work

Permission evaluation order:

1. Superuser access
2. Safe/public method access
3. Global Django permissions
4. Ownership create validation
5. Object-specific permissions
6. Ownership auto-permissions

---

# Grant Object-Level Permission

```python
from django_user_permissions.models import UserPermission
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

doc = Document.objects.get(pk=1)
perm = Permission.objects.get(codename="change_document")

UserPermission.objects.create(
    user=user,
    permission=perm,
    content_type=ContentType.objects.get_for_model(doc),
    object_id=doc.id
)
```

Now that user can modify only that specific document.

---

# Caching

This package uses:

- request-level caching
- shared caching
- automatic signal-based invalidation

Whenever permissions are updated/deleted, stale cache gets cleared automatically.

---

# Management Commands

```bash
python manage.py sync_user_permissions
```

Supports:

- `--dry-run`
- `--apps`
- `--exclude`

---

# Testing

```bash
pip install -e .[dev]
pytest tests/
```

---

# Use Cases

- SaaS platforms
- Document sharing apps
- Project management systems
- Multi-tenant products
- Internal admin tools

---

# Roadmap

- Group object permissions
- Queryset filtering helpers
- Admin dashboard improvements
- Async cache invalidation

---

# License

MIT License

---

Built because writing repetitive permission logic in every DRF project gets exhausting.
