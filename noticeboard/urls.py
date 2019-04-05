from django.conf.urls import url
from . import views

app_name = 'noticeboard'

urlpatterns = [
    url(r'^postboard/(?P<serviceId>.+)/$', views.post_board, name='postboard'),
    url(r'^showboards/$', views.show_boards, name='showboards'),
]
