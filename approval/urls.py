from django.conf.urls import url
from . import views

app_name = 'approval'

urlpatterns = [
    url(r'^postdocument/$', views.post_document, name='postdocumnet'),
]
