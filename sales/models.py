# -*- coding: utf-8 -*-
from django.db import models
from hr.models import Employee
from client.models import Company, Customer


class Contract(models.Model):
    saleTypeChoices = (('직판', '직판'), ('T1', 'T1'), ('T2', 'T2'))
    saleIndustryChoices = (('금융', '금융'), ('공공', '공공'), ('제조', '제조'), ('통신', '통신'), ('기타', '기타'))
    contractStepChoices = (('Opportunity', 'Opportunity'), ('Firm', 'Firm'), ('Drop', 'Drop'))

    contractId = models.AutoField(primary_key=True)
    contractName = models.CharField(max_length=200)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    empName = models.CharField(max_length=10)
    empDeptName = models.CharField(max_length=30)
    saleCompanyName = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='saleCompanyName')
    saleCustomerId = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='saleCustomerId', null=True, blank=True)
    saleCustomerName = models.CharField(max_length=10, null=True, blank=True)
    endCompanyName = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='endCompanyName')
    endCustomerId = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='endCustomerId', null=True, blank=True)
    endCustomerName = models.CharField(max_length=10, null=True, blank=True)
    category = models.TextField(null=True, blank=True)
    saleType = models.CharField(max_length=10, choices=saleTypeChoices, default='직판')
    saleIndustry = models.CharField(max_length=10, choices=saleIndustryChoices, default='금융')
    predictSalePrice = models.IntegerField()
    predictProfitPrice = models.IntegerField()
    predictProfitRatio = models.FloatField()
    predictContractDate = models.DateField()
    salePrice = models.IntegerField(null=True, blank=True)
    profitPrice = models.IntegerField(null=True, blank=True)
    profitRatio = models.FloatField(null=True, blank=True)
    contractDate = models.DateField(null=True, blank=True)
    contractStep = models.CharField(max_length=20, choices=contractStepChoices, default='Opportunity')
    contractStartDate = models.DateField(null=True, blank=True)
    contractEndDate = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.contractName


class Revenue(models.Model):
    revenueStepChoices = (('Complete', 'Complete'), ('분납', '분납'), ('수금완료', '수금완료'))

    revenueId = models.AutoField(primary_key=True)
    revenueName = models.CharField(max_length=200)
    contractId = models.ForeignKey(Contract, on_delete=models.CASCADE)
    salePrice = models.IntegerField()
    billingDate = models.DateField()
    predictCollectDate = models.DateField()
    collectPrice = models.IntegerField()
    collectDate = models.DateField()
    revenueStep = models.CharField(max_length=20, choices=revenueStepChoices, default='Opportunity')

    def __str__(self):
        return self.revenueName
