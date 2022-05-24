from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status

from ..accounts.serializers import UserSerializer
from .models import Location, Device, InverterData, InverterJsonData
from ..base.serializers import ModelSerializer


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
