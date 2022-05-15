from rest_framework import serializers

from ..accounts.serializers import UserSerializer
from .models import Location, Device
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

    @staticmethod
    def get_location_data(obj):
        return LocationSerializer(obj.location).data if obj.location else None

