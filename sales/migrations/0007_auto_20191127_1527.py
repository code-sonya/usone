# Generated by Django 2.1.7 on 2019-11-27 15:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0006_auto_20191126_1630'),
    ]

    operations = [
        migrations.RenameField(
            model_name='purchasetypeb',
            old_name='unitPrice',
            new_name='units',
        ),
    ]
