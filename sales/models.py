# -*- coding: utf-8 -*-
from django.db import models
from django_mysql.models import Model, JSONField
from hr.models import Employee
from client.models import Company, Customer


class Contract(Model):
    saleTypeChoices = (('직판', '직판'), ('T1', 'T1'), ('T2', 'T2'))
    saleIndustryChoices = (('금융', '금융'), ('공공', '공공'), ('제조', '제조'), ('통신', '통신'), ('기타', '기타'))
    contractStepChoices = (('Opportunity', 'Opportunity'), ('Firm', 'Firm'), ('Drop', 'Drop'))

    contractId = models.AutoField(primary_key=True)
    contractName = models.CharField(max_length=200)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    empName = models.CharField(max_length=10)
    empDeptName = models.CharField(max_length=30)
    saleCompanyName = models.ForeignKey(Company, on_delete=models.CASCADE)
    saleCustomerId = models.ForeignKey(Customer, on_delete=models.CASCADE)
    saleCustomerName = models.CharField(max_length=10)
    endCompanyName = models.ForeignKey(Company, on_delete=models.CASCADE)
    endCustomerId = models.ForeignKey(Customer, on_delete=models.CASCADE)
    endCustomerName = models.CharField(max_length=10)
    category = JSONField(null=True, blank=True)
    saleType = models.CharField(max_length=10, choices=saleTypeChoices, default='직판')
    saleIndustry = models.CharField(max_length=10, choices=saleIndustryChoices, default='금융')
    predictSalePrice = models.IntegerField()
    predictProfitPrice = models.IntegerField()
    predictProfitRatio = models.FloatField()
    predictContractDate = models.DateField()
    salePrice = models.IntegerField()
    profitPrice = models.IntegerField()
    profitRatio = models.FloatField()
    contractDate = models.DateField()
    contractStep = models.CharField(max_length=20, choices=contractStepChoices, default='Opportunity')
    contractStartDate = models.DateField()
    contractEndDate = models.DateField()

    def __str__(self):
        return self.contractName


class Revenue(models.Model):
    revenueStepChoices = (('Complete', 'Complete'), ('수금완료', '수금완료'))
    revenueId = models.AutoField(primary_key=True)
    revenueName = contractName = models.CharField(max_length=200)
    contractId = models.ForeignKey(Contract, on_delete=models.CASCADE)
    salePrice = models.IntegerField()
    billingDate = models.DateField()
    collectDate = models.DateField()
    revenueStep = models.CharField(max_length=20, choices=revenueStepChoices, default='Opportunity')

    def __str__(self):
        return self.revenueName
