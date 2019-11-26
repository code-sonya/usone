from django.contrib import admin
from .models import Contract, Revenue, Purchase, Cost, Category, Contractitem, Goal, Expense, Acceleration, Incentive, Contractfile


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contractName', 'empName', 'saleCompanyName', 'endCompanyName', 'contractStep', 'contractCode')
    list_filter = ('saleCompanyName', 'endCompanyName', 'contractCode')
    list_display_links = ['contractName', 'empName', 'saleCompanyName', 'endCompanyName', 'contractStep', 'contractCode']


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ('revenueId', 'contractId', 'revenueCompany', 'revenuePrice', 'predictBillingDate', 'billingDate', 'predictDepositDate', 'depositDate', 'billingTime')
    list_filter = ('revenueId', 'contractId', 'revenueCompany', 'revenuePrice', 'predictBillingDate', 'billingDate', 'predictDepositDate', 'depositDate', 'billingTime')
    list_display_links = ['revenueId', 'contractId', 'revenueCompany', 'revenuePrice', 'predictBillingDate', 'billingDate', 'predictDepositDate', 'depositDate', 'billingTime']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchaseId', 'contractId', 'purchaseCompany', 'purchasePrice', 'predictBillingDate', 'billingDate', 'predictWithdrawDate', 'withdrawDate', 'billingTime')
    list_filter = ('purchaseId', 'contractId', 'purchaseCompany', 'purchasePrice', 'predictBillingDate', 'billingDate', 'predictWithdrawDate', 'withdrawDate', 'billingTime')
    list_display_links = ['purchaseId', 'contractId', 'purchaseCompany', 'purchasePrice', 'predictBillingDate', 'billingDate', 'predictWithdrawDate', 'withdrawDate', 'billingTime']


@admin.register(Cost)
class CostAdmin(admin.ModelAdmin):
    list_display = ('costId', 'contractId', 'costCompany', 'costPrice', 'billingDate', 'billingTime')
    list_filter = ('costId', 'contractId', 'costCompany', 'costPrice', 'billingDate', 'billingTime')
    list_display_links = ['costId', 'contractId', 'costCompany', 'costPrice', 'billingDate', 'billingTime']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('categoryId', 'mainCategory', 'subCategory')
    list_filter = ('mainCategory', 'subCategory')
    list_display_links = ['categoryId', 'mainCategory', 'subCategory']


@admin.register(Contractitem)
class ContractitemAdmin(admin.ModelAdmin):
    list_display = ('contractItemId', 'contractId', 'mainCategory', 'subCategory', 'itemName', 'itemPrice')
    list_filter = ('contractId', 'itemName')
    list_display_links = ['contractItemId', 'contractId', 'mainCategory', 'subCategory', 'itemName', 'itemPrice']


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('year', 'empDeptName', 'empName', 'yearSalesSum', 'yearProfitSum')
    list_filter = ('year', 'empDeptName', 'empName')
    list_display_links = ['year', 'empDeptName', 'empName', 'yearSalesSum', 'yearProfitSum']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expenseType', 'expenseDept', 'expenseMain', 'expenseSub', 'expenseMoney')
    list_filter = ('expenseType', 'expenseDept', 'expenseMain', 'expenseSub', 'expenseMoney')
    list_display_links = ['expenseType', 'expenseDept', 'expenseMain', 'expenseSub', 'expenseMoney']


@admin.register(Acceleration)
class AccelerationAdmin(admin.ModelAdmin):
    list_display = ('accelerationYear', 'accelerationQuarter', 'accelerationMin', 'accelerationMax', 'accelerationRatio', 'accelerationAcc')
    list_filter = ('accelerationYear', 'accelerationQuarter', 'accelerationMin', 'accelerationMax', 'accelerationRatio', 'accelerationAcc')
    list_display_links = ('accelerationYear', 'accelerationQuarter', 'accelerationMin', 'accelerationMax', 'accelerationRatio', 'accelerationAcc')


@admin.register(Incentive)
class IncentiveAdmin(admin.ModelAdmin):
    list_display = ('empId', 'year', 'quarter')
    list_filter = ('empId', 'year', 'quarter')
    list_display_links = ('empId', 'year', 'quarter')


@admin.register(Contractfile)
class ContractfileAdmin(admin.ModelAdmin):
    list_display = ('fileId', 'fileCategory', 'fileName', 'fileSize')
    list_filter = ('fileId', 'fileCategory', 'fileName', 'fileSize')
    list_display_links = ['fileId', 'fileCategory', 'fileName', 'fileSize']
