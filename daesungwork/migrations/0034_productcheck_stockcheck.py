# Generated by Django 2.1.7 on 2020-02-27 19:23

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0030_auto_20200212_1322'),
        ('daesungwork', '0033_merge_20200227_1650'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCheck',
            fields=[
                ('productcheckId', models.AutoField(primary_key=True, serialize=False)),
                ('productGap', models.CharField(blank=True, default='', max_length=10, null=True)),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='daesungwork.Product')),
            ],
        ),
        migrations.CreateModel(
            name='StockCheck',
            fields=[
                ('stockcheckId', models.AutoField(primary_key=True, serialize=False)),
                ('checkDate', models.DateField()),
                ('createdDate', models.DateTimeField(default=django.utils.timezone.now)),
                ('modifyDate', models.DateTimeField(default=django.utils.timezone.now)),
                ('checkEmp', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hr.Employee')),
            ],
        ),
    ]
