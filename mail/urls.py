from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<serviceId>\d+)/$', views.selectreceiver, name='selectreceiver'),
    url(r'^sendmail/(?P<serviceId>.+)/$', views.sendmail, name='sendmail'),
]
