from django.conf.urls import url
from . import views

app_name = 'scheduler'

urlpatterns = [
    url(r'^scheduler/(?P<day>.+)/$', views.scheduler, name='scheduler'),
    url(r'^changeDate/', views.changeDate, name='changeDate'),
    url(r'^showeventday/', views.show_eventday, name='showeventday'),
    url(r'^showeventdayasjson/', views.showeventday_asjson, name='showeventdayasjson'),
    url(r'^vieweventday/(?P<eventDate>.+)/$', views.view_eventday, name='vieweventday'),
    url(r'^posteventday/$', views.post_eventday, name='posteventday'),
    url(r'^deleteeventday/(?P<eventDate>.+)/$', views.delete_eventday, name='deleteeventday'),
    url(r'^checkeventday/$', views.check_eventday, name='checkeventday'),
]
