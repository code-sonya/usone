# -*- coding: utf-8 -*-
from django.db import models
from hr.models import Employee
from client.models import Company, Customer


class Servicereport(models.Model):
    serviceTypeChoices = (
        ('교육', '교육'),
        ('마이그레이션', '마이그레이션'),
        ('모니터링', '모니터링'),
        ('미팅&회의', '미팅&회의'),
        ('백업&복구', '백업&복구'),
        ('상주', '상주'),
        ('설치&패치', '설치&패치'),
        ('원격지원', '원격지원'),
        ('일반작업지원', '일반작업지원'),
        ('장애지원', '장애지원'),
        ('정기점검', '정기점검'),
        ('튜닝', '튜닝'),
        ('프로젝트', '프로젝트'),
        ('프리세일즈', '프리세일즈'),
    )
    serviceLocationChoices = (('서울', '서울'), ('경기', '경기'), ('기타', '기타'))
    statusChoices = (('Y', 'Y'), ('N', 'N'))

    serviceId = models.AutoField(primary_key=True)
    serviceDate = models.DateField()
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    empName = models.CharField(max_length=10)
    empDeptName = models.CharField(max_length=30)
    companyName = models.ForeignKey(Company, on_delete=models.CASCADE)
    serviceType = models.CharField(max_length=30, choices=serviceTypeChoices)
    serviceStartDatetime = models.DateTimeField()
    serviceEndDatetime = models.DateTimeField()
    serviceFinishDatetime = models.DateTimeField()
    serviceHour = models.FloatField()
    serviceOverHour = models.FloatField()
    serviceRegHour = models.FloatField()
    serviceLocation = models.CharField(max_length=10, choices=serviceLocationChoices, default='서울')
    directgo = models.CharField(max_length=1, choices=statusChoices, default='N')
    serviceTitle = models.CharField(max_length=200, help_text="제목을 작성해 주세요.")
    serviceDetails = models.TextField(help_text="상세 내용을 작성해 주세요.")
    customerName = models.CharField(max_length=10, null=True, blank=True)
    customerDeptName = models.CharField(max_length=30, null=True, blank=True)
    customerPhone = models.CharField(max_length=20, null=True, blank=True)
    customerEmail = models.EmailField(max_length=254, null=True, blank=True)
    serviceSignPath = models.CharField(max_length=254, null=True, blank=True, default='/media/images/signature/nosign.jpg')
    serviceStatus = models.CharField(max_length=1, choices=statusChoices, default='N')

    def __str__(self):
        return 'Servicereport : {} {}'.format(self.serviceId, self.empName)


class Serviceform(models.Model):
    serviceTypeChoices = (
        ('교육', '교육'),
        ('마이그레이션', '마이그레이션'),
        ('모니터링', '모니터링'),
        ('미팅&회의', '미팅&회의'),
        ('백업&복구', '백업&복구'),
        ('상주', '상주'),
        ('설치&패치', '설치&패치'),
        ('원격지원', '원격지원'),
        ('일반작업지원', '일반작업지원'),
        ('장애지원', '장애지원'),
        ('정기점검', '정기점검'),
        ('튜닝', '튜닝'),
        ('프로젝트', '프로젝트'),
        ('프리세일즈', '프리세일즈'),
    )
    serviceLocationChoices = (('서울', '서울'), ('경기', '경기'), ('기타', '기타'))
    statusChoices = (('Y', 'Y'), ('N', 'N'))

    serviceFormId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    companyName = models.ForeignKey(Company, on_delete=models.CASCADE)
    serviceType = models.CharField(max_length=30, choices=serviceTypeChoices)
    serviceStartTime = models.TimeField()
    serviceEndTime = models.TimeField()
    serviceLocation = models.CharField(max_length=10, choices=serviceLocationChoices, default='서울')
    directgo = models.CharField(max_length=1, choices=statusChoices, default='N')
    serviceTitle = models.CharField(max_length=200, help_text="제목을 작성해 주세요.")
    serviceDetails = models.TextField(help_text="상세 내용을 작성해 주세요.")

    def __str__(self):
        return 'Serviceform : {} {}'.format(self.empId, self.companyName)


class Vacation(models.Model):
    vacationTypeChoices = (
        ('일차', '일차'),
        ('오전반차', '오전반차'),
        ('오후반차', '오후반차'),
    )

    vacationId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    empName = models.CharField(max_length=10)
    empDeptName = models.CharField(max_length=30)
    vacationDate = models.DateField()
    vacationType = models.CharField(max_length=10, choices=vacationTypeChoices, default='일차')

    def __str__(self):
        return 'Vacation : {}'.format(self.empName)