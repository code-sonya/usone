# Generated by Django 2.1.7 on 2019-12-23 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0004_auto_20191223_1013'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adminemail',
            name='smtpDatetime',
        ),
        migrations.AddField(
            model_name='adminemail',
            name='smtpDate',
            field=models.DateField(blank=True, null=True),
        ),
    ]