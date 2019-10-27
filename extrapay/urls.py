from django.conf.urls import url
from . import views

app_name = 'extrapay'

urlpatterns = [
    url(r'^overhour/$', views.over_hour, name='overhour'),
    url(r'^overhourall/(?P<searchdate>.+)$', views.overhour_all, name='overhourall'),
    url(r'^postoverhour/$', views.post_overhour, name='postoverhour'),
    url(r'^saveoverhourtable/$', views.save_overhourtable, name='saveoverhourtable'),
    url(r'^overjson/$', views.over_asjson, name='over_ajax_url'),
    url(r'^postcar/', views.post_car, name='postcar'),
    url(r'^showoils/', views.show_oils, name='showoils'),
    url(r'^postoils/', views.post_oils, name='postoils'),
    url(r'^showfuel/', views.show_fuel, name='showfuel'),
    url(r'^adminfuel/', views.admin_fuel, name='adminfuel'),
    url(r'^approvalfuel/(?P<empId>.+)/$', views.approval_fuel, name='approvalfuel'),
    url(r'^postfuel/', views.post_fuel, name='postfuel'),
    url(r'^delfuel/', views.del_fuel, name='delfuel'),
    url(r'^approvalpostfuel/', views.approval_post_fuel, name='approvalpostfuel'),
    url(r'^adminfuelasjson/$', views.adminfuel_asjson, name='adminfuelasjson'),
    url(r'^approvalfuelasjson/$', views.approvalfuel_asjson, name='approvalfuelasjson'),
    url(r'^fuelasjson/$', views.fuel_asjson, name='fuelasjson'),
    url(r'^viewoverhour/(?P<extraPayId>.+)/$', views.view_overhour, name='viewoverhour'),
    url(r'^viewextrapaypdf/(?P<yearmonth>.+)/$', views.view_extrapay_pdf, name='viewextrapaypdf'),
    url(r'^postdistance/$', views.post_distance, name='postdistance'),
    url(r'^showsalarys/$', views.show_salarys, name='showsalarys'),
    url(r'^salaryjson/$', views.salary_asjson, name='salary_ajax_url'),
    url(r'^savesalarytable/$', views.save_salarytable, name='savesalarytable'),
    url(r'^postsalary/$', views.post_salary, name='postsalary'),
    url(r'^viewoverhourpdf/(?P<extraPayId>.+)/$', views.view_overhour_pdf, name='viewoverhourpdf'),
    url(r'^deleteoverhour/$', views.delete_overhour, name='deleteoverhour'),
    url(r'^viewfuelpdf/(?P<yearmonth>.+)/$', views.view_fuel_pdf, name='viewfuelpdf'),
]
