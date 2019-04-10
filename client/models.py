# -*- coding: utf-8 -*-
from django.db import models
from hr.models import Employee


class Company(models.Model):
    statusChoices = (('Y', 'Y'), ('N', 'N'),('X', 'X'))

    companyName = models.CharField(max_length=100, primary_key=True)
    saleEmpId = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='saleEmpID')
    solutionMainEmpId = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True,
                                          related_name='solutionMainEmpID')
    solutionSubEmpId = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True,
                                         related_name='solutionSubEmpId')
    dbMainEmpId = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='dbMainEmpId')
    dbSubEmpId = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='dbSubEmpId')
    companyAddress = models.CharField(max_length=200)
    companyLatitude = models.FloatField(null=True, blank=True)
    companyLongitude = models.FloatField(null=True, blank=True)
    companyDbms = models.TextField(null=True, blank=True)
    companySystem = models.TextField(null=True, blank=True)
    dbComment = models.TextField(null=True, blank=True)
    solutionComment = models.TextField(null=True, blank=True)
    dbContractStartDate = models.DateField(null=True, blank=True)
    dbContractEndDate = models.DateField(null=True, blank=True)
    solutionContractStartDate = models.DateField(null=True, blank=True)
    solutionContractEndDate = models.DateField(null=True, blank=True)
    companyStatus = models.CharField(max_length=1, choices=statusChoices, default='Y')

    def __str__(self):
        return self.companyName


class Customer(models.Model):
    statusChoices = (('Y', 'Y'), ('N', 'N'))

    customerId = models.AutoField(primary_key=True)
    customerName = models.CharField(max_length=10)
    companyName = models.ForeignKey(Company, on_delete=models.CASCADE)
    customerDeptName = models.CharField(max_length=30, null=True, blank=True)
    customerPhone = models.CharField(max_length=20, null=True, blank=True)
    customerEmail = models.EmailField(max_length=254)
    customerStatus = models.CharField(max_length=1, choices=statusChoices, default='Y')

    class Meta:
        unique_together = (('customerName', 'companyName'),)

    def __str__(self):
        return 'Customer : {}'.format(self.customerName)
