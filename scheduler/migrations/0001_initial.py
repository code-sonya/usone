# Generated by Django 2.1.7 on 2019-04-10 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Eventday',
            fields=[
                ('eventDate', models.DateField(primary_key=True, serialize=False)),
                ('eventName', models.CharField(max_length=10)),
                ('eventType', models.CharField(choices=[('휴일', '휴일'), ('사내일정', '사내일정')], default='휴일', max_length=10)),
            ],
        ),
    ]
