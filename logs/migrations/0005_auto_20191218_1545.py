# Generated by Django 2.1.7 on 2019-12-18 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0004_auto_20191218_1542'),
    ]

    operations = [
        migrations.AddField(
            model_name='approvallog',
            name='approvalError',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='approvallog',
            name='approvalStatus',
            field=models.CharField(default='전송성공', max_length=20),
        ),
    ]