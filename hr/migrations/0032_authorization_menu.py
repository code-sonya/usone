# Generated by Django 2.1.7 on 2020-03-10 17:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0031_employee_profilephoto'),
    ]

    operations = [
        migrations.CreateModel(
            name='Authorization',
            fields=[
                ('authorizationId', models.AutoField(primary_key=True, serialize=False)),
                ('empId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hr.Employee')),
            ],
        ),
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('menuId', models.AutoField(primary_key=True, serialize=False)),
                ('menuName', models.CharField(blank=True, max_length=20, null=True)),
                ('defaultStatus', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='N', max_length=10)),
            ],
        ),
    ]