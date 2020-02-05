from django.contrib import admin
from .models import Center, CenterManager, CenterManagerEmp, CheckList, ConfirmCheckList


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


@admin.register(CheckList)
class CheckListAdmin(admin.ModelAdmin):
    list_display = ('checkListId', 'checkListName', 'checkListStatus')
    list_filter = ('checkListName', 'checkListStatus')
    list_display_links = ['checkListId', 'checkListName', 'checkListStatus']


@admin.register(ConfirmCheckList)
class ConfirmCheckListAdmin(admin.ModelAdmin):
    list_display = ('confirmId', 'empId', 'confirmDate', 'checkListId', 'checkListStatus', 'comment', 'centerId')
    list_filter = ('checkListId', 'checkListStatus')
    list_display_links = ['confirmId', 'confirmDate', 'checkListId', 'checkListStatus', 'comment']