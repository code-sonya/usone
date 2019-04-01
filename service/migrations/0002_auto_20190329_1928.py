# Generated by Django 2.1.5 on 2019-03-29 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serviceform',
            name='serviceType',
            field=models.CharField(choices=[('교육', '교육'), ('마이그레이션', '마이그레이션'), ('모니터링', '모니터링'), ('미팅&회의', '미팅&회의'), ('백업&복구', '백업&복구'), ('상주', '상주'), ('설치&패치', '설치&패치'), ('원격지원', '원격지원'), ('일반작업지원', '일반작업지원'), ('장애지원', '장애지원'), ('정기점검', '정기점검'), ('튜닝', '튜닝'), ('프로젝트', '프로젝트'), ('프리세일즈', '프리세일즈')], max_length=30),
        ),
        migrations.AlterField(
            model_name='servicereport',
            name='serviceType',
            field=models.CharField(choices=[('교육', '교육'), ('마이그레이션', '마이그레이션'), ('모니터링', '모니터링'), ('미팅&회의', '미팅&회의'), ('백업&복구', '백업&복구'), ('상주', '상주'), ('설치&패치', '설치&패치'), ('원격지원', '원격지원'), ('일반작업지원', '일반작업지원'), ('장애지원', '장애지원'), ('정기점검', '정기점검'), ('튜닝', '튜닝'), ('프로젝트', '프로젝트'), ('프리세일즈', '프리세일즈')], max_length=30),
        ),
    ]
