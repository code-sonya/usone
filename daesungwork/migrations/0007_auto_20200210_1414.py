# Generated by Django 2.1.7 on 2020-02-10 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('daesungwork', '0006_auto_20200207_1115'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmchecklist',
            name='file',
            field=models.FileField(upload_to='checkList/'),
        ),
    ]