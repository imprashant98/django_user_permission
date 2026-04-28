import pytest
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from tests.testapp.models import Post
from django_user_permissions.models import UserPermission

@pytest.fixture
def user1(db):
    return User.objects.create_user(username='user1', password='pass')

@pytest.fixture
def user2(db):
    return User.objects.create_user(username='user2', password='pass')

@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username='admin', password='pass')

@pytest.fixture
def post1(user1):
    return Post.objects.create(title='Post 1', content='Content 1', user=user1)

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

def test_superuser_full_access(api_client, superuser, post1):
    api_client.force_authenticate(user=superuser)
    response = api_client.get('/api/posts/')
    assert response.status_code == 200
    response = api_client.delete(f'/api/posts/{post1.id}/')
    assert response.status_code == 204

def test_global_permission(api_client, user1, post1):
    api_client.force_authenticate(user=user1)
    response = api_client.get('/api/posts/')
    # Initially no view permission -> empty list due to auto_filter_queryset
    assert response.status_code == 200
    assert len(response.data) == 0

    # Give global view permission
    perm = Permission.objects.get(codename='view_post')
    user1.user_permissions.add(perm)
    response = api_client.get('/api/posts/')
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == post1.id

def test_per_object_permission(api_client, user2, post1):
    api_client.force_authenticate(user=user2)
    # No permission -> 404 because the queryset is filtered
    response = api_client.get(f'/api/posts/{post1.id}/')
    assert response.status_code == 404

    # Give per-object view permission
    ct = ContentType.objects.get_for_model(Post)
    perm = Permission.objects.get(codename='view_post')
    UserPermission.objects.create(user=user2, permission=perm, content_type=ct, object_id=post1.id)

    response = api_client.get(f'/api/posts/{post1.id}/')
    assert response.status_code == 200
    assert response.data['title'] == 'Post 1'

def test_ownership_auto_permission(api_client, user1, post1):
    api_client.force_authenticate(user=user1)
    # Owner should be able to change (default OWNER_AUTO_PERMISSIONS includes 'change')
    response = api_client.patch(f'/api/posts/{post1.id}/', {'title': 'Updated'})
    assert response.status_code == 200
    assert response.data['title'] == 'Updated'