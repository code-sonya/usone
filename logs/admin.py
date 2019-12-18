from django.contrib import admin
from .models import DownloadLog, OrderLog, ApprovalLog


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ('downloadLogId', 'empId', 'contractId', 'downloadDatetime', 'downloadType', 'downloadName')
    list_filter = ('empId', 'contractId', 'downloadType')
    list_display_links = ['downloadLogId', 'empId', 'contractId', 'downloadDatetime', 'downloadType', 'downloadName']

@admin.register(OrderLog)
class OrderLogAdmin(admin.ModelAdmin):
    list_display = ('orderLogId', 'empId', 'toEmail', 'contractId', 'orderDatetime', 'orderUrl')
    list_filter = ('empId', 'toEmail', 'contractId')
    list_display_links = ['orderLogId', 'empId', 'toEmail', 'contractId', 'orderDatetime', 'orderUrl']


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ('approvalLogId', 'empId', 'toEmail', 'documentId', 'approvalDatetime', 'approvalStatus')
    list_filter = ('empId', 'toEmail', 'documentId', 'approvalStatus')
    list_display_links = ['approvalLogId', 'empId', 'toEmail', 'documentId', 'approvalDatetime', 'approvalStatus']
