# Generated by Django 2.1.7 on 2020-03-11 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daesungwork', '0042_auto_20200311_1339'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buy',
            name='totalPrice',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='buy',
            name='vatPrice',
            field=models.IntegerField(default=0),
        ),
    ]
