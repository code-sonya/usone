# Generated by Django 2.1.7 on 2019-11-28 09:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0001_initial'),
        ('sales', '0008_merge_20191127_1553'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractfile',
            name='uploadEmp',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hr.Employee'),
        ),
    ]
