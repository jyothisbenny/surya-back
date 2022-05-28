from rest_framework import viewsets
from datetime import datetime
from rest_framework.decorators import action
from django.db.models import Avg, IntegerField, FloatField
from django.db.models.functions import Cast

from .models import Location, Device, InverterData, InverterJsonData
from .filters import LocationFilter, DeviceFilter, InverterDataFilter
from .serializers import LocationSerializer, DeviceSerializer, InverterDataSerializer, LocationSummarySerializer, \
    DeviceSummarySerializer
from .permissions import LocationPermissions, DevicePermissions, InverterDataPermissions
from ..base import response
from ..base.api.viewsets import ModelViewSet
from ..base.api.pagination import StandardResultsSetPagination
from ..base.utils import timezone

now = timezone.now_local()


class LocationViewSet(ModelViewSet):
    """
    Here we have user login, logout, endpoints.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (LocationPermissions,)
    filterset_class = None

    def get_queryset(self):
        queryset = super(LocationViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        self.filterset_class = LocationFilter
        queryset = self.filter_queryset(queryset)
        return queryset

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def location_list(self, request):
        queryset = Location.objects.filter(is_active=True)
        queryset = queryset.order_by('name')
        self.filterset_class = LocationFilter
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(LocationSerializer(page, many=True).data)
        return response.Ok(LocationSerializer(queryset, many=True).data)

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def get_location_count(self, request):
        queryset = Location.objects.filter(is_active=True).count()
        print("count", queryset)
        return response.Ok(queryset)

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def user_locations(self, request):
        date = request.query_params.get('date', str(datetime.now().strftime(("%Y-%m-%d"))))
        queryset = Location.objects.filter(user__id=request.user.pk, is_active=True)

        # print(InverterDataSerializer(inverter_data, many=True).data)

        self.filterset_class = LocationFilter
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(LocationSummarySerializer(page, many=True, context={"date": date}).data)
        return response.Ok(LocationSummarySerializer(queryset, many=True, context={"date": date}).data)


class DeviceViewSet(ModelViewSet):
    """
    Here we have user login, logout, endpoints.
    """
    queryset = Device.objects.filter(is_active=True)
    serializer_class = DeviceSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (DevicePermissions,)
    filterset_class = None

    def get_queryset(self):
        queryset = super(DeviceViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        self.filterset_class = DeviceFilter
        queryset = self.filter_queryset(queryset)
        return queryset

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def location_devices(self, request):
        print("-----------------", request.query_params.get('start_date'))
        start_date = request.query_params.get('start_date', str(datetime.now().strftime(("%Y-%m-%d"))))
        end_date = request.query_params.get('end_date', str(datetime.now().strftime(("%Y-%m-%d"))))
        print(str(datetime.now().strftime(("%Y-%m-%d"))),  str(datetime.now().strftime(("%Y-%m-%d"))))
        queryset = Device.objects.filter(location=request.query_params.get('location', 0), is_active=True)
        self.filterset_class = DeviceFilter
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(
                DeviceSummarySerializer(page, many=True, context={"start_date": start_date, "end_date": end_date}).data)
        return response.Ok(DeviceSerializer(DeviceSummarySerializer, many=True,
                                            context={"start_date": start_date, "end_date": end_date}).data)


class InverterDataViewSet(ModelViewSet):
    """
    Here we have user login, logout, endpoints.
    """
    queryset = InverterData.objects.all()
    serializer_class = InverterDataSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (InverterDataPermissions,)
    filterset_class = None

    def get_queryset(self):
        queryset = super(InverterDataViewSet, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        self.filterset_class = InverterDataFilter
        queryset = self.filter_queryset(queryset)
        return queryset

    def perform_create(self, serializer):
        data = self.request.data
        serializer.save(data=data)

    @action(methods=['POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def location_devices(self, request):
        date = request.query_params.get('date', str(datetime.now().strftime(("%Y-%m-%d"))))

        queryset = InverterData.objects.filter(
            device__in=Device.objects.filter(location=request.data['location'], is_active=True),
            is_active=True).order_by('id')
        self.filterset_class = InverterDataFilter
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(InverterDataSerializer(page, many=True, context={"date": date}).data)
        return response.Ok(InverterDataSerializer(queryset, many=True, context={"date": date}).data)
