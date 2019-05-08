from django.conf.urls import url
from . import views

app_name = 'sales'

urlpatterns = [
    url(r'^postopportunity/', views.post_opportunity, name='postopportunity'),
    url(r'^showcontracts/', views.show_contracts, name='postopportunity'),
    url(r'^contractasjson/$', views.contract_asjson, name='contractasjson'),
]