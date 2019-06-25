from django.contrib import admin
from .models import Company, Customer


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('companyName', 'companyNameKo', 'companyAddress', 'companyStatus')
    list_filter = ('companyStatus',)
    list_display_links = ['companyName', 'companyNameKo', 'companyAddress', 'companyStatus']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customerName', 'companyName', 'customerEmail')
    list_filter = ('companyName',)
    list_display_links = ['customerName']
