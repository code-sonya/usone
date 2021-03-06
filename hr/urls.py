from django.conf.urls import url
from . import views

app_name = 'hr'

urlpatterns = [
    url(r'^$', views.profile, name='profile'),
    url(r'^showprofiles/$', views.show_profiles, name='showprofiles'),
    url(r'^showprofilesasjson/$', views.showprofiles_asjson, name='showprofilesasjson'),
    url(r'^viewprofile/(?P<empId>.+)/$', views.view_profile, name='viewprofile'),
    url(r'^postprofile/$', views.post_profile, name='postprofile'),
    url(r'^showdepartments/$', views.show_departments, name='showdepartments'),
    url(r'^showdepartmentsasjson/$', views.showdepartments_asjson, name='showdepartmentsasjson'),
    url(r'^viewdepartment/(?P<deptId>.+)/$', views.view_department, name='viewdepartment'),
    url(r'^deletedepartment/(?P<deptId>.+)/$', views.delete_department, name='deletedepartment'),
    url(r'^postdepartment/$', views.post_department, name='postdepartment'),
    url(r'^showpunctuality/(?P<day>.+)/$', views.show_punctuality, name='showpunctuality'),
    url(r'^showyearpunctuality/(?P<year>.+)/$', views.show_yearpunctuality, name='showyearpunctuality'),
    url(r'^showabsence/$', views.show_absence, name='showabsence'),
    url(r'^uploadcaps/$', views.upload_caps, name='uploadcaps'),
    url(r'^savecaps/$', views.save_caps, name='savecaps'),
    url(r'^absencesasjson/$', views.absences_asjson, name='absences_ajax_url'),
    url(r'^viewabsence/(?P<punctualityId>.+)/$', views.view_absence, name='viewabsence'),
    url(r'^modifyabsence/(?P<punctualityId>.+)/$', views.modify_absence, name='modifyabsence'),
    url(r'^checkdepartment/$', views.check_department, name='checkdepartment'),
    url(r'^checkprofile/$', views.check_profile, name='checkprofile'),
    url(r'^emailregistration/$', views.email_registration, name='emailregistration'),
    url(r'^adminemailasjson/$', views.adminemail_asjson, name='adminemail_ajax_url'),
    url(r'^uploadempstamp/(?P<empId>.+)/$', views.upload_emp_stamp, name='uploadempstamp'),
    url(r'^redodefaultstamp/(?P<empId>.+)/$', views.redo_default_stamp, name='redodefaultstamp'),
    url(r'^showvacations/$', views.show_vacations, name='showvacations'),
    url(r'^showvacationsasjson/$', views.showvacations_asjson, name='showvacationsasjson'),
    url(r'^deletevacation/$', views.delete_vacation, name='deletevacation'),
    url(r'^savevacation/$', views.save_vacation, name='savevacation'),
    url(r'^vacationsexcel/$', views.vacations_excel, name='vacationsexcel'),
    url(r'^vacationsexcelasjson/$', views.vacationsexcel_asjson, name='vacationsexcelasjson'),
    url(r'^returnvacation/$', views.return_vacation, name='returnvacation'),
    url(r'^returnvacationasjson/$', views.returnvacation_asjson, name='returnvacationasjson'),
    url(r'^vacationdocumentasjson/$', views.vacationdocument_asjson, name='vacationdocumentasjson'),
    url(r'^cancelvacation/$', views.cancel_vacation, name='cancelvacation'),
    url(r'^detailvacationasjson/$', views.detailvacation_asjson, name='detailvacationasjson'),
    # 알림
    url(r'^alertcountingasjson/$', views.alertcounting_asjson, name='alertcountingasjson'),
    url(r'^clickalertasjson/$', views.clickalert_asjson, name='clickalertasjson'),
    url(r'^pastalertasjson/$', views.pastalert_asjson, name='pastalertasjson'),
]

