# Generated by Django 2.1.7 on 2020-01-15 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0021_returnvacation'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnvacation',
            name='returnDateTime',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]