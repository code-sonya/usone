from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.scheduler, name='scheduler'),
    url(r'^changeDate/', views.changeDate, name='changeDate'),
]
