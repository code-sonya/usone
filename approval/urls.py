from django.conf.urls import url
from . import views

app_name = 'approval'

urlpatterns = [
    url(r'^postdocument/$', views.post_document, name='postdocumnet'),
    url(r'^postdocumentform/$', views.post_documentform, name='postdocumnetform'),
    url(r'^documentcategoryasjson/$', views.documentcategory_asjson, name='documentcategoryasjson'),
    url(r'^documentformasjson/$', views.documentform_asjson, name='documentformasjson'),
    url(r'^showdocumentasjson/$', views.showdocument_asjson, name='showdocumentasjson'),
    url(r'^showdocumentformasjson/$', views.showdocumentform_asjson, name='showdocumentformasjson'),
    url(r'^postdocumentcategory/$', views.post_documentcategory, name='postdocumentcategory'),
    url(r'^showdocumentform/$', views.show_documentform, name='showdocumentform'),
    url(r'^modifydocumentform/(?P<formId>.+)/$', views.modify_documentform, name='modifydocumentform'),
    url(r'^showdocument/end/all/$', views.show_document_end_all, name='showdocumentendall'),
    url(r'^showdocument/end/write/$', views.show_document_end_write, name='showdocumentendwrite'),
    url(r'^showdocument/ing/all/$', views.show_document_ing_all, name='showdocumentingall'),
    url(r'^showdocument/ing/write/$', views.show_document_ing_write, name='showdocumentingwrite'),
    url(r'^viewdocument/(?P<documentId>.+)/$', views.view_document, name='viewdocument'),
    url(r'^approvedocument/(?P<approvalId>.+)/$', views.approve_document, name='approvedocument'),
    url(r'^returndocument/(?P<approvalId>.+)/$', views.return_document, name='returndocument'),
]
