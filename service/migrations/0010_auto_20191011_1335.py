# Generated by Django 2.1.7 on 2019-10-11 13:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0009_car_fuel_oil'),
    ]

    operations = [
        migrations.RenameField(
            model_name='oil',
            old_name='carType',
            new_name='carId',
        ),
    ]
