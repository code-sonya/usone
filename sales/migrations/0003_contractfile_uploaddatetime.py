# Generated by Django 2.1.7 on 2019-11-26 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0002_contractfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractfile',
            name='uploadDatetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]