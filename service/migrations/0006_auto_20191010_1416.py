# Generated by Django 2.1.7 on 2019-10-10 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0005_auto_20191010_1025'),
    ]

    operations = [
        migrations.AddField(
            model_name='geolocation',
            name='beginLatitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='geolocation',
            name='beginLongitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='geolocation',
            name='finishLatitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='geolocation',
            name='finishLongitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='servicereport',
            name='serviceBeginDatetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='geolocation',
            name='startLatitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='geolocation',
            name='startLongitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='servicereport',
            name='serviceEndDatetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='servicereport',
            name='serviceFinishDatetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='servicereport',
            name='serviceStartDatetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]