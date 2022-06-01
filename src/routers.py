from rest_framework import routers
from django.urls import path, include

from .accounts.viewsets import UserViewSet
from .adminapp.viewsets import LocationViewSet, DeviceViewSet, InverterDataViewSet, ZipReportViewSet

router = routers.DefaultRouter()

# user
router.register(r'users', UserViewSet, basename='v1_auth')
router.register(r'location', LocationViewSet, basename='v1_location')
router.register(r'device', DeviceViewSet, basename='v1_device')
router.register(r'inverter', InverterDataViewSet, basename='v1_inverter')
router.register(r'report', ZipReportViewSet, basename='v1_report')


urlpatterns = [
    path('api/v1/', include(router.urls)),
    ]