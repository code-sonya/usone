from django.contrib import admin
from .models import Contract, Revenue


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contractName', 'empName', 'saleCompanyName', 'endCompanyName', 'contractStep')
    list_filter = ('saleCompanyName', 'endCompanyName')
    list_display_links = ['contractName', 'empName', 'saleCompanyName', 'endCompanyName', 'contractStep']


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ('revenueName', 'billingDate', 'collectDate', 'revenueStep')
    list_filter = ('revenueName', 'billingDate', 'collectDate')
    list_display_links = ['revenueName', 'billingDate', 'collectDate', 'revenueStep']
