# Generated by Django 2.1.7 on 2019-12-28 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0016_employee_emprewardavailable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='empRewardAvailable',
            field=models.CharField(choices=[('불가능', '불가능'), ('가능', '가능')], default='불가능', max_length=10),
        ),
    ]
