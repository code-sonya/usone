from django.conf.urls import url
from . import views

app_name = 'extrapay'

urlpatterns = [
    url(r'^overhour/$', views.over_hour, name='overhour'),
    url(r'^overhourall/$', views.overhour_all, name='overhourall'),
    url(r'^postoverhour/$', views.post_overhour, name='postoverhour'),
    url(r'^saveoverhourtable/$', views.save_overhourtable, name='saveoverhourtable'),
    url(r'^overjson/$', views.over_asjson, name='over_ajax_url'),
    url(r'^postcar/', views.post_car, name='postcar'),
    url(r'^showoils/', views.show_oils, name='showoils'),
    url(r'^postoils/', views.post_oils, name='postoils'),
    url(r'^showfuel/', views.show_fuel, name='showfuel'),
    url(r'^adminfuel/', views.admin_fuel, name='adminfuel'),
    url(r'^postfuel/', views.post_fuel, name='postfuel'),
    url(r'^adminfuelasjson/$', views.adminfuel_asjson, name='adminfuelasjson'),
    url(r'^fuelasjson/$', views.fuel_asjson, name='fuelasjson'),
    url(r'^viewoverhour/(?P<extraPayId>.+)/$', views.view_overhour, name='viewoverhour'),
]
