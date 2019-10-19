# Generated by Django 2.1.7 on 2019-10-18 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extrapay', '0011_merge_20191017_1621'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extrapay',
            name='compensatedHour',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='overhour',
            name='foodCost',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='overhour',
            name='overHour',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='overhour',
            name='overHourCost',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='overhour',
            name='overHourCostWeekDay',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='overhour',
            name='overHourWeekDay',
            field=models.FloatField(blank=True, default=0, null=True),
        ),
    ]