from django.conf.urls import url
from . import views

app_name = 'daesungwork'

urlpatterns = [
    url(r'^managecenter/$', views.manage_center, name='managecenter'),
    url(r'^postmanager/$', views.post_manager, name='postmanager'),
]