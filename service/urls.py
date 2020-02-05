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
    url(r'^showvacationsasjson/', views.showvacations_asjson, name='showvacationsasjson'),
    url(r'^deletevacation/(?P<vacationId>.+)/$', views.delete_vacation, name='deletevacation'),
    url(r'^dayreport/(?P<day>.+)/$', views.day_report, name='dayreport'),
    url(r'^json/$', views.service_asjson, name='service_ajax_url'),
    url(r'^viewservicepdf/(?P<serviceId>.+)/$', views.view_service_pdf, name='viewservicepdf'),
    url(r'^postgeolocation/(?P<serviceId>.+)/(?P<status>.+)/(?P<latitude>.+)/(?P<longitude>.+)/$',
        views.post_geolocation, name='postgeolocation'),
    url(r'^changecontractsname/', views.change_contracts_name, name='changecontractsname'),
    url(r'^adminservice/(?P<serviceId>.+)/$', views.admin_service, name='adminservice'),
    url(r'^saveconfirmfiles/(?P<contractId>.+)/$', views.save_confirm_files, name='savepurchasefiles'),
    url(r'^showservicetype/$', views.show_service_type, name='showservicetype'),
    url(r'^showservicetypeasjson/$', views.showservicetype_asjson, name='showservicetypeasjson'),
    url(r'^viewservicetype/(?P<typeId>.+)/$', views.view_service_type, name='viewservicetype'),
    url(r'^postservicetype/$', views.post_service_type, name='postservicetype'),
    url(r'^deleteservicetype/(?P<typeId>.+)/$', views.delete_service_type, name='deleteservicetype'),
    url(r'^coworkersign/(?P<serviceId>.+)/$', views.coworker_sign, name='coworkersign'),
    # 주간회의록
    url(r'^showreports/$', views.show_reports, name='showreports'),
    url(r'^reportsasjson/$', views.reports_asjson, name='reportsasjson'),
    url(r'^postreport/$', views.post_report, name='postreport'),
    url(r'^viewreport/(?P<reportId>.+)/$', views.view_report, name='viewreport'),
    url(r'^deletereport/(?P<reportId>.+)/$', views.delete_report, name='deletereport'),
    url(r'^modifyreport/(?P<reportId>.+)/$', views.modify_report, name='modifyreport'),
]
