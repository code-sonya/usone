# -*- coding: utf-8 -*-
from django.db import models
from hr.models import Employee
from client.models import Company, Customer
from sales.models import Contract
from extrapay.models import OverHour


class Servicereport(models.Model):
    serviceTypeChoices = (
        ('교육', '교육'),
        ('마이그레이션', '마이그레이션'),
        ('모니터링', '모니터링'),
        ('미팅&회의', '미팅&회의'),
        ('백업&복구', '백업&복구'),
        ('프로젝트상주', '프로젝트상주'),
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
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    serviceDate = models.DateField()
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    empName = models.CharField(max_length=10)
    empDeptName = models.CharField(max_length=30)
    companyName = models.ForeignKey(Company, on_delete=models.CASCADE)
    serviceType = models.CharField(max_length=30, choices=serviceTypeChoices)
    serviceBeginDatetime = models.DateTimeField(null=True, blank=True)
    serviceStartDatetime = models.DateTimeField(null=True, blank=True)
    serviceEndDatetime = models.DateTimeField(null=True, blank=True)
    serviceFinishDatetime = models.DateTimeField(null=True, blank=True)
    serviceHour = models.FloatField()
    serviceOverHour = models.FloatField()
    serviceRegHour = models.FloatField()
    serviceLocation = models.CharField(max_length=10, choices=serviceLocationChoices, default='서울')
    directgo = models.CharField(max_length=1, choices=statusChoices, default='N')
    coWorker = models.CharField(max_length=200, null=True, blank=True)
    serviceTitle = models.CharField(max_length=200, help_text="제목을 작성해 주세요.")
    serviceDetails = models.TextField(help_text="상세 내용을 작성해 주세요.")
    customerName = models.CharField(max_length=10, null=True, blank=True)
    customerDeptName = models.CharField(max_length=30, null=True, blank=True)
    customerPhone = models.CharField(max_length=20, null=True, blank=True)
    customerEmail = models.EmailField(max_length=254, null=True, blank=True)
    serviceSignPath = models.CharField(max_length=254, default='/media/images/signature/nosign.jpg')
    overHourId = models.ForeignKey(OverHour, on_delete=models.CASCADE, null=True, blank=True)
    serviceStatus = models.CharField(max_length=1, default='N')

    def __str__(self):
        return 'Servicereport : {} {}'.format(self.serviceId, self.empName)


class Serviceform(models.Model):
    serviceTypeChoices = (
        ('교육', '교육'),
        ('마이그레이션', '마이그레이션'),
        ('모니터링', '모니터링'),
        ('미팅&회의', '미팅&회의'),
        ('백업&복구', '백업&복구'),
        ('프로젝트상주', '프로젝트상주'),
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
    statusChoices = (('N', 'N'), ('B', 'B'), ('S', 'S'), ('E', 'E'), ('Y', 'Y'))

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


class Geolocation(models.Model):
    geolocationId = models.AutoField(primary_key=True)
    serviceId = models.ForeignKey(Servicereport, on_delete=models.CASCADE)
    beginLatitude = models.FloatField(null=True, blank=True)
    beginLongitude = models.FloatField(null=True, blank=True)
    startLatitude = models.FloatField(null=True, blank=True)
    startLongitude = models.FloatField(null=True, blank=True)
    endLatitude = models.FloatField(null=True, blank=True)
    endLongitude = models.FloatField(null=True, blank=True)
    finishLatitude = models.FloatField(null=True, blank=True)
    finishLongitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return str(self.serviceId)


class Car(models.Model):
    carId = models.AutoField(primary_key=True)
    oilType = models.CharField(max_length=10)
    carType = models.CharField(max_length=10)
    comment = models.CharField(max_length=20, null=True, blank=True)
    kpl = models.FloatField()

    def __str__(self):
        return self.oilType + ', ' + self.carType


class Oil(models.Model):
    oilId = models.AutoField(primary_key=True)
    oilDate = models.DateField()
    carId = models.ForeignKey(Car, on_delete=models.CASCADE)
    oilMoney = models.FloatField()
    mpk = models.IntegerField()

    def __str__(self):
        return str(self.oilDate) + ', ' + str(self.carId)


class Fuel(models.Model):
    fuelId = models.AutoField(primary_key=True)
    serviceId = models.ForeignKey(Servicereport, on_delete=models.CASCADE)
    distance1 = models.FloatField()
    distance2 = models.FloatField()
    totalDistance = models.FloatField()
    fuelMoney = models.IntegerField(null=True, blank=True)
    fuelStatus = models.CharField(max_length=1, default='N')

    def __str__(self):
        return str(self.fuelId)
