# Generated by Django 2.1.7 on 2020-02-25 10:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('daesungwork', '0015_auto_20200224_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='unitPrice',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='sale',
            name='size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='daesungwork.Size'),
        ),
    ]
