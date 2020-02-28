from django.contrib import admin
from .models import Documentcategory, Documentform, Document, Approval, Documentfile, Approvalform, Relateddocument, Documentcomment


@admin.register(Documentcategory)
class DocumentcategoryAdmin(admin.ModelAdmin):
    list_display = ('categoryId', 'firstCategory', 'secondCategory', 'thirdCategory')
    list_filter = ('categoryId', 'firstCategory', 'secondCategory', 'thirdCategory')
    list_display_links = ['categoryId', 'firstCategory', 'secondCategory', 'thirdCategory']


@admin.register(Documentform)
class DocumentformAdmin(admin.ModelAdmin):
    list_display = ('formId', 'categoryId', 'formNumber', 'approvalFormat', 'comment')
    list_filter = ('formId', 'categoryId', 'formNumber', 'approvalFormat', 'comment')
    list_display_links = ['formId', 'categoryId', 'formNumber', 'approvalFormat', 'comment']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('documentNumber', 'writeEmp', 'title', 'documentStatus')
    list_filter = ('documentNumber', 'writeEmp', 'title', 'documentStatus')
    list_display_links = ['documentNumber', 'writeEmp', 'title', 'documentStatus']


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('documentId', 'approvalEmp', 'approvalStatus', 'comment')
    list_filter = ('documentId', 'approvalEmp', 'approvalStatus', 'comment')
    list_display_links = ['documentId', 'approvalEmp', 'approvalStatus', 'comment']


@admin.register(Documentfile)
class DocumentfileAdmin(admin.ModelAdmin):
    list_display = ('fileId', 'fileName', 'fileSize')
    list_filter = ('fileId', 'fileName', 'fileSize')
    list_display_links = ['fileId', 'fileName', 'fileSize']


@admin.register(Approvalform)
class ApprovalformAdmin(admin.ModelAdmin):
    list_display = ('approvalId', 'formId', 'approvalEmp', 'approvalStep', 'approvalCategory')
    list_filter = ('approvalId', 'formId', 'approvalEmp', 'approvalStep', 'approvalCategory')
    list_display_links = ['approvalId', 'formId', 'approvalEmp', 'approvalStep', 'approvalCategory']


@admin.register(Relateddocument)
class RelateddocumentAdmin(admin.ModelAdmin):
    list_display = ('relatedId', 'documentId', 'relatedDocumentId')
    list_filter = ('relatedId', 'documentId', 'relatedDocumentId')
    list_display_links = ['relatedId', 'documentId', 'relatedDocumentId']


@admin.register(Documentcomment)
class DocumentcommentAdmin(admin.ModelAdmin):
    list_display = ('commentId', 'documentId', 'author', 'comment', 'updated')
    list_filter = ('documentId', 'author')
    list_display_links = ['commentId', 'documentId', 'author', 'comment', 'updated']
