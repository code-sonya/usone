# Generated by Django 2.1.5 on 2019-03-21 18:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('service', '0002_auto_20190322_0255'),
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('boardId', models.AutoField(primary_key=True, serialize=False)),
                ('boardWriter', models.CharField(max_length=10)),
                ('boardTitle', models.CharField(help_text='제목을 작성해 주세요.', max_length=200)),
                ('boardDetails', models.TextField(help_text='상세 내용을 작성해 주세요.')),
                ('boardFiles', models.FileField(blank=True, null=True, upload_to='')),
                ('boardWriteDatetime', models.DateTimeField()),
                ('boardEditDatetime', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Serviceboard',
            fields=[
                ('serviceBoardId', models.AutoField(primary_key=True, serialize=False)),
                ('serviceDate', models.DateField()),
                ('companyName', models.CharField(max_length=100)),
                ('serviceType', models.CharField(choices=[('교육', '교육'), ('마이그레이션', '마이그레이션'), ('모니터링', '모니터링'), ('미팅&회의', '미팅&회의'), ('백업&복구', '백업&복구'), ('상주', '상주'), ('설치&패치', '설치&패치'), ('원격지원', '원격지원'), ('일반작업지원', '일반작업지원'), ('장애지원', '장애지원'), ('정기점검', '정기점검'), ('튜닝', '튜닝'), ('프로젝트', '프로젝트'), ('프리세일즈', '프리세일즈'), ('휴가', '휴가')], max_length=30)),
                ('empDeptName', models.CharField(max_length=30)),
                ('empName', models.CharField(max_length=10)),
                ('serviceBoardWriter', models.CharField(max_length=10)),
                ('serviceBoardTitle', models.CharField(help_text='제목을 작성해 주세요.', max_length=200)),
                ('serviceBoardDetails', models.TextField(help_text='상세 내용을 작성해 주세요.')),
                ('serviceBoardFiles', models.FileField(blank=True, null=True, upload_to='')),
                ('serviceBoardWriteDatetime', models.DateTimeField()),
                ('serviceBoardEditDatetime', models.DateTimeField()),
                ('serviceId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service.Servicereport')),
            ],
        ),
    ]
