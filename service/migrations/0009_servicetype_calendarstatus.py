# Generated by Django 2.1.7 on 2020-02-20 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0008_auto_20200122_1716'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicetype',
            name='calendarStatus',
            field=models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='Y', max_length=10),
        ),
    ]