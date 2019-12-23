from django.conf.urls import url
from . import views

app_name = 'hr'

urlpatterns = [
    url(r'^$', views.profile, name='profile'),
    url(r'^showprofiles/$', views.show_profiles, name='showprofiles'),
    url(r'^showprofilesasjson/$', views.showprofiles_asjson, name='showprofilesasjson'),
    url(r'^viewprofile/(?P<empId>.+)/$', views.view_profile, name='viewprofile'),
    url(r'^showdepartments/$', views.show_departments, name='showdepartments'),
    url(r'^showdepartmentsasjson/$', views.showdepartments_asjson, name='showdepartmentsasjson'),
    url(r'^viewdepartment/(?P<deptId>.+)/$', views.view_department, name='viewdepartment'),
    url(r'^showpunctuality/(?P<day>.+)/$', views.show_punctuality, name='showpunctuality'),
    url(r'^showyearpunctuality/(?P<year>.+)/$', views.show_yearpunctuality, name='showyearpunctuality'),
    url(r'^showabsence/$', views.show_absence, name='showabsence'),
    url(r'^uploadcaps/$', views.upload_caps, name='uploadcaps'),
    url(r'^savecaps/$', views.save_caps, name='savecaps'),
    url(r'^absencesasjson/$', views.absences_asjson, name='absences_ajax_url'),
    url(r'^viewabsence/(?P<punctualityId>.+)/$', views.view_absence, name='viewabsence'),
    url(r'^modifyabsence/(?P<punctualityId>.+)/$', views.modify_absence, name='modifyabsence'),
]
