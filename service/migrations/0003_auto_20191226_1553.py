# Generated by Django 2.1.7 on 2019-12-26 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0002_auto_20191224_1456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicereport',
            name='serviceOverHour',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='servicereport',
            name='serviceRegHour',
            field=models.FloatField(blank=True, null=True),
        ),
    ]