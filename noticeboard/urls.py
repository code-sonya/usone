from django.conf.urls import url
from . import views

app_name = 'noticeboard'

urlpatterns = [
    url(r'^postboard/(?P<serviceId>.+)/$', views.post_board, name='postboard'),
    url(r'^showboards/$', views.show_boards, name='showboards'),
    url(r'^viewboard/(?P<boardId>.+)/$', views.view_board, name='viewboard'),
    url(r'^deleteboard/(?P<boardId>.+)/$', views.delete_board, name='deleteboard'),
    url(r'^modifyboard/(?P<boardId>.+)/$', views.modify_board, name='modifyboard'),
    url(r'^json/$', views.board_asjson, name='board_ajax_url'),
    url(r'^shownotices/$', views.show_notices, name='show_notices'),
]
