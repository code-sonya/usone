# Generated by Django 2.1.7 on 2020-02-10 16:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0029_auto_20200131_1720'),
        ('supply', '0006_saving_standard'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavingQuantity',
            fields=[
                ('quantityId', models.AutoField(primary_key=True, serialize=False)),
                ('quantity', models.IntegerField(default=0)),
                ('standard', models.CharField(blank=True, max_length=100, null=True)),
                ('purchaseCompany', models.CharField(blank=True, max_length=100, null=True)),
                ('purchaseDate', models.DateField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('purchaseEmp', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hr.Employee')),
            ],
        ),
        migrations.RemoveField(
            model_name='saving',
            name='comment',
        ),
        migrations.RemoveField(
            model_name='saving',
            name='location',
        ),
        migrations.RemoveField(
            model_name='saving',
            name='purchaseCompany',
        ),
        migrations.RemoveField(
            model_name='saving',
            name='purchaseDate',
        ),
        migrations.RemoveField(
            model_name='saving',
            name='purchaseEmp',
        ),
        migrations.RemoveField(
            model_name='saving',
            name='quantity',
        ),
        migrations.RemoveField(
            model_name='saving',
            name='standard',
        ),
        migrations.AddField(
            model_name='savingquantity',
            name='savingId',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='supply.Saving'),
        ),
    ]