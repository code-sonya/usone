from django.contrib import admin
from .models import Documentcategory, Documentform, Document, Approvalcategory, Approval, Documentfile, Approvalform


@admin.register(Documentcategory)
class DocumentcategoryAdmin(admin.ModelAdmin):
    list_display = ('categoryId', 'firstCategory', 'secondCategory', 'thirdCategory')
    list_filter = ('categoryId', 'firstCategory', 'secondCategory', 'thirdCategory')
    list_display_links = ['categoryId', 'firstCategory', 'secondCategory', 'thirdCategory']


@admin.register(Documentform)
class DocumentformAdmin(admin.ModelAdmin):
    list_display = ('formId', 'categoryId', 'formNumber', 'formHtml', 'comment')
    list_filter = ('formId', 'categoryId', 'formNumber', 'formHtml', 'comment')
    list_display_links = ['formId', 'categoryId', 'formNumber', 'formHtml', 'comment']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('documentNumber', 'writeEmp', 'title', 'contentHtml', 'documentStatus')
    list_filter = ('documentNumber', 'writeEmp', 'title', 'contentHtml', 'documentStatus')
    list_display_links = ['documentNumber', 'writeEmp', 'title', 'contentHtml', 'documentStatus']


@admin.register(Approvalcategory)
class ApprovalcategoryAdmin(admin.ModelAdmin):
    list_display = ('categoryId', 'approvalCategory')
    list_filter = ('categoryId', 'approvalCategory')
    list_display_links = ['categoryId', 'approvalCategory']


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('documentId', 'approvalEmp', 'approvalStatus', 'comment')
    list_filter = ('documentId', 'approvalEmp', 'approvalStatus', 'comment')
    list_display_links = ['documentId', 'approvalEmp', 'approvalStatus', 'comment']


@admin.register(Documentfile)
class DocumentfileAdmin(admin.ModelAdmin):
    list_display = ('fileId', 'fileName', 'fileSize')
    list_filter = ('fileId', 'fileName', 'fileSize')
    list_display_links = ['fileId', 'fileName', 'fileSize']\


@admin.register(Approvalform)
class ApprovalformAdmin(admin.ModelAdmin):
    list_display = ('approvalId', 'formId', 'approvalEmp', 'approvalStep', 'approvalCategory')
    list_filter = ('approvalId', 'formId', 'approvalEmp', 'approvalStep', 'approvalCategory')
    list_display_links = ['approvalId', 'formId', 'approvalEmp', 'approvalStep', 'approvalCategory']
