# Generated by Django 2.1.7 on 2020-02-17 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extrapay', '0002_auto_20191028_0031'),
    ]

    operations = [
        migrations.AddField(
            model_name='extrapay',
            name='empSalary',
            field=models.IntegerField(default=0),
        ),
    ]
