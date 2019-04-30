from django.conf.urls import url
from . import views

app_name = 'dashboard'

urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^dashboardreport/$', views.dashboardreport, name='dashboardreport'),
    url(r'^overhour/$', views.over_hour, name='over_hour'),
    url(r'^overjson/$', views.over_asjson, name='over_ajax_url'),
    url(r'^filterjson/$', views.filter_asjson, name='filter_ajax_url'),
]
