from django.conf.urls import url
from . import views

app_name = 'client'

urlpatterns = [
    url(r'^$', views.show_clientlist, name='show_clientlist'),
    url(r'^postclient/$', views.post_client, name='post_client'),
    url(r'^checkcompany/$', views.check_company, name='checkcompany'),
    url(r'^modifyclient/(?P<companyName>.+)/$', views.modify_client, name='modifyclient'),
    url(r'^viewclient/(?P<companyName>.+)/$', views.view_client, name='view_client'),
    url(r'^viewcustomer/(?P<customerId>.+)/$', views.view_customer, name='view_customer'),
    url(r'^postcustomer/(?P<companyName>.+)/$', views.post_customer, name='post_customer'),
    url(r'^deletecustomer/(?P<customerId>.+)/$', views.delete_customer, name='delete_customer'),
    url(r'^servicejson/$', views.service_asjson, name='service_ajax_url'),
    url(r'^filterjson/$', views.filter_asjson, name='filter_ajax_url'),
]
