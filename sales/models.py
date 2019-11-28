# -*- coding: utf-8 -*-
from django.db import models
from hr.models import Employee
from client.models import Company, Customer


class Contract(models.Model):
    saleTypeChoices = (('직판', '직판'), ('T1', 'T1'), ('T2', 'T2'), ('기타', '기타'))
    saleIndustryChoices = (('금융', '금융'), ('공공', '공공'), ('유통 & 제조', '유통 & 제조'), ('통신 & 미디어', '통신 & 미디어'), ('기타', '기타'))
    contractStepChoices = (('Opportunity', 'Opportunity'), ('Firm', 'Firm'), ('Drop', 'Drop'))
    depositConditionChoices = (('계산서 발행 후', '계산서 발행 후'), ('당월', '당월'), ('익월', '익월'), ('당월 말', '당월 말'), ('익월 초', '익월 초'), ('익월 말', '익월 말'))
    modifyContractPaperChoices = (('N', 'N'), ('Y', 'Y'))
    newCompanyChoices = (('N', 'N'), ('Y', 'Y'))

    contractId = models.AutoField(primary_key=True)
    contractCode = models.CharField(max_length=30)
    contractName = models.CharField(max_length=200)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='saleEmpId')
    empName = models.CharField(max_length=10)
    empDeptName = models.CharField(max_length=30)
    newCompany = models.CharField(max_length=10, choices=newCompanyChoices, default='N')
    saleCompanyName = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='saleCompanyName')
    saleCustomerId = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='saleCustomerId', null=True, blank=True)
    saleCustomerName = models.CharField(max_length=10, null=True, blank=True)
    endCompanyName = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='endCompanyName', null=True, blank=True)
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
    depositCondition = models.CharField(max_length=20, choices=depositConditionChoices, default='계산서 발행 후', null=True, blank=True)
    depositConditionDay = models.IntegerField(default=0, null=True, blank=True)
    contractPaper = models.FileField(null=True, blank=True, upload_to="contractPaper/%Y_%m")
    modifyContractPaper = models.CharField(max_length=20, choices=modifyContractPaperChoices, default='N', null=True, blank=True)
    orderPaper = models.FileField(null=True, blank=True, upload_to="orderPaper/%Y_%m")
    transferContractId = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.CharField(max_length=200, null=True, blank=True)
    writeEmpId = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='writeEmpId', null=True, blank=True)
    writeDatetime = models.DateTimeField(null=True, blank=True)
    editEmpId = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='editEmpId', null=True, blank=True)
    editDatetime = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.contractName


class Revenue(models.Model):
    revenueId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.CASCADE)
    revenueCompany = models.ForeignKey(Company, on_delete=models.CASCADE)
    revenuePrice = models.BigIntegerField()
    revenueProfitPrice = models.BigIntegerField()
    revenueProfitRatio = models.FloatField()
    incentivePrice = models.BigIntegerField(default=0)
    incentiveProfitPrice = models.BigIntegerField(default=0)
    incentiveReason = models.CharField(max_length=20, default='계산서미발행')
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


class Cost(models.Model):
    costId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.CASCADE)
    costCompany = models.CharField(max_length=20)
    costPrice = models.BigIntegerField(default=0)
    billingDate = models.DateField(null=True, blank=True)
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


class Expense(models.Model):
    expenseId = models.AutoField(primary_key=True)
    expenseType = models.CharField(max_length=20, null=True, blank=True)
    expenseDept = models.CharField(max_length=20, null=True, blank=True)
    expenseMain = models.CharField(max_length=50, null=True, blank=True)
    expenseSub = models.CharField(max_length=50, null=True, blank=True)
    expenseGroup = models.CharField(max_length=50, null=True, blank=True)
    expenseMoney = models.IntegerField(default=0)
    expenseDate = models.DateField(null=True, blank=True)
    comment = models.CharField(max_length=100, null=True, blank=True)
    expenseStatus = models.CharField(max_length=1, default='Y')

    def __str__(self):
        return self.expenseDept + self.expenseMain + self.expenseSub


