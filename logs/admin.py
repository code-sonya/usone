from django.contrib import admin
from .models import DownloadLog, OrderLog, ApprovalLog


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ('downloadLogId', 'empId', 'contractId', 'downloadDatetime', 'downloadUrl')
    list_filter = ('empId', 'contractId')
    list_display_links = ['downloadLogId', 'empId', 'contractId', 'downloadDatetime', 'downloadUrl']

@admin.register(OrderLog)
class OrderLogAdmin(admin.ModelAdmin):
    list_display = ('orderLogId', 'empId', 'toEmail', 'contractId', 'orderDatetime', 'orderUrl')
    list_filter = ('empId', 'toEmail', 'contractId')
    list_display_links = ['orderLogId', 'empId', 'toEmail', 'contractId', 'orderDatetime', 'orderUrl']


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ('approvalLogId', 'empId', 'toEmail', 'contractId', 'approvalDatetime', 'approvalUrl')
    list_filter = ('empId', 'toEmail', 'contractId')
    list_display_links = ['approvalLogId', 'empId', 'toEmail', 'contractId', 'approvalDatetime', 'approvalUrl']
