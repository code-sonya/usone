# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django import forms


class Position(models.Model):
    positionId = models.IntegerField(primary_key=True)
    positionName = models.CharField(max_length=10)
    positionSalary = models.IntegerField(default=0)

    def __str__(self):
        return self.positionName


class Employee(models.Model):
    statusChoices = (
        ('Y', '재직'), ('N', '퇴사')
    )
    managerChoices = (
        ('Y', '부서장'), ('N', '팀원')
    )

    empId = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    empCode = models.CharField(max_length=20, null=True, blank=True)
    empName = models.CharField(max_length=10)
    empPosition = models.ForeignKey(Position, on_delete=models.PROTECT)
    empManager = models.CharField(max_length=1, choices=managerChoices, default='N')
    empPhone = models.CharField(max_length=20)
    empEmail = models.EmailField(max_length=254)
    empDeptName = models.CharField(max_length=30, null=True, blank=True)
    departmentName = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    dispatchCompany = models.CharField(max_length=100, default='내근')
    message = models.CharField(max_length=200, default='내근 업무 내용을 작성해 주세요.', help_text='내근 업무 내용을 작성해 주세요.')
    carId = models.ForeignKey("extrapay.Car", on_delete=models.SET_NULL, null=True, blank=True)
    empAuth = models.CharField(max_length=10, default='일반')
    empRank = models.IntegerField(default=10)
    empSalary = models.IntegerField(default=0)
    empStartDate = models.DateField(null=True, blank=True)
    empEndDate = models.DateField(null=True, blank=True)
    empStamp = models.FileField(upload_to="stamp/", default='stamp/accepted.png')
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
    deptName = models.CharField(max_length=20, unique=True)
    deptManager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    deptLevel = models.IntegerField(default=0)
    parentDept = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.deptName)

class AdminEmail(models.Model):
    adminId = models.AutoField(primary_key=True)
    smtpServer = models.CharField(max_length=20)
    smtpPort = models.CharField(max_length=10)
    smtpEmail = models.CharField(max_length=20)
    smtpPassword = models.CharField(forms.PasswordInput, max_length=20)
    smtpSecure = models.CharField(max_length=10, null=True, blank=True)
    smtpDatetime = models.DateTimeField(null=True, blank=True)
    smtpStatus = models.CharField(max_length=10, default='정상')

    def __str__(self):
        return str(self.adminId)


class AdminVacation(models.Model):
    vacationId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    vacationType = models.CharField(max_length=20)
    vacationDays = models.FloatField()
    creationDateTime = models.DateTimeField()
    expirationDate = models.DateField(null=True, blank=True)
    comment = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return str(self.vacationId)
