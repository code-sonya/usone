# Generated by Django 2.1.7 on 2020-02-27 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daesungwork', '0035_remove_buy_unitprice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buy',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='buy',
            name='salePrice',
            field=models.IntegerField(default=0),
        ),
    ]