from django.contrib import admin
from .models import Servicereport, Serviceform, Vacation


@admin.register(Servicereport)
class ServicereportAdmin(admin.ModelAdmin):
    list_display = ('serviceDate', 'empDeptName', 'empName', 'companyName', 'serviceType', 'serviceTitle', 'serviceOverHour')
    list_filter = ('empDeptName', 'empName', 'companyName', )
    list_display_links = ['serviceDate', 'empName', 'companyName']


@admin.register(Serviceform)
class ServiceformAdmin(admin.ModelAdmin):
    list_display = ('empId', 'companyName', 'serviceType', 'serviceTitle')
    list_filter = ('empId',)
    list_display_links = ['empId']


@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ('empId', 'empDeptName', 'empName', 'vacationDate', 'vacationType')
    list_filter = ('empId',)
    list_display_links = ['empId']
