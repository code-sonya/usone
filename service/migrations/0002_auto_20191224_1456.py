# Generated by Django 2.1.7 on 2019-12-24 14:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Servicetype',
            fields=[
                ('typeId', models.AutoField(primary_key=True, serialize=False)),
                ('typeName', models.CharField(max_length=30)),
                ('orderNumber', models.IntegerField(default=0)),
            ],
        ),
        migrations.AlterField(
            model_name='servicereport',
            name='serviceType',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='service.Servicetype'),
        ),
    ]
