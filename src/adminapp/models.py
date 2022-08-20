from django.db import models
import jsonfield

from ..accounts.models import User
from ..base.models import TimeStampedModel, BaseModel
from ..base.validators.form_validations import file_extension_validator


# Create your models here.
class Location(TimeStampedModel):
    name = models.CharField(max_length=128, blank=True, null=True, default='')
    address = models.CharField(max_length=1024, null=True, blank=True)
    pincode = models.CharField(max_length=128, blank=True, null=True, default='')
    user = models.ManyToManyField(User, related_name='location_users', blank=True)
    latitude = models.CharField(max_length=128, blank=True, null=True, default='')
    longitude = models.CharField(max_length=128, blank=True, null=True, default='')
    inverter_type = models.CharField(max_length=128, blank=True, null=True, default='')
    is_suspended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class Device(TimeStampedModel):
    device_name = models.CharField(max_length=128, blank=True, null=True, default='')
    imei = models.CharField(max_length=128, blank=True, null=True, default='')
    location = models.ForeignKey(Location, blank=True, null=True, on_delete=models.PROTECT)
    is_suspended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class InverterJsonData(BaseModel):
    data = jsonfield.JSONField()
    is_active = models.BooleanField(default=True)


class InverterData(BaseModel):
    device = models.ForeignKey(Device, blank=True, null=True, on_delete=models.PROTECT)
    imei = models.CharField(max_length=128, blank=True, null=True, default='')
    sid = models.CharField(max_length=128, blank=True, null=True, default='')
    uid = models.CharField(max_length=128, blank=True, null=True, default='')
    rcnt = models.CharField(max_length=128, blank=True, null=True, default='')
    daily_energy = models.FloatField(blank=True, null=True)
    total_energy = models.FloatField(blank=True, null=True)
    op_active_power = models.FloatField(blank=True, null=True)
    specific_yields = models.FloatField(blank=True, null=True)
    inverter_op_active_power = models.FloatField(blank=True, null=True)
    inverter_daily_energy = models.FloatField(blank=True, null=True)
    inverter_total_energy = models.FloatField(blank=True, null=True)
    meter_active_power = models.FloatField(blank=True, null=True)
    # meter_active_energy = models.CharField(max_length=128, blank=True, null=True, default='')
    is_active = models.BooleanField(default=True)


class ZipReport(BaseModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    name = models.CharField(max_length=128, blank=True, null=True, default='')
    from_date = models.DateTimeField(blank=True, null=True)
    to_date = models.DateTimeField(blank=True, null=True)
    frequency = models.CharField(max_length=128, blank=True, null=True, default='')
    category = models.CharField(max_length=128, blank=True, null=True, default='')
    status = models.CharField(max_length=128, blank=True, null=True, default='')
    zip_file = models.FileField(upload_to="reports/%Y/%m/%d", max_length=80, blank=True, null=True,
                                validators=[file_extension_validator])
    location = models.ManyToManyField(Location, blank=True)
    is_active = models.BooleanField(default=True)
