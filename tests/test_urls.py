from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tests.testapp.views import PostViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]