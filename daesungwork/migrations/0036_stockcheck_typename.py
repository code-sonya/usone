# Generated by Django 2.1.7 on 2020-02-27 19:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('daesungwork', '0035_productcheck_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockcheck',
            name='typeName',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='daesungwork.Type'),
        ),
    ]
