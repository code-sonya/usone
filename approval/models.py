# -*- coding: utf-8 -*-
from datetime import datetime

from django.db import models
from hr.models import Employee
from service.models import Servicereport
from sales.models import Contract


class Documentcategory(models.Model):
    categoryId = models.AutoField(primary_key=True)
    firstCategory = models.CharField(max_length=20, default='공통')
    secondCategory = models.CharField(max_length=20, default='공통')
    thirdCategory = models.CharField(max_length=20, default='공통')


class Documentform(models.Model):
    approvalFormatChoices = (
        ('신청', '신청'),
        ('결재', '결재'),
    )
    formId = models.AutoField(primary_key=True)
    categoryId = models.ForeignKey(Documentcategory, on_delete=models.SET_NULL, null=True, blank=True)
    formNumber = models.IntegerField(default=0)
    preservationYear = models.IntegerField(default=9999)
    securityLevel = models.CharField(max_length=1, default='S')
    approvalFormat = models.CharField(max_length=10, choices=approvalFormatChoices, default='신청')
    formTitle = models.CharField(max_length=200)
    formHtml = models.TextField()
    comment = models.CharField(max_length=200, default='')
    copyAuth = models.CharField(max_length=10, default='Y')
    mailAuth = models.CharField(max_length=10, default='Y')


class Document(models.Model):
    documentId = models.AutoField(primary_key=True)
    documentNumber = models.CharField(max_length=100, default='')
    writeEmp = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='documentWriteEmp')
    formId = models.ForeignKey(Documentform, on_delete=models.SET_NULL, null=True, blank=True)
    preservationYear = models.IntegerField(default=9999)
    securityLevel = models.CharField(max_length=1, default='S')
    title = models.CharField(max_length=200)
    contentHtml = models.TextField()
    writeDatetime = models.DateTimeField()
    modifyDatetime = models.DateTimeField()
    draftDatetime = models.DateTimeField(null=True, blank=True)
    approveDatetime = models.DateTimeField(null=True, blank=True)
    documentStatus = models.CharField(max_length=10, default='임시')
    serviceId = models.ForeignKey(Servicereport, on_delete=models.SET_NULL, null=True, blank=True)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)

    def preservationDate(self):
        if self.preservationYear == 9999:
            return datetime(9999, 12, 31)
        else:
            return datetime(
                self.preservationYear + self.writeDatetime.year,
                self.writeDatetime.month,
                self.writeDatetime.day
            )


class Documentfile(models.Model):
    fileId = models.AutoField(primary_key=True)
    documentId = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to="document/%Y_%m")
    fileName = models.CharField(max_length=200)
    fileSize = models.FloatField()


class Relateddocument(models.Model):
    relatedId = models.AutoField(primary_key=True)
    documentId = models.ForeignKey(Document, on_delete=models.PROTECT, related_name='documentId2')
    relatedDocumentId = models.ForeignKey(Document, on_delete=models.PROTECT, related_name='relatedDocumentId')


class Approvalcategory(models.Model):
    categoryId = models.AutoField(primary_key=True)
    approvalCategory = models.CharField(max_length=10)


class Approval(models.Model):
    approvalCategoryChoices = (
        ('신청', '신청'),
        ('승인', '승인'),
        ('참조', '참조'),
        ('결재', '결재'),
        ('합의', '합의'),
        ('재무합의', '재무합의'),
    )
    approvalId = models.AutoField(primary_key=True)
    documentId = models.ForeignKey(Document, on_delete=models.CASCADE)
    approvalEmp = models.ForeignKey(Employee, on_delete=models.PROTECT)
    approvalStep = models.IntegerField(default=0)
    approvalCategory = models.CharField(max_length=20, choices=approvalCategoryChoices, default='신청')
    approvalStatus = models.CharField(max_length=10, default='대기')
    comment = models.CharField(max_length=200, default='')
    approvalDatetime = models.DateTimeField(null=True, blank=True)


class Approvalform(models.Model):
    approvalId = models.AutoField(primary_key=True)
    formId = models.ForeignKey(Documentform, on_delete=models.CASCADE)
    approvalEmp = models.ForeignKey(Employee, on_delete=models.PROTECT)
    approvalStep = models.IntegerField(default=0)
    approvalCategory = models.CharField(max_length=10, default='처리')


class Documentcomment(models.Model):
    commentId = models.AutoField(primary_key=True)
    documentId = models.ForeignKey(Document, on_delete=models.CASCADE)
    author = models.ForeignKey(Employee, on_delete=models.PROTECT)
    comment = models.CharField(max_length=255)
    created = models.DateTimeField()
    updated = models.DateTimeField()
