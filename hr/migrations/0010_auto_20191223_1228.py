# Generated by Django 2.1.7 on 2019-12-23 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0009_remove_adminemail_smtpname'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adminemail',
            name='smtpDate',
        ),
        migrations.AddField(
            model_name='adminemail',
            name='smtpDatetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
