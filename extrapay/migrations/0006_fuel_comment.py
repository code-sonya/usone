# Generated by Django 2.1.7 on 2019-10-16 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extrapay', '0005_auto_20191015_1432'),
    ]

    operations = [
        migrations.AddField(
            model_name='fuel',
            name='comment',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]