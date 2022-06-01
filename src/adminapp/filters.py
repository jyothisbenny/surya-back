from datetime import datetime

import django_filters
from .models import Location, Device, InverterData, ZipReport


class LocationFilter(django_filters.FilterSet):
    class Meta:
        model = Location
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'latitude': ['exact', 'icontains'],
            'longitude': ['exact', 'icontains']
        }


class DeviceFilter(django_filters.FilterSet):
    class Meta:
        model = Device
        fields = {
            'id': ['exact'],
            'imei': ['exact'],
            'device_name': ['exact', 'icontains'],
            'location': ['exact'],
        }


class InverterDataFilter(django_filters.FilterSet):
    class Meta:
        model = InverterData
        fields = {
            'id': ['exact'],
            'device': ['exact'],
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


class ZipReportFilter(django_filters.FilterSet):
    class Meta:
        model = ZipReport
        fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains'],
            'from_date': ['exact'],
            'to_date': ['exact'],
            'frequency': ['exact', 'icontains'],
            'category': ['exact', 'icontains'],
            'status': ['exact', 'icontains'],
            'location': ['exact',  'icontains'],
        }
