from django.contrib import admin
from .models import Center, CenterManager, CenterManagerEmp


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('centerId', 'centerName', 'centerStatus')
    list_filter = ('centerId', 'centerName', 'centerStatus')
    list_display_links = ['centerId', 'centerName', 'centerStatus']


@admin.register(CenterManager)
class CenterManagerAdmin(admin.ModelAdmin):
    list_display = ('centerManagerId', 'writeEmp', 'createdDatetime', 'startDate', 'endDate', 'centerManagerStatus')
    list_filter = ('writeEmp', 'centerManagerStatus')
    list_display_links = ['centerManagerId', 'writeEmp', 'createdDatetime', 'startDate', 'endDate', 'centerManagerStatus']


@admin.register(CenterManagerEmp)
class CenterManagerEmpAdmin(admin.ModelAdmin):
    list_display = ('managerId', 'empId', 'manageArea', 'additionalArea', 'cleanupArea')
    list_filter = ('empId', 'manageArea')
    list_display_links = ['managerId', 'empId', 'manageArea', 'additionalArea', 'cleanupArea']