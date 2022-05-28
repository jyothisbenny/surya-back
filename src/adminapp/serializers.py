from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status
import datetime
from django.db.models import Avg, Min, FloatField
from django.db.models.functions import Cast

from ..accounts.serializers import UserSerializer
from .models import Location, Device, InverterData, InverterJsonData
from ..base.serializers import ModelSerializer
from ..base.utils import timezone

now = timezone.now_local()


class LocationSerializer(ModelSerializer):
    user_data = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Location
        fields = '__all__'

    def validate(self, data):
        print(data)
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
        print("-----___=-", inverter_data)
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
        print(pr, cuf, irradiation, isolation)
        return {"avg_data": avg_data, "pr": pr, "cuf": cuf, "irradiation": irradiation, "isolation": isolation}


class DeviceSummarySerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Device
        fields = '__all__'

    def get_summary(self, obj):
        print(obj.imei)
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
        end_date = end_date + datetime.timedelta(days=10)
        inverter_data = InverterData.objects.filter(device=obj, created_at__range=[self.context.get('start_date'),
                                                                                   end_date], is_active=True)
        avg_data = inverter_data.aggregate(avg_de=Avg(Cast("daily_energy", FloatField())),
                                           avg_te=Avg(Cast("total_energy", FloatField())),
                                           uid=Min(Cast("uid", FloatField()))
                                           )
        return {"avg_data": avg_data, "status": status}
