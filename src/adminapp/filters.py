import django_filters
from .models import Location, Device


class LocationFilter(django_filters.FilterSet):
    class Meta:
        model = Location
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            }


class DeviceFilter(django_filters.FilterSet):
    class Meta:
        model = Device
        fields = {
            'id': ['exact'],
            'device_name': ['exact', 'icontains'],
            'location': ['exact'],
            }