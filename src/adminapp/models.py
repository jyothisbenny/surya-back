from django.db import models
import jsonfield

from ..accounts.models import User
from ..base.models import TimeStampedModel, BaseModel


# Create your models here.
class Location(TimeStampedModel):
    name = models.CharField(max_length=128, blank=True, null=True, default='')
    address = models.CharField(max_length=1024, null=True, blank=True)
    pincode = models.CharField(max_length=128, blank=True, null=True, default='')
    user = models.ManyToManyField(User, related_name='location_users', blank=True)
    latitude = models.CharField(max_length=128, blank=True, null=True, default='')
    longitude = models.CharField(max_length=128, blank=True, null=True, default='')
    is_suspended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class Device(TimeStampedModel):
    device_name = models.CharField(max_length=128, blank=True, null=True, default='')
    location = models.ForeignKey(Location, blank=True, null=True, on_delete=models.PROTECT)
    is_suspended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class InverterJsonData(BaseModel):
    data = jsonfield.JSONField()
    is_active = models.BooleanField(default=True)




class InverterData(BaseModel):
    imei = models.CharField(max_length=128, blank=True, null=True, default='')
    sid = models.CharField(max_length=128, blank=True, null=True, default='')
    uid = models.CharField(max_length=128, blank=True, null=True, default='')
    rcnt = models.CharField(max_length=128, blank=True, null=True, default='')
    daily_energy = models.CharField(max_length=128, blank=True, null=True, default='')
    total_energy = models.CharField(max_length=128, blank=True, null=True, default='')
    op_active_power = models.CharField(max_length=128, blank=True, null=True, default='')
    specific_yields = models.CharField(max_length=128, blank=True, null=True, default='')
    inverter_op_active_power = models.CharField(max_length=128, blank=True, null=True, default='')
    inverter_daily_energy = models.CharField(max_length=128, blank=True, null=True, default='')
    inverter_total_energy = models.CharField(max_length=128, blank=True, null=True, default='')
    meter_active_power = models.CharField(max_length=128, blank=True, null=True, default='')
    # meter_active_energy = models.CharField(max_length=128, blank=True, null=True, default='')
    is_active = models.BooleanField(default=True)
