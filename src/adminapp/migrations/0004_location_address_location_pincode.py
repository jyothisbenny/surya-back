# Generated by Django 4.0.4 on 2022-05-08 06:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0003_location_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='address',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='pincode',
            field=models.CharField(blank=True, default='', max_length=128, null=True),
        ),
    ]
