# Generated by Django 2.1.7 on 2020-01-05 22:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0025_purchasecontractitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasecontractitem',
            name='companyName',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='client.Company'),
        ),
        migrations.AlterField(
            model_name='purchasecontractitem',
            name='itemName',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
