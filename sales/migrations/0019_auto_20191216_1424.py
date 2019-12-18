# Generated by Django 2.1.7 on 2019-12-16 14:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0004_customer_customertype'),
        ('hr', '0002_auto_20191206_1732'),
        ('sales', '0018_auto_20191212_1104'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchaseorder',
            fields=[
                ('orderId', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('contentHtml', models.TextField()),
                ('writeDatetime', models.DateTimeField()),
                ('modifyDatetime', models.DateTimeField()),
                ('sendDatetime', models.DateTimeField(blank=True, null=True)),
                ('contractId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.Contract')),
                ('purchaseCompany', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='client.Company')),
                ('writeEmp', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hr.Employee')),
            ],
        ),
        migrations.CreateModel(
            name='Purchaseorderfile',
            fields=[
                ('fileId', models.AutoField(primary_key=True, serialize=False)),
                ('fileCategory', models.CharField(max_length=100)),
                ('fileName', models.CharField(max_length=200)),
                ('fileSize', models.FloatField()),
                ('uploadDatetime', models.DateTimeField(blank=True, null=True)),
                ('file', models.FileField(upload_to='contract/%Y_%m')),
                ('purchaseCompany', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='client.Company')),
                ('purchaseOrder', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sales.Purchaseorder')),
                ('uploadEmp', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hr.Employee')),
            ],
        ),
        migrations.AddField(
            model_name='purchase',
            name='purchaseOrder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.Purchaseorder'),
        ),
    ]
