import django_filters
from .models import Location, Device, InverterData


class LocationFilter(django_filters.FilterSet):
    class Meta:
        model = Location
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'latitude': ['exact', 'icontains'],
            'longitude': ['exact', 'icontains'],
        }


class DeviceFilter(django_filters.FilterSet):
    class Meta:
        model = Device
        fields = {
            'id': ['exact'],
            'device_name': ['exact', 'icontains'],
            'location': ['exact'],
        }


class InverterDataFilter(django_filters.FilterSet):
    class Meta:
        model = InverterData
        fields = {
            'id': ['exact'],
            'sid': ['exact', 'icontains'],
            'uid': ['exact', 'icontains'],
            'imei': ['exact', 'icontains'],
            'rcnt': ['exact', 'icontains'],
            'daily_energy': ['exact', 'icontains'],
            'total_energy': ['exact', 'icontains'],
            'op_active_power': ['exact', 'icontains'],
            'specific_yields': ['exact', 'icontains'],
            'inverter_op_active_power': ['exact', 'icontains'],
            'inverter_daily_energy': ['exact', 'icontains'],
            'inverter_total_energy': ['exact', 'icontains'],
            'meter_active_power': ['exact', 'icontains'],
        }
