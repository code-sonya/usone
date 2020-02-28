from django.conf.urls import url
from . import views

app_name = 'logs'

urlpatterns = [
    url(r'^insertdownloadlog/', views.insert_downloadlog, name='insertdownloadlog'),
    url(r'^showdownloads/', views.show_downloads, name='showdownloads'),
    url(r'^downloadasjson/', views.download_asjson, name='download_ajax_url'),
    url(r'^showapprovals/', views.show_approvals, name='showapprovals'),
    url(r'^approvalasjson/', views.approval_asjson, name='approval_ajax_url'),
    url(r'^contractlog/', views.show_contract_log, name='contractlog'),
    url(r'^contractlogasjson/', views.contractlog_asjson, name='contractlog_ajax_url'),
    url(r'^showorders/', views.show_orders, name='showorders'),
    url(r'^orderasjson/', views.order_asjson, name='order_ajax_url'),
]