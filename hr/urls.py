from django.conf.urls import url
from . import views

app_name = 'hr'

urlpatterns = [
    url(r'^$', views.profile, name='profile'),
    url(r'^showpunctuality/$', views.show_punctuality, name='showpunctuality'),
    url(r'^uploadcaps/$', views.upload_caps, name='uploadcaps'),
    url(r'^savecaps/$', views.save_caps, name='savecaps'),
]
