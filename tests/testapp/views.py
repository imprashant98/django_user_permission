from rest_framework import viewsets
from django_user_permissions.mixins import UserSpecificPermissionMixin
from .models import Post
from .serializers import PostSerializer

class PostViewSet(UserSpecificPermissionMixin, viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    auto_filter_queryset = True