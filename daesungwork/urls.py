from django.conf.urls import url
from . import views

app_name = 'daesungwork'

urlpatterns = [
    # 센터별 담당자 관리
    url(r'^showcentermanagers/$', views.show_centermanagers, name='showcentermanagers'),
    url(r'^postmanager/$', views.post_manager, name='postmanager'),
    url(r'^modifycentermanager/(?P<centerManagerId>.+)/$', views.modify_centermanager, name='modifycentermanager'),
    url(r'^centerasjson/$', views.center_asjson, name='centerasjson'),
    url(r'^centermanagerasjson/$', views.centermanager_asjson, name='centermanagerasjson'),
    url(r'^viewcentermanager/(?P<centerManagerId>.+)/$', views.view_centermanager, name='viewcentermanager'),
    url(r'^deletecentermanager/(?P<centerManagerId>.+)/$', views.delete_centermanager, name='deletecentermanager'),
    # 센터별 체크 리스트
    url(r'^showchecklist/$', views.show_checklist, name='showchecklist'),
    url(r'^postchecklist/$', views.post_checklist, name='postchecklist'),
    url(r'^viewchecklistpdf/(?P<month>.+)/$', views.view_checklist_pdf, name='viewchecklistpdf'),
    # 센터 관리
    url(r'^showcenters/$', views.show_centers, name='showcenters'),
    url(r'^deletecenter/$', views.delete_center, name='deletecenter'),
]