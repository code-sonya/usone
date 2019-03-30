from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^postservice/(?P<postdate>.+)/$', views.postservice, name='postservice'),
    url(r'^postvacation/', views.postvacation, name='postvacation'),
    url(r'^postserviceform/', views.postserviceform, name='postserviceform'),
    url(r'^showservices/', views.showservices, name='showservices'),
]
