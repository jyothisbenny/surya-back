import pandas as pd
import datetime

from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font

from django.conf import settings
from rest_framework import serializers

from .models import Location, Device, InverterData, InverterJsonData, ZipReport
from ..accounts.serializers import UserSerializer
from ..base.serializers import ModelSerializer
from ..base.utils import timezone
from ..base.validators.form_validations import file_extension_validator

now = timezone.now_local()


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
        for record in device_data:
            if record.created_at + datetime.timedelta(minutes=5) < now:
                status = "Online"
        pr, cuf, insolation = 0, 0, 0
        irradiation = 250
        insolation = irradiation * 24
        if inverter_data and inverter_data.specific_yields:
            pr = (int(inverter_data.specific_yields) * 100) / 24
            cuf = pr / 365 * 24 * 12
        if inverter_data:
            context = {"total_energy": inverter_data.total_energy,
                       "daily_energy": inverter_data.daily_energy,
                       "op_active_power": inverter_data.op_active_power,
                       "specific_yields": inverter_data.specific_yields,
                       "pr": pr, "cuf": cuf, "irradiation": irradiation,
                       "insolation": insolation, "status": status
                       }
            return context
        else:
            return {"pr": pr, "cuf": cuf, "irradiation": irradiation, "insolation": insolation, "status": status}


class DeviceSummarySerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Device
        fields = '__all__'

    def get_summary(self, obj):
        imei_last_record = None
        status = None
        if obj.imei:
            imei_last_record = InverterData.objects.filter(imei=obj.imei).last()
        if imei_last_record:
            if imei_last_record.created_at + datetime.timedelta(minutes=5) > now:
                status = "Online"
        else:
            status = "Offline"
        start_date = self.context.get('start_date')
        end_date = self.context.get('end_date')

        if start_date == end_date:
            inverter_data = InverterData.objects.filter(device=obj, created_at__date=start_date,
                                                        is_active=True).order_by('-id').first()
            if inverter_data:
                context = {"total_energy": inverter_data.total_energy,
                           "daily_energy": inverter_data.daily_energy,
                           "uid": inverter_data.op_active_power,
                           "status": status}
                return context

        inverter_start_data = InverterData.objects.filter(device=obj, created_at__date=self.context.get('start_date'),
                                                          is_active=True).order_by('-id').first()
        inverter_end_data = InverterData.objects.filter(device=obj, created_at__date=end_date,
                                                        is_active=True).order_by('-id').first()

        if inverter_start_data and inverter_end_data:
            context = {"total_energy": int(inverter_end_data.total_energy) - int(inverter_start_data.total_energy),
                       "daily_energy": int(inverter_end_data.daily_energy) - int(inverter_start_data.daily_energy),
                       "uid": int(inverter_end_data.op_active_power) - int(inverter_start_data.op_active_power),
                       "status": status
                       }
            return context
        else:
            context = {"status": status}
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
        # from_date = validated_data.pop("from_date", None)
        # to_date = validated_data.pop("to_date", None)
        # from_date = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
        # to_date = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()
        report_instance = ZipReport.objects.create(user=validated_data.pop('user', None), **validated_data)
        for location in location_list:
            try:
                report_instance.location.add(location)
                from_date = validated_data.get('from_date')
                to_date = validated_data.get('to_date')

                context = None
                if from_date == to_date:
                    # from_date = datetime.datetime.strptime(from_date, "%Y-%m-%d")
                    from_date = from_date - datetime.timedelta(days=1)

                start_data = InverterData.objects.filter(device__location=location,
                                                         created_at__date=from_date,
                                                         is_active=True).order_by('-id').first()
                end_data = InverterData.objects.filter(device__location=location,
                                                       created_at__date=to_date,
                                                       is_active=True).order_by('-id').first()

                context = {
                    "total_energy": int(end_data.total_energy) - int(start_data.total_energy),
                    "daily_energy": int(end_data.daily_energy) - int(start_data.daily_energy),
                    "op_active_power": int(end_data.op_active_power) - int(start_data.op_active_power),
                    "specific_yields": int(end_data.specific_yields) - int(start_data.specific_yields),
                    "status": "status"}

                pr, cuf, insolation = 0, 0, 0
                irradiation = 250
                insolation = irradiation * 24
                if context and context['specific_yields']:
                    pr = (int(inverter_data.specific_yields) * 100) / 24
                    cuf = pr / 365 * 24 * 12

                wb = Workbook()
                sheet = wb['Sheet']
                wb.remove(sheet)
                ws1 = wb.create_sheet("Plant Summery")
                ws2 = wb.create_sheet("Plant Analysis")
                # ws3 = wb.create_sheet("Grid Downtime Analysis")
                # ws4 = wb.create_sheet("Inverter Summery ")
                # ws5 = wb.create_sheet("Alarm Analysis")
                # ws6 = wb.create_sheet("Help & Support")

                plant_summery_data = [
                    ['Plant Name', location.name],
                    ['Date', validated_data.get('from_date').replace(tzinfo=None),
                     validated_data.get('to_date').replace(tzinfo=None)],
                    ['Description'],
                    ['Plant Capacity', "", "kWp"],
                    ['Plant Manager'],
                    ['Manager Phone'],
                    [''],
                    ['Daily Energy', context['daily_energy'], "kWh"],
                    ['Output Active Power', context['op_active_power'], "kWp"],
                    ['Specific Yield', context['specific_yields'], "kWh/kWp"],
                    ['CUF', cuf, "%"],
                    ['Performance Ratio', pr, "%"],
                    ['Total Energy', context['total_energy'], "MWh"],
                    ['Solar Insolation', insolation, "KWh/m2"],
                    ['Solar Irradiation', irradiation, "W/m2"],
                ]
                plant_analysis_data = []

                inverter_data = InverterData.objects.filter(device__location=location,
                                                            created_at__date__lte=to_date,
                                                            created_at__date__gte=from_date,
                                                            is_active=True)
                for inverter in inverter_data.iterator():
                    inverter_pr = (int(inverter.specific_yields) * 100) / 24
                    inverter_cuf = int(inverter_pr) / 365 * 24 * 12
                    plant_analysis_data.append(
                        [inverter.created_at.replace(tzinfo=None), inverter.daily_energy, inverter.op_active_power,
                         inverter.specific_yields,
                         inverter_cuf, inverter_pr, inverter.total_energy, insolation, irradiation])

                for row in plant_summery_data:
                    ws1.append(row)
                ws2.append(["Timestamp", "Daily Energy [ kWh ]", "Output Active Power [ kWp ]",
                            "Specific Yield [ kWh/kWp ]", "CUF [ % ]", "Performance Ratio [ % ]",
                            "Total Energy [ MWh ]", "Solar Insolation [ KWh/m2 ]", "Solar Irradiation [ W/m2 ]"])
                red_font = Font(bold=True, italic=True)
                for cell in ws2["1:1"]:
                    cell.font = red_font
                for row in plant_analysis_data:
                    ws2.append(row)
                Path(settings.MEDIA_ROOT + "/" + str(report_instance.id)).mkdir(parents=True, exist_ok=True)
                wb.save('{}/{}/{}.xlsx'.format(settings.MEDIA_ROOT, str(report_instance.id), location.name))
                report_instance.status = "Success"
            except Exception as e:
                print(e)
                report_instance.status = "Error"
        report_instance.save()
        return report_instance


class FileSerializer(serializers.Serializer):
    file = serializers.FileField(validators=[file_extension_validator])
