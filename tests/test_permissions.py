import pytest
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from tests.testapp.models import Post
from django_user_permissions.models import UserPermission

@pytest.fixture
def user1(db):
    return User.objects.create_user(username='user1', password='pass')

@pytest.fixture
def other_user(db):
    return User.objects.create_user(username='other', password='pass')

@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username='admin', password='pass')

@pytest.fixture
def post1(user1):
    return Post.objects.create(title='Post 1', content='Content 1', user=user1)

@pytest.fixture
def post2(other_user):
    return Post.objects.create(title='Post 2', content='Content 2', user=other_user)

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

def test_global_permission(api_client, user1, post2):
    api_client.force_authenticate(user=user1)
    # Without global permission, user cannot see another user's post
    response = api_client.get(f'/api/posts/{post2.id}/')
    assert response.status_code == 404

    # Give global view permission
    perm = Permission.objects.get(codename='view_post')
    user1.user_permissions.add(perm)
    # Clear the permission cache on the user instance
    user1._perm_cache = None
    # Re‑authenticate with the updated user
    api_client.force_authenticate(user=user1)
    response = api_client.get(f'/api/posts/{post2.id}/')
    assert response.status_code == 200
    assert response.data['id'] == post2.id

def test_per_object_permission(api_client, user1, other_user, post2):
    # user1 has no permission to see post2 (owned by other_user)
    api_client.force_authenticate(user=user1)
    response = api_client.get(f'/api/posts/{post2.id}/')
    assert response.status_code == 404

    # Give per-object view permission for post2 to user1
    ct = ContentType.objects.get_for_model(Post)
    perm = Permission.objects.get(codename='view_post')
    UserPermission.objects.create(user=user1, permission=perm, content_type=ct, object_id=post2.id)

    response = api_client.get(f'/api/posts/{post2.id}/')
    assert response.status_code == 200
    assert response.data['title'] == 'Post 2'

def test_ownership_auto_permission(api_client, user1, post1):
    api_client.force_authenticate(user=user1)
    # Owner should be able to change (default OWNER_AUTO_PERMISSIONS includes 'change')
    response = api_client.patch(f'/api/posts/{post1.id}/', {'title': 'Updated'})
    assert response.status_code == 200
    assert response.data['title'] == 'Updated'