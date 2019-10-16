from django.conf.urls import url
from . import views

app_name = 'extrapay'

urlpatterns = [
    url(r'^overhour/$', views.over_hour, name='over_hour'),
    url(r'^overjson/$', views.over_asjson, name='over_ajax_url'),
    url(r'^postcar/', views.post_car, name='postcar'),
    url(r'^showoils/', views.show_oils, name='showoils'),
    url(r'^postoils/', views.post_oils, name='postoils'),
    url(r'^showfuel/', views.show_fuel, name='showfuel'),
    url(r'^adminfuel/', views.admin_fuel, name='adminfuel'),
    url(r'^approvalfuel/(?P<empId>.+)/$', views.approval_fuel, name='approvalfuel'),
    url(r'^postfuel/', views.post_fuel, name='postfuel'),
    url(r'^approvalpostfuel/', views.approval_post_fuel, name='approvalpostfuel'),
    url(r'^adminfuelasjson/$', views.adminfuel_asjson, name='adminfuelasjson'),
    url(r'^approvalfuelasjson/$', views.approvalfuel_asjson, name='approvalfuelasjson'),
    url(r'^fuelasjson/$', views.fuel_asjson, name='fuelasjson'),
    url(r'^viewoverhour/(?P<extraPayId>.+)/$', views.view_overhour, name='viewoverhour'),
]
