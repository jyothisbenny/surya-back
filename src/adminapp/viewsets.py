import shutil
import re
import json

from django.http import HttpResponse
from django.conf import settings
from datetime import datetime
from rest_framework.decorators import action
from django.db.models import Max, FloatField
from django.db.models.functions import Coalesce

from .models import Location, Device, InverterData, InverterJsonData, ZipReport
from .filters import LocationFilter, DeviceFilter, InverterDataFilter, ZipReportFilter
from .serializers import LocationSerializer, DeviceSerializer, InverterDataSerializer, LocationSummarySerializer, \
    DeviceSummarySerializer, ZipReportSerializer, FileSerializer
from .permissions import LocationPermissions, DevicePermissions, InverterDataPermissions, ZipReportPermissions
from .constants import INVERTER_TYPE_SUNGROW, INVERTER_TYPE_ABB
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

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def graph_data(self, request):
        THRESHOLD_VALUE = 100
        from_date = request.query_params.get('from_date', str(datetime.now().strftime(("%Y-%m-%d"))))
        to_date = request.query_params.get('to_date', str(datetime.now().strftime(("%Y-%m-%d"))))
        device_id = request.query_params.get('device')
        inverter_data = InverterData.objects.filter(device=device_id,
                                                    created_at__date__lte=to_date,
                                                    created_at__date__gte=from_date,
                                                    is_active=True)
        count = inverter_data.count()
        inverter_data = inverter_data.order_by('created_at')
        results = []
        if count < THRESHOLD_VALUE:
            results = list(inverter_data.values('created_at', 'daily_energy'))
        else:
            ratio = round(count / THRESHOLD_VALUE)
            for i in range(0, count, ratio):
                selected_data = inverter_data[i:i + ratio]
                max_energy = selected_data.aggregate(
                    max_energy=Coalesce(Max('daily_energy', output_field=FloatField()), 0, output_field=FloatField()))
                max_energy = max_energy.get('max_energy', 0)
                instance = inverter_data.filter(id__in=selected_data.values_list('id', flat=True),
                                                daily_energy=max_energy).first()
                results.append({'created_at': instance.created_at, 'daily_energy': instance.daily_energy})
        x_axis = []
        y_axis = []
        for i in results:
            x_axis.append(i.get("created_at"))
            y_axis.append(round(i.get("daily_energy"), 3))
        return response.Ok({"x_axis": x_axis, "y_axis": y_axis})


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
        start_date = request.query_params.get('start_date', str(datetime.now().strftime(("%Y-%m-%d"))))
        end_date = request.query_params.get('end_date', str(datetime.now().strftime(("%Y-%m-%d"))))
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

    @action(methods=['POST'], detail=False)
    def inverter_data(self, request):
        data = None
        try:
            raw_data = request.body.decode('utf-8').replace(" ", "")
            raw_data = re.sub(":([\w\.]+)", r':"\1"', raw_data)
            data = json.loads(raw_data)
        except Exception as e:
            print(str(e))
        InverterJsonData.objects.create(data=data)
        data = data.pop("data", None)
        imei = data.get('imei', None)
        if imei is None:
            return response.BadRequest({'detail': 'IMEI number is required!'})
        device = Device.objects.filter(imei=imei).first()
        if not device:
            return response.BadRequest({'detail': 'This IMEI number is not used by any device!'})

        uid = data.get('uid', None)
        modbus = data.get('modbus', None)
        sid = rcnt = None
        if device.location.inverter_type == INVERTER_TYPE_SUNGROW:
            if modbus:
                modbus = modbus[0]
                sid = modbus.get('sid', None)
                rcnt = modbus.get('rcnt', None)
                reg4 = modbus.get('reg4', '0000')
                daily_energy = (int(reg4, 16)) * 0.1
                reg5 = modbus.get('reg5', '0000')
                reg6 = modbus.get('reg6', '0000')
                total_energy = (int(reg6 + reg5, 16)) * 1
                reg32 = modbus.get('reg32', '0000')
                reg33 = modbus.get('reg33', '0000')
                op_active_power = (int(reg33 + reg32, 16)) * 0.001
                specific_yields = int(reg6 + reg5, 16)
                inverter_op_active_power = int(reg33 + reg32, 16)
                inverter_daily_energy = int(reg4, 16)
                inverter_total_energy = int(reg6 + reg5, 16)
                reg84 = modbus.get('reg84', '0000')
                reg85 = modbus.get('reg85', '0000')
                meter_active_power = int(reg85 + reg84, 16)
        elif device.location.inverter_type == INVERTER_TYPE_ABB:
            if modbus:
                modbus = modbus[0]
                sid = modbus.get('sid', None)
                rcnt = modbus.get('rcnt', None)
                reg21 = modbus.get('reg21', '0000')
                reg22 = modbus.get('reg22', '0000')
                daily_energy = (int(reg22 + reg21, 16)) * 0.1
                reg23 = modbus.get('reg23', '0000')
                reg24 = modbus.get('reg24', '0000')
                total_energy = (int(reg24 + reg23, 16)) * 1
                reg45 = modbus.get('reg45', '0000')
                reg46 = modbus.get('reg46', '0000')
                op_active_power = (int(reg46 + reg45, 16)) * 1
                specific_yields = int(reg24 + reg23, 16)
                inverter_op_active_power = int(reg46 + reg45, 16)
                inverter_daily_energy = int(reg22 + reg21, 16)
                inverter_total_energy = int(reg24 + reg23, 16)
                reg84 = modbus.get('reg84', '0000')
                reg85 = modbus.get('reg85', '0000')
                meter_active_power = int(reg85 + reg84, 16)
        else:
            return response.BadRequest({'detail': 'Invalid Inverter type!'})
        InverterData.objects.create(device=device, imei=imei, sid=sid, uid=uid, rcnt=rcnt, daily_energy=daily_energy,
                                    total_energy=total_energy, op_active_power=op_active_power,
                                    specific_yields=specific_yields, inverter_op_active_power=inverter_op_active_power,
                                    inverter_daily_energy=inverter_daily_energy,
                                    inverter_total_energy=inverter_total_energy, meter_active_power=meter_active_power)
        return response.Ok({"detail": "Data stored successfully!"})

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


