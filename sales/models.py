# -*- coding: utf-8 -*-
from django.db import models
from hr.models import Employee
from client.models import Company, Customer


class Contract(models.Model):
    saleTypeChoices = (('직판', '직판'), ('T1', 'T1'), ('T2', 'T2'), ('기타', '기타'))
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
    endCompanyName = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='endCompanyName', null=True, blank=True)
    comment = models.CharField(max_length=200, null=True, blank=True)
    saleType = models.CharField(max_length=10, choices=saleTypeChoices, default='직판')
    saleIndustry = models.CharField(max_length=10, choices=saleIndustryChoices, default='금융')
    mainCategory = models.CharField(max_length=50)
    subCategory = models.CharField(max_length=50)
    salePrice = models.BigIntegerField()
    profitPrice = models.BigIntegerField()
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
    revenueCompany = models.ForeignKey(Company, on_delete=models.CASCADE)
    revenuePrice = models.BigIntegerField()
    revenueProfitPrice = models.BigIntegerField()
    revenueProfitRatio = models.FloatField()
    predictBillingDate = models.DateField(null=True, blank=True)
    billingDate = models.DateField(null=True, blank=True)
    predictDepositDate = models.DateField(null=True, blank=True)
    depositDate = models.DateField(null=True, blank=True)
    billingTime = models.CharField(max_length=10, null=True, blank=True)
    comment = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return '{} {}'.format(self.billingTime, self.contractId.contractName)


class Purchase(models.Model):
    purchaseId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.CASCADE)
    purchaseCompany = models.ForeignKey(Company, on_delete=models.CASCADE)
    purchasePrice = models.BigIntegerField()
    predictBillingDate = models.DateField(null=True, blank=True)
    billingDate = models.DateField(null=True, blank=True)
    predictWithdrawDate = models.DateField(null=True, blank=True)
    withdrawDate = models.DateField(null=True, blank=True)
    billingTime = models.CharField(max_length=10, null=True, blank=True)
    comment = models.CharField(max_length=200, null=True, blank=True)


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
    itemPrice = models.BigIntegerField()

    def __str__(self):
        return '{} : {}'.format(self.contractId.contractName, self.itemName)


class Goal(models.Model):
    goalId = models.AutoField(primary_key=True)
    empDeptName = models.CharField(max_length=30)
    empName = models.CharField(max_length=30)
    year = models.BigIntegerField()
    sales1 = models.BigIntegerField()
    sales2 = models.BigIntegerField()
    sales3 = models.BigIntegerField()
    sales4 = models.BigIntegerField()
    sales5 = models.BigIntegerField()
    sales6 = models.BigIntegerField()
    sales7 = models.BigIntegerField()
    sales8 = models.BigIntegerField()
    sales9 = models.BigIntegerField()
    sales10 = models.BigIntegerField()
    sales11 = models.BigIntegerField()
    sales12 = models.BigIntegerField()
    salesq1 = models.BigIntegerField()
    salesq2 = models.BigIntegerField()
    salesq3 = models.BigIntegerField()
    salesq4 = models.BigIntegerField()
    profit1 = models.BigIntegerField()
    profit2 = models.BigIntegerField()
    profit3 = models.BigIntegerField()
    profit4 = models.BigIntegerField()
    profit5 = models.BigIntegerField()
    profit6 = models.BigIntegerField()
    profit7 = models.BigIntegerField()
    profit8 = models.BigIntegerField()
    profit9 = models.BigIntegerField()
    profit10 = models.BigIntegerField()
    profit11 = models.BigIntegerField()
    profit12 = models.BigIntegerField()
    profitq1 = models.BigIntegerField()
    profitq2 = models.BigIntegerField()
    profitq3 = models.BigIntegerField()
    profitq4 = models.BigIntegerField()
    yearSalesSum = models.BigIntegerField()
    yearProfitSum = models.BigIntegerField()

    def __str__(self):
        return '{}년 {} 목표'.format(self.year, self.empName)
