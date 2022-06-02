import pandas as pd
import datetime

from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font

from django.conf import settings
from django.db.models import Avg, Min, FloatField
from django.db.models.functions import Cast
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

    """default value=0000"""

    def create(self, validated_data):
        data = validated_data.pop("data", None)
        InverterJsonData.objects.create(data=data)
        imei = dict(data['data']).get('imei', None)
        if imei is None:
            raise serializers.ValidationError({"detail": "IMEI number is required!"})
        try:
            uid = data['data']['uid']
            sid = data['data']['modbus'][0]['sid']
            rcnt = data['data']['modbus'][0]['rcnt']
            reg4 = dict(data['data']['modbus'][0]).get('reg4', '0000')
            daily_energy = int(reg4, 16)
            reg5 = dict(data['data']['modbus'][0]).get('reg5', '0000')
            reg6 = dict(data['data']['modbus'][0]).get('reg6', '0000')
            total_energy = int(reg5 + reg6, 16)
            reg78 = dict(data['data']['modbus'][0]).get('reg78', '0000')
            reg79 = dict(data['data']['modbus'][0]).get('reg79', '0000')
            op_active_power = int(reg78 + reg79, 16)
            specific_yields = int(reg5 + reg6, 16)
            inverter_op_active_power = int(reg78 + reg79, 16)
            inverter_daily_energy = int(reg4, 16)
            inverter_total_energy = int(reg5 + reg6, 16)
            reg84 = dict(data['data']['modbus'][0]).get('reg84', '0000')
            reg85 = dict(data['data']['modbus'][0]).get('reg85', '0000')
            meter_active_power = int(reg84 + reg85, 16)
        except:
            raise serializers.ValidationError({"detail": "Key error! check data format."})

        device = Device.objects.filter(imei=imei).first()
        if not device:
            raise serializers.ValidationError({"detail": "This IMEI number is not used by any device!"})

        InverterData.objects.create(device=device, imei=imei, sid=sid, uid=uid, rcnt=rcnt,
                                    daily_energy=daily_energy,
                                    total_energy=total_energy, op_active_power=op_active_power,
                                    specific_yields=specific_yields,
                                    inverter_op_active_power=inverter_op_active_power,
                                    inverter_daily_energy=inverter_daily_energy,
                                    inverter_total_energy=inverter_total_energy,
                                    meter_active_power=meter_active_power)
        raise serializers.ValidationError({"detail": "Data stored successfully!"})

    @staticmethod
    def get_device_data(obj):
        return DeviceSerializer(obj.device).data if obj.device else None


class LocationSummarySerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Location
        fields = '__all__'

    def get_summary(self, obj):
        inverter_data = InverterData.objects.filter(device__location=obj, created_at__date=self.context.get('date'))
        avg_data = inverter_data.aggregate(avg_de=Avg(Cast("daily_energy", FloatField())),
                                           avg_te=Avg(Cast("total_energy", FloatField())),
                                           avg_oap=Avg(Cast("op_active_power", FloatField())),
                                           avg_sy=Avg(Cast('specific_yields', FloatField())))
        pr, cuf, isolation = 0, 0, 0
        irradiation = 250
        isolation = irradiation * 24

        if avg_data and avg_data['avg_sy']:
            pr = (avg_data['avg_sy'] * 100) / 24
            cuf = pr / 365 * 24 * 12
        return {"avg_data": avg_data, "pr": pr, "cuf": cuf, "irradiation": irradiation, "isolation": isolation}


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
        else:
            status = "Offline"

        end_date = datetime.datetime.strptime(self.context.get('end_date'), "%Y-%m-%d")
        end_date = end_date + datetime.timedelta(days=1)
        inverter_data = InverterData.objects.filter(device=obj, created_at__range=[self.context.get('start_date'),
                                                                                   end_date], is_active=True)
        avg_data = inverter_data.aggregate(avg_de=Avg(Cast("daily_energy", FloatField())),
                                           avg_te=Avg(Cast("total_energy", FloatField())),
                                           uid=Min(Cast("uid", FloatField()))
                                           )
        return {"avg_data": avg_data, "status": status}


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
                inverter_data = InverterData.objects.filter(device__location=location,
                                                            created_at__date__lte=validated_data.get('to_date'),
                                                            created_at__date__gte=validated_data.get('from_date'),
                                                            is_active=True)

                avg_data = inverter_data.aggregate(avg_de=Avg(Cast("daily_energy", FloatField())),
                                                   avg_te=Avg(Cast("total_energy", FloatField())),
                                                   avg_oap=Avg(Cast("op_active_power", FloatField())),
                                                   avg_sy=Avg(Cast('specific_yields', FloatField())))

                pr, cuf, insolation = 0, 0, 0
                irradiation = 250
                insolation = irradiation * 24

                if avg_data and avg_data['avg_sy']:
                    pr = (avg_data['avg_sy'] * 100) / 24
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
                    ['Daily Energy', avg_data['avg_de'], "kWh"],
                    ['Output Active Power', avg_data['avg_oap'], "kWp"],
                    ['Specific Yield', avg_data['avg_sy'], "kWh/kWp"],
                    ['CUF', cuf, "%"],
                    ['Performance Ratio', pr, "%"],
                    ['Total Energy', avg_data['avg_te'], "MWh"],
                    ['Solar Insolation', insolation, "KWh/m2"],
                    ['Solar Irradiation', irradiation, "W/m2"],
                ]
                plant_analysis_data = []

                for inverter in inverter_data.iterator():
                    inverter_pr = (int(inverter.specific_yields) * 100) / 24
                    inverter_cuf = int(inverter_pr) / 365 * 24 * 12
                    plant_analysis_data.append(
                        [inverter.created_at.replace(tzinfo=None), inverter.daily_energy, inverter.op_active_power,
                         inverter.specific_yields,
                         inverter_cuf, inverter_pr, inverter.total_energy, insolation, irradiation])

                for row in plant_summery_data:
                    ws1.append(row)

                ws2.append(
                        ["Timestamp", "Daily Energy [ kWh ]", "Output Active Power [ kWp ]",
                         "Specific Yield [ kWh/kWp ]",
                         "CUF [ % ]", "Performance Ratio [ % ]", "Total Energy [ MWh ]", "Solar Insolation [ KWh/m2 ]",
                         "Solar Irradiation [ W/m2 ]"])
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
