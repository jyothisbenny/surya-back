import shutil
import re
import json

from decouple import config
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
from .services import operation_state_check, alarm_name_check, alarm_status_check
from ..base import response
from ..base.api.viewsets import ModelViewSet
from ..base.api.pagination import StandardResultsSetPagination
from ..base.utils import timezone
from ..base.utils.timezone import localtime

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
    def account_overview(self, request):
        queryset = Location.objects.filter(user__id=request.user.pk, is_active=True)
        location_count = queryset.count()
        all_devices = Device.objects.filter(location__user__id=request.user.pk, location__is_active=True,
                                            is_active=True)
        device_count = all_devices.count()
        capacity = 0
        for record in queryset.iterator():
            try:
                capacity += int(record.capacity)
            except:
                pass
        inverter_count = all_devices.count()
        etotal = 0
        for record in all_devices.iterator():
            inverter_data = InverterData.objects.filter(device=record).order_by('-created_at').first()
            if inverter_data and inverter_data.total_energy:
                etotal += int(inverter_data.total_energy)
        co2_saved = etotal * 0.8
        context = {"location_count": location_count, "device_count": device_count, "capacity": capacity,
                   "inverter_count": inverter_count, "co2_saved": co2_saved}
        return response.Ok(context)

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
    def de_vs_time(self, request):
        THRESHOLD_VALUE = int(config('THRESHOLD_VALUE'))
        from_date = request.query_params.get('from_date', str(datetime.now().strftime(("%Y-%m-%d"))))
        to_date = request.query_params.get('to_date', str(datetime.now().strftime(("%Y-%m-%d"))))
        device_id = request.query_params.get('device')
        inverter_data = InverterData.objects.filter(device=device_id,
                                                    created_at__date__lte=to_date,
                                                    created_at__date__gte=from_date,
                                                    is_active=True)
        x_axis = []
        y_axis = []
        if not inverter_data:
            return response.Ok({"x_axis": x_axis, "y_axis": y_axis})
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
        for i in results:
            x_axis.append(localtime(i.get("created_at")).replace(tzinfo=None))
            y_axis.append(round(i.get("daily_energy"), 3))
        return response.Ok({"x_axis": x_axis, "y_axis": y_axis})

    @action(methods=['GET'], detail=False, pagination_class=StandardResultsSetPagination)
    def oap_vs_time(self, request):
        THRESHOLD_VALUE = int(config('THRESHOLD_VALUE'))
        from_date = request.query_params.get('from_date', str(datetime.now().strftime(("%Y-%m-%d"))))
        to_date = request.query_params.get('to_date', str(datetime.now().strftime(("%Y-%m-%d"))))
        device_id = request.query_params.get('device')
        inverter_data = InverterData.objects.filter(device=device_id,
                                                    created_at__date__lte=to_date,
                                                    created_at__date__gte=from_date,
                                                    is_active=True)
        x_axis = []
        y_axis = []
        if not inverter_data:
            return response.Ok({"x_axis": x_axis, "y_axis": y_axis})
        count = inverter_data.count()
        inverter_data = inverter_data.order_by('created_at')
        results = []
        if count < THRESHOLD_VALUE:
            results = list(inverter_data.values('created_at', 'op_active_power'))
        else:
            ratio = round(count / THRESHOLD_VALUE)
            for i in range(0, count, ratio):
                selected_data = inverter_data[i:i + ratio]
                max_oap = selected_data.aggregate(
                    max_energy=Coalesce(Max('op_active_power', output_field=FloatField()), 0,
                                        output_field=FloatField()))
                max_oap = max_oap.get('max_energy', 0)
                instance = inverter_data.filter(id__in=selected_data.values_list('id', flat=True),
                                                op_active_power=max_oap).first()
                results.append({'created_at': instance.created_at, 'op_active_power': instance.op_active_power})

        for i in results:
            x_axis.append(localtime(i.get("created_at")).replace(tzinfo=None))
            y_axis.append(round(i.get("op_active_power"), 3))
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
                reg2 = modbus.get('reg2', '0000')
                nominal_power = (int(reg2, 16)) * 0.1
                reg4 = modbus.get('reg4', '0000')
                daily_energy = (int(reg4, 16)) * 0.1
                reg5 = modbus.get('reg5', '0000')
                reg6 = modbus.get('reg6', '0000')
                total_energy = (int(reg6 + reg5, 16)) * 1
                reg32 = modbus.get('reg32', '0000')
                reg33 = modbus.get('reg33', '0000')
                op_active_power = (int(reg33 + reg32, 16)) * 0.001
                specific_yields = 0
                if nominal_power != 0:
                    specific_yields = daily_energy / nominal_power
                inverter_op_active_power = int(reg33 + reg32, 16)
                inverter_daily_energy = int(reg4, 16)
                inverter_total_energy = int(reg6 + reg5, 16)
                reg84 = modbus.get('reg84', '0000')
                reg85 = modbus.get('reg85', '0000')
                meter_active_power = int(reg85 + reg84, 16)
                reg39 = int(modbus.get('reg39', '0000'), 16)
                alarm_status = alarm_status_check(reg39)
                alarm_ops_state = operation_state_check(reg39)
                reg46 = int(modbus.get('reg46', '0000'), 16)
                alarm_name = alarm_name_check(reg46)
                alarm_date = ""
                reg40 = modbus.get('reg40', None)
                if reg40 is not None:
                    alarm_year = int(reg40, 16)
                    alarm_date += str(alarm_year) + "/"
                reg41 = modbus.get('reg41', None)
                if reg41 is not None:
                    alarm_month = int(reg41, 16)
                    alarm_date += str(alarm_month) + "/"
                reg42 = modbus.get('reg42', None)
                if reg42 is not None:
                    alarm_day = int(reg42, 16)
                    alarm_date += str(alarm_day) + ", "
                reg43 = modbus.get('reg43', None)
                if reg43 is not None:
                    alarm_hr = int(reg43, 16)
                    alarm_date += str(alarm_hr) + ":"
                reg44 = modbus.get('reg44', None)
                if reg44 is not None:
                    alarm_min = int(reg44, 16)
                    alarm_date += str(alarm_min) + ":"
                reg45 = modbus.get('reg45', None)
                if reg45 is not None:
                    alarm_sec = int(reg45, 16)
                    alarm_date += str(alarm_sec)
                if len(alarm_date) == 0:
                    alarm_date = None
        elif device.location.inverter_type == INVERTER_TYPE_ABB:
            if modbus:
                modbus = modbus[0]
                sid = modbus.get('sid', None)
                rcnt = modbus.get('rcnt', None)
                reg2 = modbus.get('reg2', '0000')
                nominal_power = (int(reg2, 16)) * 0.1
                reg21 = modbus.get('reg21', '0000')
                reg22 = modbus.get('reg22', '0000')
                daily_energy = (int(reg22 + reg21, 16)) * 0.1
                reg23 = modbus.get('reg23', '0000')
                reg24 = modbus.get('reg24', '0000')
                total_energy = (int(reg24 + reg23, 16)) * 1
                reg45 = modbus.get('reg45', '0000')
                reg46 = modbus.get('reg46', '0000')
                op_active_power = (int(reg46 + reg45, 16)) * 1
                specific_yields = 0
                if nominal_power != 0:
                    specific_yields = daily_energy / nominal_power
                inverter_op_active_power = int(reg46 + reg45, 16)
                inverter_daily_energy = int(reg22 + reg21, 16)
                inverter_total_energy = int(reg24 + reg23, 16)
                reg84 = modbus.get('reg84', '0000')
                reg85 = modbus.get('reg85', '0000')
                meter_active_power = int(reg85 + reg84, 16)
                reg39 = int(modbus.get('reg39', '0000'), 16)
                alarm_status = alarm_status_check(reg39)
                alarm_ops_state = operation_state_check(reg39)
                alarm_name = alarm_name_check(reg46)
                alarm_year = int(modbus.get('reg40', '0000'), 16)
                alarm_month = int(modbus.get('reg41', '0000'), 16)
                alarm_date = ""
                reg40 = modbus.get('reg40', None)
                if reg40 is not None:
                    alarm_year = int(reg40, 16)
                    alarm_date += str(alarm_year) + "/"
                reg41 = modbus.get('reg41', None)
                if reg41 is not None:
                    alarm_month = int(reg41, 16)
                    alarm_date += str(alarm_month) + "/"
                reg42 = modbus.get('reg42', None)
                if reg42 is not None:
                    alarm_day = int(reg42, 16)
                    alarm_date += str(alarm_day) + ", "
                reg43 = modbus.get('reg43', None)
                if reg43 is not None:
                    alarm_hr = int(reg43, 16)
                    alarm_date += str(alarm_hr) + ":"
                reg44 = modbus.get('reg44', None)
                if reg44 is not None:
                    alarm_min = int(reg44, 16)
                    alarm_date += str(alarm_min) + ":"
                reg45 = modbus.get('reg45', None)
                if reg45 is not None:
                    alarm_sec = int(reg45, 16)
                    alarm_date += str(alarm_sec)
                if len(alarm_date) == 0:
                    alarm_date = None
        else:
            return response.BadRequest({'detail': 'Invalid Inverter type!'})
        InverterData.objects.create(device=device, imei=imei, sid=sid, uid=uid, rcnt=rcnt, daily_energy=daily_energy,
                                    total_energy=total_energy, op_active_power=op_active_power,
                                    specific_yields=specific_yields, inverter_op_active_power=inverter_op_active_power,
                                    inverter_daily_energy=inverter_daily_energy, nominal_power=nominal_power,
                                    inverter_total_energy=inverter_total_energy, meter_active_power=meter_active_power,
                                    alarm_status=alarm_status, alarm_ops_state=alarm_ops_state, alarm_name=alarm_name,
                                    alarm_date=alarm_date)
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
