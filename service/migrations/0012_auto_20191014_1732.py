# Generated by Django 2.1.7 on 2019-10-14 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0011_auto_20191011_1536'),
    ]

    operations = [
        migrations.AddField(
            model_name='fuel',
            name='distance3',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='fuel',
            name='distance1',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='fuel',
            name='distance2',
            field=models.FloatField(default=0),
        ),
    ]
