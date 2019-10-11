from django.conf.urls import url
from . import views
app_name = 'service'
urlpatterns = [
    url(r'^postservice/(?P<postdate>.+)/$', views.post_service, name='postservice'),
    url(r'^postvacation/', views.post_vacation, name='postvacation'),
    url(r'^postserviceform/', views.post_serviceform, name='postserviceform'),
    url(r'^showservices/', views.show_services, name='showservices'),
    url(r'^viewservice/(?P<serviceId>.+)/$', views.view_service, name='viewservice'),
    url(r'^saveservice/(?P<serviceId>.+)/$', views.save_service, name='saveservice'),
    url(r'^deleteservice/(?P<serviceId>.+)/$', views.delete_service, name='deleteservice'),
    url(r'^modifyservice/(?P<serviceId>.+)/$', views.modify_service, name='modifyservice'),
    url(r'^copyservice/(?P<serviceId>.+)/$', views.copy_service, name='copyservice'),
    url(r'^showserviceforms/', views.show_serviceforms, name='showserviceforms'),
    url(r'^modifyserviceform/(?P<serviceFormId>.+)/$', views.modify_serviceform, name='modifyserviceform'),
    url(r'^deleteserviceform/(?P<serviceFormId>.+)/$', views.delete_serviceform, name='deleteserviceform'),
    url(r'^showvacations/', views.show_vacations, name='showvacations'),
    url(r'^deletevacation/(?P<vacationId>.+)/$', views.delete_vacation, name='deletevacation'),
    url(r'^dayreport/(?P<day>.+)/$', views.day_report, name='dayreport'),
    url(r'^json/$', views.service_asjson, name='service_ajax_url'),
    url(r'^viewservicepdf/(?P<serviceId>.+)/$', views.view_service_pdf, name='viewservicepdf'),
    url(r'^postgeolocation/(?P<serviceId>.+)/(?P<status>.+)/(?P<latitude>.+)/(?P<longitude>.+)/$',
        views.post_geolocation, name='postgeolocation'),
    url(r'^changecontractsname/', views.change_contracts_name, name='changecontractsname'),
    url(r'^postcar/', views.post_car, name='postcar'),
]
