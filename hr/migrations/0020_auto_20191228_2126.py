# Generated by Django 2.1.7 on 2019-12-28 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0019_auto_20191228_2123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminemail',
            name='smtpEmail',
            field=models.CharField(max_length=100),
        ),
    ]