class Acceleration(models.Model):
    accelerationId = models.AutoField(primary_key=True)
    accelerationYear = models.IntegerField()
    accelerationQuarter = models.IntegerField(default=0)
    accelerationMin = models.IntegerField()
    accelerationMax = models.IntegerField()
    accelerationRatio = models.IntegerField()
    accelerationAcc = models.FloatField()

    def __str__(self):
        return str(self.accelerationYear) + '년' + str(self.accelerationMin) + '% ~ ' + str(self.accelerationMax) + '%'


class Incentive(models.Model):
    statusChoices = (('N', 'N'), ('Y', 'Y'))

    incentiveId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    year = models.IntegerField()
    quarter = models.IntegerField()
    salary = models.BigIntegerField()
    bettingRatio = models.IntegerField()
    basicSalary = models.BigIntegerField()
    bettingSalary = models.BigIntegerField()
    achieveIncentive = models.BigIntegerField(default=0)
    achieveAward = models.BigIntegerField(default=0)
    incentiveStatus = models.CharField(max_length=1, choices=statusChoices, default='N')

    def __str__(self):
        return str(self.empId.empName) + str(self.year) + '년 ' + str(self.quarter) + '분기 인센티브'


class Contractfile(models.Model):
    fileId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    fileCategory = models.CharField(max_length=100)
    fileName = models.CharField(max_length=200)
    fileSize = models.FloatField()
    file = models.FileField(upload_to="contract/%Y_%m")


class Purchasetypea(models.Model):
    classNumberChoices = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9))
    typeId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    companyName = models.ForeignKey(Company, on_delete=models.CASCADE)
    contents = models.CharField(max_length=200)
    price = models.IntegerField()
    classNumber = models.IntegerField(choices=classNumberChoices)

    def __str__(self):
        return '{} {}'.format(self.companyName, self.contractId)


class Purchasetypeb(models.Model):
    classNumberChoices = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9))
    classificationChoices = (('상품_HW', '상품_HW'), ('상품_SW', '상품_SW'), ('유지보수_HW', '유지보수_HW'), ('유지보수_SW', '유지보수_SW'), ('PM상주', 'PM상주'), ('기타', '기타'))
    typeId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    classification = models.CharField(max_length=20,  choices=classificationChoices)
    times = models.IntegerField(null=True, blank=True)
    sites = models.IntegerField(null=True, blank=True)
    units = models.IntegerField()
    price = models.IntegerField()
    classNumber = models.IntegerField(choices=classNumberChoices)

    def __str__(self):
        return '{} {}'.format(self.classification, self.contractId)


class Purchasetypec(models.Model):
    classNumberChoices = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9))
    classificationChoices = (('상품_HW', '상품_HW'), ('상품_SW', '상품_SW'), ('유지보수_HW', '유지보수_HW'), ('유지보수_SW', '유지보수_SW'), ('HW', 'HW'), ('SW', 'SW'), ('PM상주', 'PM상주'),
                             ('프로젝트비용', '프로젝트비용'), ('사업진행비용', '사업진행비용'), ('교육', '교육'), ('교육쿠폰', '교육쿠폰'), ('부자재매입', '부자재매입'), ('기타', '기타'))
    typeId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    classification = models.CharField(max_length=20, choices=classificationChoices)
    contents = models.CharField(max_length=200)
    price = models.IntegerField()
    classNumber = models.IntegerField(choices=classNumberChoices)

    def __str__(self):
        return '{} {}'.format(self.classification, self.contractId)


class Purchasetyped(models.Model):
    classNumberChoices = ((1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9))
    typeId = models.AutoField(primary_key=True)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    contractNo = models.CharField(max_length=50)
    contractStartDate = models.DateField()
    contractEndDate = models.DateField()
    price = models.IntegerField()
    classNumber = models.IntegerField(choices=classNumberChoices)

    def __str__(self):
        return '{} {}'.format(self.contractNo, self.contractId)