class ZipReportViewSet(ModelViewSet):
    """
    Here we have user login, logout, endpoints.
    """
    queryset = ZipReport.objects.filter(is_active=True)
    serializer_class = ZipReportSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (ZipReportPermissions,)
    filterset_class = None

    def get_queryset(self):
        queryset = super(ZipReportViewSet, self).get_queryset()
        queryset = queryset.filter(user=self.request.user.pk, is_active=True).order_by('-id')
        self.filterset_class = ZipReportFilter
        queryset = self.filter_queryset(queryset)
        return queryset

    def perform_create(self, serializer):
        data = self.request.data
        user = self.request.user
        serializer.save(user=user)

    @action(methods=['GET'], detail=False)
    def report_zip(self, request):
        report_id = request.query_params.get('report_id', None)
        queryset = ZipReport.objects.filter(pk=report_id).first()
        archive_name = '{}/{}/{}'.format(settings.MEDIA_ROOT, str(queryset.id) + "-zip", queryset.name)
        directory_name = '{}/{}/'.format(settings.MEDIA_ROOT, str(queryset.id))
        shutil.make_archive(archive_name, 'zip', directory_name)
        # zip_file = open(settings.MEDIA_ROOT + "/" + str(queryset.id)+"-zip" + "/" + str(queryset.name)+".zip", 'rb')
        # response = HttpResponse(zip_file, content_type='application/zip')
        # response['Content-Disposition'] = 'attachment; filename=name.zip'
        return response.Ok({"path": "/" + str(queryset.id) + "-zip" + "/" + str(queryset.name) + ".zip"})
