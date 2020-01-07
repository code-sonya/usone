from django.conf.urls import url
from . import views

app_name = 'approval'

urlpatterns = [
    url(r'^postdocument/$', views.post_document, name='postdocumnet'),
    url(r'^modifydocument/(?P<documentId>.+)/$', views.modify_document, name='modifydocument'),
    url(r'^postdocumentform/$', views.post_documentform, name='postdocumnetform'),
    url(r'^documentcategoryasjson/$', views.documentcategory_asjson, name='documentcategoryasjson'),
    url(r'^documentformasjson/$', views.documentform_asjson, name='documentformasjson'),
    url(r'^showdocumentasjson/$', views.showdocument_asjson, name='showdocumentasjson'),
    url(r'^showdocumentformasjson/$', views.showdocumentform_asjson, name='showdocumentformasjson'),
    url(r'^postdocumentcategory/$', views.post_documentcategory, name='postdocumentcategory'),
    url(r'^showdocumentform/$', views.show_documentform, name='showdocumentform'),
    url(r'^modifydocumentform/(?P<formId>.+)/$', views.modify_documentform, name='modifydocumentform'),

    # 전자결재
    url(r'^showdocument/all/$', views.show_document_all, name='showdocumentall'),
    url(r'^showdocument/ing/$', views.show_document_ing, name='showdocumenting'),
    url(r'^showdocument/done/$', views.show_document_done, name='showdocumentdone'),
    url(r'^showdocument/temp/$', views.show_document_temp, name='showdocumenttemp'),
    url(r'^showdocument/admin/ing/$', views.show_document_admin_ing, name='showdocumentadmining'),
    url(r'^showdocument/admin/done/$', views.show_document_admin_done, name='showdocumentadmindone'),
    url(r'^showdocument/admin/reject/$', views.show_document_admin_reject, name='showdocumentadminreject'),

    url(r'^viewdocument/(?P<documentId>.+)/$', views.view_document, name='viewdocument'),
    url(r'^deletedocument/(?P<documentId>.+)/$', views.delete_document, name='deletedocument'),
    url(r'^draftcancel/(?P<documentId>.+)/$', views.draft_cancel, name='draftcancel'),
    url(r'^copydocument/(?P<documentId>.+)/$', views.copy_document, name='copydocument'),
    url(r'^postdocumentcomment/$', views.post_document_comment, name='postdocumentcomment'),
    url(r'^approvedocument/(?P<approvalId>.+)/$', views.approve_document, name='approvedocument'),
    url(r'^returndocument/(?P<approvalId>.+)/$', views.return_document, name='returndocument'),
    url(r'^postcontractdocument/(?P<contractId>.+)/(?P<documentType>.+)/$', views.post_contract_document, name='postcontractdocument'),
    url(r'^viewdocumentemail/(?P<documentId>.+)/$', views.view_documentemail, name='viewdocumentemail'),
    url(r'^countingasjson/$', views.counting_asjson, name='countingasjson'),
    url(r'^deletecomment/(?P<commentId>.+)/$', views.delete_comment, name='deletecomment'),
]
