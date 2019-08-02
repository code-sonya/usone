# Generated by Django 2.1.7 on 2019-07-31 13:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0002_punctuality'),
    ]

    operations = [
        migrations.CreateModel(
            name='Position',
            fields=[
                ('positionId', models.IntegerField(primary_key=True, serialize=False)),
                ('positionName', models.CharField(max_length=10)),
                ('positionSalary', models.IntegerField(default=0)),
            ],
        ),
        migrations.AddField(
            model_name='employee',
            name='empEndDate',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='employee',
            name='empSalary',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='employee',
            name='empStartDate',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='empPosition',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='hr.Position'),
        ),
    ]
