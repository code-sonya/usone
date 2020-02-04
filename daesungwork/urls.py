from django.conf.urls import url
from . import views

app_name = 'daesungwork'

urlpatterns = [
    url(r'^showcentermanagers/$', views.show_centermanagers, name='showcentermanagers'),
    url(r'^postmanager/$', views.post_manager, name='postmanager'),
    url(r'^centerasjson/$', views.center_asjson, name='centerasjson'),
    url(r'^centermanagerasjson/$', views.centermanager_asjson, name='centermanagerasjson'),
    url(r'^viewcentermanager/(?P<centerManagerId>.+)/$', views.view_centermanager, name='viewcentermanager'),
]