from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.show_clientlist, name='show_clientlist'),
    url(r'^postclient/$', views.post_client, name='post_client'),
    url(r'^viewclient/(?P<companyName>.+)/$', views.view_client, name='view_client')
]
