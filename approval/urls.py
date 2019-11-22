from django.conf.urls import url
from . import views

app_name = 'approval'

urlpatterns = [
    url(r'^postdocument/$', views.post_document, name='postdocumnet'),
    url(r'^modifydocument/(?P<documentId>.+)/$', views.modify_document, name='modifydocumnet'),
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
    url(r'^showdocument/end/approval/$', views.show_document_end_approval, name='showdocumentendapproval'),
    url(r'^showdocument/end/check/$', views.show_document_end_check, name='showdocumentendcheck'),
    url(r'^showdocument/end/reject/$', views.show_document_end_reject, name='showdocumentendreject'),
    url(r'^showdocument/temp/$', views.show_document_temp, name='showdocumenttemp'),

    url(r'^showdocument/ing/all/$', views.show_document_ing_all, name='showdocumentingall'),
    url(r'^showdocument/ing/done/$', views.show_document_ing_done, name='showdocumentingdone'),
    url(r'^showdocument/ing/do/$', views.show_document_ing_do, name='showdocumentingdo'),
    url(r'^showdocument/ing/check/$', views.show_document_ing_check, name='showdocumentingcheck'),
    url(r'^showdocument/ing/will/$', views.show_document_ing_will, name='showdocumentingwill'),

    url(r'^viewdocument/(?P<documentId>.+)/$', views.view_document, name='viewdocument'),
    url(r'^approvedocument/(?P<approvalId>.+)/$', views.approve_document, name='approvedocument'),
    url(r'^returndocument/(?P<approvalId>.+)/$', views.return_document, name='returndocument'),
]
