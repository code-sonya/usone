from django.conf.urls import url
from . import views

app_name = 'dashboard'

urlpatterns = [
    url(r'^service/$', views.dashboard_service, name='dashboardservice'),
    url(r'^opportunity/$', views.dashboard_opportunity, name='dashboardopportunity'),
    url(r'^quarter/$', views.dashboard_quarter, name='dashboardsquarter'),
    url(r'^goal/$', views.dashboard_goal, name='dashboardgoal'),
    url(r'^credit/$', views.dashboard_credit, name='dashboardcredit'),
    # url(r'^overhour/$', views.over_hour, name='over_hour'),
    # url(r'^overjson/$', views.over_asjson, name='over_ajax_url'),
    url(r'^opportunitygraph/$', views.opportunity_graph, name='opportunity_ajax_graph'),
    url(r'^opportunityjson/$', views.opportunity_asjson, name='opportunity_ajax_url'),
    url(r'^quarterasjson/$', views.quarter_asjson, name='quarter_ajax_url'),
    url(r'^cashflowasjson/$', views.cashflow_asjson, name='cashflow_ajax_url'),
    url(r'^serviceasjson/$', views.service_asjson, name='service_ajax_url'),
    url(r'^location/$', views.dashboard_location, name='dashboardlocation'),
    url(r'^notdepositasjson/$', views.not_deposit_asjson, name='not_deposit_asjson'),
    url(r'^notwithdrawasjson/$', views.not_withdraw_asjson, name='not_withdraw_asjson'),
    url(r'^client/$', views.dashboard_client, name='dashboardclient'),
    url(r'^clientgraph/$', views.client_graph, name='client_ajax_graph'),
    url(r'^servicesasjson/$', views.services_asjson, name='services_ajax_url'),
    url(r'^contractsasjson/$', views.contracts_asjson, name='contracts_ajax_url'),
    # home 화면 / 메인 화면
    url(r'^home/$', views.home, name='home'),
]
