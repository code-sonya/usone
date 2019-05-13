from django.conf.urls import url
from . import views

app_name = 'dashboard'

urlpatterns = [
    url(r'^service/$', views.dashboard_service, name='dashboardservice'),
    url(r'^opportunity/$', views.dashboard_opportunity, name='dashboardopportunity'),
    url(r'^sales/$', views.dashboard_sales, name='dashboardsales'),
    url(r'^contract/$', views.dashboard_contract, name='dashboardcontract'),
    url(r'^overhour/$', views.over_hour, name='over_hour'),
    url(r'^overjson/$', views.over_asjson, name='over_ajax_url'),
    url(r'^filterjson/$', views.filter_asjson, name='filter_ajax_url'),
    url(r'^opportunityjson/$', views.opportunity_asjson, name='opportunity_ajax_url'),
]
