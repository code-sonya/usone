from django.conf.urls import url
from . import views

app_name = 'logs'

urlpatterns = [
    url(r'^insertdownloadlog/', views.insert_downloadlog, name='insertdownloadlog')
]