from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^post/(?P<postdate>.+)/$', views.post, name='post'),
]
