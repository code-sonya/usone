# Generated by Django 2.1.7 on 2020-02-26 13:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('daesungwork', '0021_auto_20200226_1313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sale',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='daesungwork.Product'),
        ),
    ]