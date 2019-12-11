# Generated by Django 2.1.7 on 2019-12-09 15:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0002_auto_20191206_1732'),
        ('client', '0004_customer_customertype'),
        ('sales', '0016_auto_20191205_1628'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchasecategory',
            fields=[
                ('categoryId', models.AutoField(primary_key=True, serialize=False)),
                ('purchaseType', models.CharField(max_length=50)),
                ('categoryName', models.CharField(max_length=50)),
                ('orderNumber', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Purchasefile',
            fields=[
                ('fileId', models.AutoField(primary_key=True, serialize=False)),
                ('fileCategory', models.CharField(max_length=100)),
                ('fileName', models.CharField(max_length=200)),
                ('fileSize', models.FloatField()),
                ('uploadDatetime', models.DateTimeField(blank=True, null=True)),
                ('file', models.FileField(upload_to='contract/%Y_%m')),
                ('contractId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.Contract')),
                ('purchaseCompany', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='client.Company')),
                ('uploadEmp', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hr.Employee')),
            ],
        ),
    ]