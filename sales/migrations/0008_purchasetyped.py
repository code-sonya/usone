# Generated by Django 2.1.7 on 2019-11-27 16:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0007_auto_20191127_1527'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchasetyped',
            fields=[
                ('typeId', models.AutoField(primary_key=True, serialize=False)),
                ('contractNo', models.CharField(max_length=50)),
                ('contractStartDate', models.DateField()),
                ('contractEndDate', models.DateField()),
                ('price', models.IntegerField()),
                ('classNumber', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9)])),
                ('contractId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.Contract')),
            ],
        ),
    ]
