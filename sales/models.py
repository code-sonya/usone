# -*- coding: utf-8 -*-
from django.db import models
from hr.models import Employee
from client.models import Company, Customer


class Contract(models.Model):
    saleTypeChoices = (('직판', '직판'), ('T1', 'T1'), ('T2', 'T2'))
    saleIndustryChoices = (('금융', '금융'), ('공공', '공공'), ('제조', '제조'), ('통신', '통신'), ('기타', '기타'))
    contractStepChoices = (('Opportunity', 'Opportunity'), ('Firm', 'Firm'), ('Drop', 'Drop'))

    contractId = models.AutoField(primary_key=True)
    contractCode = models.CharField(max_length=30)
    contractName = models.CharField(max_length=200)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    empName = models.CharField(max_length=10)
    empDeptName = models.CharField(max_length=30)
    saleCompanyName = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='saleCompanyName')
    saleCustomerId = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='saleCustomerId', null=True, blank=True)
    saleCustomerName = models.CharField(max_length=10, null=True, blank=True)
    endCompanyName = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='endCompanyName')
    comment = models.CharField(max_length=200, null=True, blank=True)
    saleType = models.CharField(max_length=10, choices=saleTypeChoices, default='직판')
    saleIndustry = models.CharField(max_length=10, choices=saleIndustryChoices, default='금융')
    salePrice = models.IntegerField()
    profitPrice = models.IntegerField()
    profitRatio = models.FloatField()
    contractDate = models.DateField()
    contractStep = models.CharField(max_length=20, choices=contractStepChoices, default='Opportunity')
    contractStartDate = models.DateField(null=True, blank=True)
    contractEndDate = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.contractName


class Revenue(models.Model):
    revenueId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.CASCADE)
    revenuePrice = models.IntegerField()
    revenueProfitPrice = models.IntegerField()
    billingDate = models.DateField(null=True, blank=True)
    comment = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.contractId.contractName


class Category(models.Model):
    categoryId = models.AutoField(primary_key=True)
    mainCategory = models.CharField(max_length=50)
    subCategory = models.CharField(max_length=50)

    def __str__(self):
        return '{} {}'.format(self.mainCategory, self.subCategory)


class Contractitem(models.Model):
    contractItemId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.CASCADE)
    mainCategory = models.CharField(max_length=50)
    subCategory = models.CharField(max_length=50)
    itemName = models.CharField(max_length=50)
    itemPrice = models.IntegerField()

    def __str__(self):
        return '{} : {}'.format(self.contractId.contractName, self.itemName)


class Goal(models.Model):
    goalId = models.AutoField(primary_key=True)
    empDeptName = models.CharField(max_length=30)
    empName = models.CharField(max_length=30)
    year = models.IntegerField()
    jan = models.IntegerField()
    feb = models.IntegerField()
    mar = models.IntegerField()
    apr = models.IntegerField()
    may = models.IntegerField()
    jun = models.IntegerField()
    jul = models.IntegerField()
    aug = models.IntegerField()
    sep = models.IntegerField()
    oct = models.IntegerField()
    nov = models.IntegerField()
    dec = models.IntegerField()
    q1 = models.IntegerField()
    q2 = models.IntegerField()
    q3 = models.IntegerField()
    q4 = models.IntegerField()
    yearSum = models.IntegerField()

    def __str__(self):
        return '{}년 {} 목표'.format(self.year, self.name)
