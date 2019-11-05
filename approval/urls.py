from django.conf.urls import url
from . import views

app_name = 'approval'

urlpatterns = [
    url(r'^postdocument/$', views.post_document, name='postdocumnet'),
    url(r'^postdocumentform/$', views.post_documentform, name='postdocumnetform'),
    url(r'^documentcategoryasjson/$', views.documentcategory_asjson, name='documentcategoryasjson'),
    url(r'^documentformasjson/$', views.documentform_asjson, name='documentformasjson'),
    url(r'^showdocumentformasjson/$', views.showdocumentform_asjson, name='showdocumentformasjson'),
    url(r'^postdocumentcategory/$', views.post_documentcategory, name='postdocumentcategory'),
    url(r'^showdocumentform/$', views.show_documentform, name='showdocumentform'),
    url(r'^modifydocumentform/(?P<formId>.+)/$', views.modify_documentform, name='modifydocumentform'),
]
