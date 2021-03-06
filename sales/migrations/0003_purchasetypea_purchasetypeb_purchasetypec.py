# Generated by Django 2.1.7 on 2019-11-26 14:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client', '0002_auto_20191028_0031'),
        ('sales', '0002_contractfile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchasetypea',
            fields=[
                ('typeId', models.AutoField(primary_key=True, serialize=False)),
                ('contents', models.CharField(max_length=200)),
                ('price', models.IntegerField()),
                ('classNumber', models.IntegerField()),
                ('companyName', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Company')),
                ('contractId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.Contract')),
            ],
        ),
        migrations.CreateModel(
            name='Purchasetypeb',
            fields=[
                ('typeId', models.AutoField(primary_key=True, serialize=False)),
                ('classification', models.CharField(choices=[('상품_HW', '상품_HW'), ('상품_SW', '상품_SW'), ('유지보수_HW', '유지보수_HW'), ('유지보수_SW', '유지보수_SW'), ('HW', 'HW'), ('SW', 'SW'), ('PM상주', 'PM상주')], max_length=20)),
                ('times', models.IntegerField()),
                ('sites', models.IntegerField()),
                ('unitPrice', models.IntegerField()),
                ('price', models.IntegerField()),
                ('classNumber', models.IntegerField()),
                ('contractId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.Contract')),
            ],
        ),
        migrations.CreateModel(
            name='Purchasetypec',
            fields=[
                ('typeId', models.AutoField(primary_key=True, serialize=False)),
                ('classification', models.CharField(choices=[('타사 service', '타사 service'), ('HW', 'HW'), ('SW', 'SW'), ('유류', '유류'), ('PS', 'PS'), ('기타', '기타')], max_length=20)),
                ('contents', models.CharField(max_length=200)),
                ('price', models.IntegerField()),
                ('classNumber', models.IntegerField()),
                ('contractId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.Contract')),
            ],
        ),
    ]
