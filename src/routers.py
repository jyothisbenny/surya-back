from rest_framework import routers
from django.urls import path, include

from .accounts.viewsets import UserViewSet
from .adminapp.viewsets import LocationViewSet, DeviceViewSet

router = routers.DefaultRouter()

# user
router.register(r'users', UserViewSet, basename='v1_auth')
router.register(r'location', LocationViewSet, basename='v1_location')
router.register(r'device', DeviceViewSet, basename='v1_device')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    ]