# Generated by Django 2.1.7 on 2019-12-23 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0007_adminemail_smtpsecure'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminemail',
            name='smtpName',
            field=models.CharField(default='로컬', max_length=10),
        ),
    ]
