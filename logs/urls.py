from django.conf.urls import url
from . import views

app_name = 'logs'

urlpatterns = [
    url(r'^insertdownloadlog/', views.insert_downloadlog, name='insertdownloadlog'),
    url(r'^showdownloads/', views.show_downloads, name='showdownloads'),
    url(r'^downloadasjson/', views.download_asjson, name='download_ajax_url'),
    url(r'^showapprovals/', views.show_approvals, name='showapprovals'),
    url(r'^approvalasjson/', views.approval_asjson, name='approval_ajax_url'),
]