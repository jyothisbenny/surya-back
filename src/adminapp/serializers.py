import pandas as pd
import datetime
import pytz

from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font

from django.conf import settings
from rest_framework import serializers

from .models import Location, Device, InverterData, InverterJsonData, ZipReport
from .tasks import generate_zip

from ..accounts.serializers import UserSerializer
from ..base.serializers import ModelSerializer
from ..base.utils import timezone
from ..base.validators.form_validations import file_extension_validator
from ..base.utils.timezone import localtime, now_local

now = timezone.now_local()
utc = pytz.UTC


class LocationSerializer(ModelSerializer):
    user_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Location
        fields = '__all__'

    def validate(self, data):
        return data

    @staticmethod
    def get_user_data(obj):
        user_data = []
        queryset = obj.user.all() if obj.user else None
        for user in queryset:
            user_data.append(UserSerializer(user).data)
        return user_data


class DeviceSerializer(ModelSerializer):
    location_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Device
        fields = '__all__'

    def validate(self, attrs):
        is_active = attrs.get("is_active", True)
        if is_active == True:
            imei = attrs.get('imei')
            if imei:
                device = Device.objects.filter(imei=imei, is_active=True).first()
                if device:
                    raise serializers.ValidationError({"detail": "This IMEI is used by another device!"})
            else:
                raise serializers.ValidationError({"detail": "Please provide device IMEI number!"})
        return attrs

    @staticmethod
    def get_location_data(obj):
        return LocationSerializer(obj.location).data if obj.location else None


class InverterDataSerializer(ModelSerializer):
    device_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = InverterData
        fields = '__all__'

    @staticmethod
    def get_device_data(obj):
        return DeviceSerializer(obj.device).data if obj.device else None


class ETodayInverterDataSerializer(ModelSerializer):
    irradiation = serializers.SerializerMethodField(required=False)

    class Meta:
        model = InverterData
        fields = ('id', 'daily_energy', 'op_active_power', 'irradiation', 'created_at',)

    def get_irradiation(self, obj):
        irradiation = 250
        return irradiation


class LocationSummarySerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Location
        fields = '__all__'

    def get_summary(self, obj):
        inverter_data = None
        try:
            inverter_data = InverterData.objects.filter(device__location=obj, created_at__date=self.context.get('date'),
                                                        is_active=True).order_by('-id').first()
        except:
            pass
        status = "Offline"
        if obj:
            device_data = InverterData.objects.filter(device__location=obj)
            if device_data:
                device_data = device_data.order_by('created_at').last()
                if localtime(device_data.created_at) + datetime.timedelta(minutes=5) > now_local():
                    status = "Online"
        pr = cuf = insolation = None
        oap = float(inverter_data.op_active_power)
        normal_power = float(inverter_data.normal_power)
        if oap == 0 or None:
            oap = 1
        if normal_power == 0 or None:
            normal_power = 1

        irradiation = (oap * 1361) / normal_power
        insolation = irradiation * 24
        if inverter_data:
            pr = (oap * 1000 * 100) / (normal_power * irradiation)
            cuf = (float(inverter_data.daily_energy) * 100) / (normal_power * irradiation)
            context = {"total_energy": inverter_data.total_energy,
                       "daily_energy": inverter_data.daily_energy,
                       "op_active_power": inverter_data.op_active_power,
                       "specific_yields": inverter_data.specific_yields,
                       "pr": pr, "cuf": cuf, "irradiation": irradiation,
                       "insolation": insolation, "status": status
                       }
            return context
        else:
            context = {"total_energy": None,
                       "daily_energy": None,
                       "op_active_power": None,
                       "specific_yields": None,
                       "pr": pr, "cuf": cuf, "irradiation": irradiation,
                       "insolation": insolation, "status": status
                       }
            return context


class DeviceSummarySerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Device
        fields = '__all__'

    def get_summary(self, obj):
        instance = None
        status = "Offline"
        if obj.imei:
            instance = InverterData.objects.filter(imei=obj.imei)
        if instance:
            imei_last_record = instance.order_by('created_at').last()
            if localtime(imei_last_record.created_at) + datetime.timedelta(minutes=5) > now_local():
                status = "Online"
        start_date = self.context.get('start_date')
        end_date = self.context.get('end_date')

        if start_date == end_date:
            inverter_data = InverterData.objects.filter(device=obj, created_at__date=start_date,
                                                        is_active=True).last()
            if inverter_data:
                context = {"total_energy": inverter_data.total_energy,
                           "daily_energy": inverter_data.daily_energy,
                           "uid": inverter_data.uid if inverter_data.uid else 0,
                           "status": status}
                return context

        inverter_start_data = InverterData.objects.filter(device=obj, created_at__date=self.context.get('start_date'),
                                                          is_active=True).order_by('-id').first()
        inverter_end_data = InverterData.objects.filter(device=obj, created_at__date=end_date,
                                                        is_active=True).order_by('-id').first()

        if inverter_start_data and inverter_end_data:
            context = {"total_energy": int(inverter_end_data.total_energy) - int(inverter_start_data.total_energy),
                       "daily_energy": int(inverter_end_data.daily_energy) - int(inverter_start_data.daily_energy),
                       "uid": inverter_end_data.uid if inverter_start_data.uid else 0,
                       "status": status
                       }
            return context
        else:
            context = {"total_energy": None,
                       "daily_energy": None,
                       "uid": None,
                       "status": status}
            return context


class ZipReportSerializer(serializers.ModelSerializer):
    # summary = serializers.SerializerMethodField(required=False)
    # date = serializers.SerializerMethodField('date')
    class Meta:
        model = ZipReport

        fields = (
            'id', 'name', "from_date", "to_date", "frequency", "category", "status", "location", "zip_file",
            "is_active")

    def create(self, validated_data):
        location_list = validated_data.pop("location", None)
        user = validated_data.pop("user", None)
        from_date = validated_data.pop("from_date", None)
        to_date = validated_data.pop("to_date", None)
        frequency = validated_data.pop("frequency", None)
        category = validated_data.pop("category", None)
        name = validated_data.pop("name", None)
        locations = []
        for record in location_list:
            locations.append(record.id)
        report_instance = ZipReport.objects.create(user=user, from_date=from_date,
                                                   to_date=to_date,
                                                   category=category, frequency=frequency, name=name)
        from_date = from_date.strftime("%Y-%m-%d")
        to_date = to_date.strftime("%Y-%m-%d")
        generate_zip.s(locations, report_instance.id, from_date, to_date).apply_async(countdown=5, serializer='json')
        return report_instance


class FileSerializer(serializers.Serializer):
    file = serializers.FileField(validators=[file_extension_validator])
