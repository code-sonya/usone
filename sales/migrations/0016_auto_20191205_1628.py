# Generated by Django 2.1.7 on 2019-12-05 16:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0004_customer_customertype'),
        ('sales', '0015_auto_20191204_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='saleTaxCustomerId',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='saleTaxCustomerId', to='client.Customer'),
        ),
        migrations.AddField(
            model_name='contract',
            name='saleTaxCustomerName',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
