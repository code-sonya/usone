from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<serviceId>\d+)/$', views.signature, name='signature'),
    url(r'^saveimg/(?P<serviceId>\d+)/$', views.saveimg, name='saveimg'),
]
