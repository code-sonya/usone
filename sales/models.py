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
    sales1 = models.IntegerField()
    sales2 = models.IntegerField()
    sales3 = models.IntegerField()
    sales4 = models.IntegerField()
    sales5 = models.IntegerField()
    sales6 = models.IntegerField()
    sales7 = models.IntegerField()
    sales8 = models.IntegerField()
    sales9 = models.IntegerField()
    sales10 = models.IntegerField()
    sales11 = models.IntegerField()
    sales12 = models.IntegerField()
    salesq1 = models.IntegerField()
    salesq2 = models.IntegerField()
    salesq3 = models.IntegerField()
    salesq4 = models.IntegerField()
    profit1 = models.IntegerField()
    profit2 = models.IntegerField()
    profit3 = models.IntegerField()
    profit4 = models.IntegerField()
    profit5 = models.IntegerField()
    profit6 = models.IntegerField()
    profit7 = models.IntegerField()
    profit8 = models.IntegerField()
    profit9 = models.IntegerField()
    profit10 = models.IntegerField()
    profit11 = models.IntegerField()
    profit12 = models.IntegerField()
    profitq1 = models.IntegerField()
    profitq2 = models.IntegerField()
    profitq3 = models.IntegerField()
    profitq4 = models.IntegerField()
    yearSalesSum = models.IntegerField()
    yearProfitSum = models.IntegerField()

    def __str__(self):
        return '{}년 {} 목표'.format(self.year, self.empName)
