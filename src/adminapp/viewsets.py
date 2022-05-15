from rest_framework import viewsets
from rest_framework.decorators import action

from .models import Location, Device
from .filters import LocationFilter, DeviceFilter
from .serializers import LocationSerializer, DeviceSerializer
from .permissions import LocationPermissions, DevicePermissions
from ..base import response
from ..base.api.viewsets import ModelViewSet
from ..base.api.pagination import StandardResultsSetPagination


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
        queryset = Location.objects.filter(user__id=request.user.pk, is_active=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(LocationSerializer(page, many=True).data)
        return response.Ok(LocationSerializer(queryset, many=True).data)


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

    @action(methods=['POST'], detail=False, pagination_class=StandardResultsSetPagination)
    def location_devices(self, request):
        print("-------", request.data)
        queryset = Device.objects.filter(location=request.data['location'], is_active=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(DeviceSerializer(page, many=True).data)
        return response.Ok(DeviceSerializer(queryset, many=True).data)
