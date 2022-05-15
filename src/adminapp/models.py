from django.db import models

from ..accounts.models import User
from ..base.models import TimeStampedModel


# Create your models here.
class Location(TimeStampedModel):
    name = models.CharField(max_length=128, blank=True, null=True, default='')
    address = models.CharField(max_length=1024, null=True, blank=True)
    pincode = models.CharField(max_length=128, blank=True, null=True, default='')
    user = models.ManyToManyField(User, related_name='location_users', blank=True)
    is_suspended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class Device(TimeStampedModel):
    device_name = models.CharField(max_length=128, blank=True, null=True, default='')
    location = models.ForeignKey(Location, blank=True, null=True, on_delete=models.PROTECT)
    is_suspended = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

