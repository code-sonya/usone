# Generated by Django 2.1.7 on 2019-05-14 16:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hr', '0001_initial'),
        ('client', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Serviceform',
            fields=[
                ('serviceFormId', models.AutoField(primary_key=True, serialize=False)),
                ('serviceType', models.CharField(choices=[('교육', '교육'), ('마이그레이션', '마이그레이션'), ('모니터링', '모니터링'), ('미팅&회의', '미팅&회의'), ('백업&복구', '백업&복구'), ('상주', '상주'), ('설치&패치', '설치&패치'), ('원격지원', '원격지원'), ('일반작업지원', '일반작업지원'), ('장애지원', '장애지원'), ('정기점검', '정기점검'), ('튜닝', '튜닝'), ('프로젝트', '프로젝트'), ('프리세일즈', '프리세일즈')], max_length=30)),
                ('serviceStartTime', models.TimeField()),
                ('serviceEndTime', models.TimeField()),
                ('serviceLocation', models.CharField(choices=[('서울', '서울'), ('경기', '경기'), ('기타', '기타')], default='서울', max_length=10)),
                ('directgo', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='N', max_length=1)),
                ('serviceTitle', models.CharField(help_text='제목을 작성해 주세요.', max_length=200)),
                ('serviceDetails', models.TextField(help_text='상세 내용을 작성해 주세요.')),
                ('companyName', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Company')),
                ('empId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hr.Employee')),
            ],
        ),
        migrations.CreateModel(
            name='Servicereport',
            fields=[
                ('serviceId', models.AutoField(primary_key=True, serialize=False)),
                ('serviceDate', models.DateField()),
                ('empName', models.CharField(max_length=10)),
                ('empDeptName', models.CharField(max_length=30)),
                ('serviceType', models.CharField(choices=[('교육', '교육'), ('마이그레이션', '마이그레이션'), ('모니터링', '모니터링'), ('미팅&회의', '미팅&회의'), ('백업&복구', '백업&복구'), ('상주', '상주'), ('설치&패치', '설치&패치'), ('원격지원', '원격지원'), ('일반작업지원', '일반작업지원'), ('장애지원', '장애지원'), ('정기점검', '정기점검'), ('튜닝', '튜닝'), ('프로젝트', '프로젝트'), ('프리세일즈', '프리세일즈')], max_length=30)),
                ('serviceStartDatetime', models.DateTimeField()),
                ('serviceEndDatetime', models.DateTimeField()),
                ('serviceFinishDatetime', models.DateTimeField()),
                ('serviceHour', models.FloatField()),
                ('serviceOverHour', models.FloatField()),
                ('serviceRegHour', models.FloatField()),
                ('serviceLocation', models.CharField(choices=[('서울', '서울'), ('경기', '경기'), ('기타', '기타')], default='서울', max_length=10)),
                ('directgo', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='N', max_length=1)),
                ('coWorker', models.CharField(blank=True, max_length=200, null=True)),
                ('serviceTitle', models.CharField(help_text='제목을 작성해 주세요.', max_length=200)),
                ('serviceDetails', models.TextField(help_text='상세 내용을 작성해 주세요.')),
                ('customerName', models.CharField(blank=True, max_length=10, null=True)),
                ('customerDeptName', models.CharField(blank=True, max_length=30, null=True)),
                ('customerPhone', models.CharField(blank=True, max_length=20, null=True)),
                ('customerEmail', models.EmailField(blank=True, max_length=254, null=True)),
                ('serviceSignPath', models.CharField(default='/media/images/signature/nosign.jpg', max_length=254)),
                ('serviceStatus', models.CharField(choices=[('Y', 'Y'), ('N', 'N')], default='N', max_length=1)),
                ('companyName', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.Company')),
                ('empId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hr.Employee')),
            ],
        ),
        migrations.CreateModel(
            name='Vacation',
            fields=[
                ('vacationId', models.AutoField(primary_key=True, serialize=False)),
                ('empName', models.CharField(max_length=10)),
                ('empDeptName', models.CharField(max_length=30)),
                ('vacationDate', models.DateField()),
                ('vacationType', models.CharField(choices=[('일차', '일차'), ('오전반차', '오전반차'), ('오후반차', '오후반차')], default='일차', max_length=10)),
                ('empId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hr.Employee')),
            ],
        ),
    ]
