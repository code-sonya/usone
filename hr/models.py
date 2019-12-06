# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


class Position(models.Model):
    positionId = models.IntegerField(primary_key=True)
    positionName = models.CharField(max_length=10)
    positionSalary = models.IntegerField(default=0)

    def __str__(self):
        return self.positionName


class Employee(models.Model):
    empDeptNameChoices = (
        ('임원', '임원'),
        ('경영지원본부', '경영지원본부'),
        ('영업1팀', '영업1팀'),
        ('영업2팀', '영업2팀'),
        ('영업3팀', '영업3팀'),
        ('인프라서비스사업팀', '인프라서비스사업팀'),
        ('솔루션지원팀', '솔루션지원팀'),
        ('DB지원팀', 'DB지원팀'),
        ('미정', '미정')
    )
    statusChoices = (('Y', 'Y'), ('N', 'N'))

    empId = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    empCode = models.CharField(max_length=20, null=True, blank=True)
    empName = models.CharField(max_length=10)
    empPosition = models.ForeignKey(Position, on_delete=models.PROTECT)
    empManager = models.CharField(max_length=1, choices=statusChoices, default='N')
    empPhone = models.CharField(max_length=20)
    empEmail = models.EmailField(max_length=254)
    empDeptName = models.CharField(max_length=30, choices=empDeptNameChoices, default='미정')
    departmentName = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    dispatchCompany = models.CharField(max_length=100, default='내근')
    message = models.CharField(max_length=200, default='내근 업무 내용을 작성해 주세요.', help_text='내근 업무 내용을 작성해 주세요.')
    carId = models.ForeignKey("extrapay.Car", on_delete=models.SET_NULL, null=True, blank=True)
    empAuth = models.CharField(max_length=10, default='일반')
    empRank = models.IntegerField(default=10)
    empSalary = models.IntegerField(default=0)
    empStartDate = models.DateField(null=True, blank=True)
    empEndDate = models.DateField(null=True, blank=True)
    empStatus = models.CharField(max_length=1, choices=statusChoices, default='Y')

    def __str__(self):
        return self.empName


class Attendance(models.Model):
    attendanceId = models.AutoField(primary_key=True)
    attendanceDate = models.DateField()
    attendanceTime = models.TimeField()
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    attendanceType = models.CharField(max_length=20)

    def __str__(self):
        return str(self.attendanceId)


class Punctuality(models.Model):
    punctualityId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    punctualityDate = models.DateField()
    punctualityType = models.CharField(max_length=20)
    comment = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return str(self.punctualityId)


class Department(models.Model):
    deptId = models.AutoField(primary_key=True)
    deptName = models.CharField(max_length=20)
    deptManager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    deptLevel = models.IntegerField(default=0)
    parentDept = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.deptName)
