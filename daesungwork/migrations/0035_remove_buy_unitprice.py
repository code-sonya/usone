# Generated by Django 2.1.7 on 2020-02-27 19:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('daesungwork', '0034_buy'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='buy',
            name='unitPrice',
        ),
    ]