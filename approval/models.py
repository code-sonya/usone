# -*- coding: utf-8 -*-
from django.db import models
from hr.models import Employee


class Documentcategory(models.Model):
    categoryId = models.AutoField(primary_key=True)
    firstCategory = models.CharField(max_length=20, default='공통')
    secondCategory = models.CharField(max_length=20, default='공통')
    thirdCategory = models.CharField(max_length=20, default='공통')


class Docuform(models.Model):
    formId = models.AutoField(primary_key=True)
    formNumber = models.IntegerField(unique=True)
    categoryId = models.ForeignKey(Documentcategory, on_delete=models.SET_NULL, null=True, blank=True)
    formHtml = models.TextField()


class Document(models.Model):
    documentId = models.AutoField(primary_key=True)
    documentNumber = models.CharField(max_length=100, default='')
    writeEmp = models.ForeignKey(Employee, on_delete=models.PROTECT)
    formId = models.ForeignKey(Docuform, on_delete=models.SET_NULL, null=True, blank=True)
    preservationYear = models.IntegerField(default=9999)
    securityLevel = models.CharField(max_length=1, default='S')
    title = models.CharField(max_length=200)
    contentHtml = models.TextField()
    writeDatetime = models.DateTimeField()
    modifyDatetime = models.DateTimeField()
    draftDatetime = models.DateTimeField(null=True, blank=True)
    approveDatetime = models.DateTimeField(null=True, blank=True)
    documentStatus = models.CharField(max_length=10, default='임시')


class Approvalcategory(models.Model):
    categoryId = models.AutoField(primary_key=True)
    approvalCategory = models.CharField(max_length=10)


class Approval(models.Model):
    approvalId = models.AutoField(primary_key=True)
    documentId = models.ForeignKey(Document, on_delete=models.CASCADE)
    approvalEmp = models.ForeignKey(Employee, on_delete=models.PROTECT)
    approvalStep = models.IntegerField(default=0)
    approvalCategory = models.ForeignKey(Approvalcategory, on_delete=models.PROTECT)
    approvalStatus = models.CharField(max_length=10, default='대기')
    comment = models.CharField(max_length=200, default='')
    approvalDatetime = models.DateTimeField(null=True, blank=True)


class Documentfile(models.Model):
    fileId = models.AutoField(primary_key=True)
    file = models.FileField(upload_to="document/%Y_%m")
    fileName = models.CharField(max_length=200)
    fileSize = models.IntegerField()
