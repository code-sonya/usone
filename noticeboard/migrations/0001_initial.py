# Generated by Django 2.1.7 on 2020-02-21 16:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('service', '0001_initial'),
        ('hr', '0002_auto_20200221_1622'),
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('boardId', models.AutoField(primary_key=True, serialize=False)),
                ('boardTitle', models.CharField(help_text='제목을 작성해 주세요.', max_length=200)),
                ('boardDetails', models.TextField(help_text='상세 내용을 작성해 주세요.')),
                ('boardFiles', models.FileField(blank=True, null=True, upload_to='board/%Y_%m')),
                ('boardWriteDatetime', models.DateTimeField()),
                ('boardEditDatetime', models.DateTimeField()),
                ('boardWriter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hr.Employee')),
                ('serviceId', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='service.Servicereport')),
            ],
        ),
    ]
