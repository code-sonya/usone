from django.contrib import admin
from .models import Contract, Revenue, Category, Contractitem, Goal, Purchase


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contractName', 'empName', 'saleCompanyName', 'endCompanyName', 'contractStep')
    list_filter = ('saleCompanyName', 'endCompanyName')
    list_display_links = ['contractName', 'empName', 'saleCompanyName', 'endCompanyName', 'contractStep']


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ('contractId', 'revenueCompany', 'revenuePrice', 'billingDate', 'billingTime', 'predictBillingDate', 'revenueProfitRatio')
    list_filter = ('contractId', 'revenueCompany', 'revenuePrice', 'billingDate', 'billingTime', 'predictBillingDate', 'revenueProfitRatio')
    list_display_links = ['contractId', 'revenueCompany', 'revenuePrice', 'billingDate', 'billingTime', 'predictBillingDate', 'revenueProfitRatio']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchaseId', 'purchaseCompany', 'purchasePrice', 'purchaseDate')
    list_filter = ('purchaseId', 'purchaseCompany', 'purchasePrice', 'purchaseDate')
    list_display_links = ['purchaseId', 'purchaseCompany', 'purchasePrice', 'purchaseDate']


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
    list_display = ('year', 'empDeptName', 'empName', 'yearSalesSum' ,'yearProfitSum')
    list_filter = ('year', 'empDeptName', 'empName')
    list_display_links = ['year', 'empDeptName', 'empName', 'yearSalesSum', 'yearProfitSum']
