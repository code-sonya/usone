# -*- coding: utf-8 -*-
from django.db import models
from hr.models import Employee


class Company(models.Model):
    statusChoices = (('Y', 'Y'), ('N', 'N'), ('X', 'X'))
    typeChoices = (
        ('발주처', '발주처'),
        ('외주업체', '외주업체'),
        ('기타', '기타'),
    )

    companyName = models.CharField(max_length=100, primary_key=True)
    companyNameKo = models.CharField(max_length=100, null=True, blank=True)
    companyNumber = models.CharField(max_length=30, null=True, blank=True)
    ceo = models.CharField(max_length=30, null=True, blank=True)
    companyAddress = models.CharField(max_length=200, null=True, blank=True)
    companyPhone = models.CharField(max_length=20, null=True, blank=True)
    companyComment = models.CharField(max_length=200, null=True, blank=True)
    companyType = models.CharField(max_length=100, choices=typeChoices, default='기타')
    companyStatus = models.CharField(max_length=1, choices=statusChoices, default='Y')

    def __str__(self):
        return self.companyName


class Customer(models.Model):
    statusChoices = (('Y', 'Y'), ('N', 'N'))
    typeChoices = (('실무', '실무'), ('영업', '영업'), ('세금', '세금'))

    customerId = models.AutoField(primary_key=True)
    customerName = models.CharField(max_length=10)
    companyName = models.ForeignKey(Company, on_delete=models.CASCADE)
    customerDeptName = models.CharField(max_length=30, null=True, blank=True)
    customerPhone = models.CharField(max_length=20, null=True, blank=True)
    customerEmail = models.CharField(max_length=254, null=True, blank=True)
    customerType = models.CharField(max_length=10, choices=typeChoices, null=True, blank=True)
    customerStatus = models.CharField(max_length=1, choices=statusChoices, default='Y')

    class Meta:
        unique_together = (('customerName', 'companyName'),)

    def __str__(self):
        return self.customerName + '(' + self.companyName.companyName + ')'
