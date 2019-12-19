# Generated by Django 2.1.7 on 2019-12-19 16:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0022_remove_purchaseorderfile_purchasecompany'),
    ]

    operations = [
        migrations.CreateModel(
            name='Relatedpurchaseestimate',
            fields=[
                ('relatedId', models.AutoField(primary_key=True, serialize=False)),
                ('purchaseEstimate', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sales.Purchasefile')),
                ('purchaseOrder', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sales.Purchaseorder')),
            ],
        ),
    ]
