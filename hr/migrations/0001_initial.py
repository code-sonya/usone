# Generated by Django 2.1.7 on 2019-04-10 10:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('empId', models.AutoField(primary_key=True, serialize=False)),
                ('empName', models.CharField(max_length=10)),
                ('empPosition', models.IntegerField(choices=[(1, '임원'), (2, '부장'), (3, '차장'), (4, '과장'), (5, '대리'), (6, '사원')], default=6)),
                ('empManager', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='N', max_length=1)),
                ('empPhone', models.CharField(max_length=20)),
                ('empEmail', models.EmailField(max_length=254)),
                ('empDeptName', models.CharField(choices=[('임원', '임원'), ('경영지원본부', '경영지원본부'), ('영업1팀', '영업1팀'), ('영업2팀', '영업2팀'), ('영업3팀', '영업3팀'), ('인프라서비스사업팀', '인프라서비스사업팀'), ('솔루션지원팀', '솔루션지원팀'), ('DB지원팀', 'DB지원팀'), ('미정', '미정')], default='미정', max_length=30)),
                ('dispatchCompany', models.CharField(default='내근', max_length=100)),
                ('message', models.CharField(default='내근 업무 내용을 작성해 주세요.', help_text='내근 업무 내용을 작성해 주세요.', max_length=200)),
                ('empStatus', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='Y', max_length=1)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
