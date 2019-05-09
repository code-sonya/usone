from django.conf.urls import url
from . import views

app_name = 'sales'

urlpatterns = [
    url(r'^postcontract/', views.post_contract, name='postcontract'),
    url(r'^showcontracts/', views.show_contracts, name='showcontracts'),
    url(r'^contractasjson/$', views.contract_asjson, name='contractasjson'),
    url(r'^salemanagerjson/$', views.salemanager_asjson, name='salemanager_ajax_url'),
    url(r'^viewcontract/(?P<contractId>.+)/$', views.view_contract, name='viewcontract'),
    url(r'^empdeptjson/$', views.empdept_asjson, name='empdept_ajax_url'),
    url(r'^filterjson/$', views.filter_asjson, name='filter_ajax_url'),
    url(r'^categoryjson/$', views.category_asjson, name="category_ajax_url")
]
