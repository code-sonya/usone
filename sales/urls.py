from django.conf.urls import url
from . import views

app_name = 'sales'

urlpatterns = [
    url(r'^postopportunity/', views.post_opportunity, name='postopportunity'),
    url(r'^showcontracts/', views.show_contracts, name='showcontracts'),
    url(r'^contractasjson/$', views.contract_asjson, name='contractasjson'),
    url(r'^salemanagerjson/$', views.salemanager_asjson, name='salemanager_ajax_url'),
]
