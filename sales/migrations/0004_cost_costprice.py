# Generated by Django 2.1.7 on 2019-08-02 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0003_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='cost',
            name='costPrice',
            field=models.BigIntegerField(default=0),
        ),
    ]
