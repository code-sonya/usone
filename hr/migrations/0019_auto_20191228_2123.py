# Generated by Django 2.1.7 on 2019-12-28 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0018_auto_20191228_1903'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminemail',
            name='smtpStatus',
            field=models.CharField(default='정상', max_length=200),
        ),
    ]
