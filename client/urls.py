from django.conf.urls import url
from . import views

app_name = 'client'

urlpatterns = [
    url(r'^$', views.show_clientlist, name='show_clientlist'),
    url(r'^postclient/$', views.post_client, name='post_client'),
    url(r'^viewclient/(?P<companyName>.+)/$', views.view_client, name='view_client'),
    url(r'^viewcustomer/(?P<customerId>.+)/$', views.view_customer, name='view_customer')
]
