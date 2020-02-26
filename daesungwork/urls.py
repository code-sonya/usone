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
    # 판매 현황
    url(r'^showsalestatus/(?P<affiliateId>.+)/$', views.show_salestatus, name='showsalestatus'),
    url(r'^postsale/(?P<affiliateId>.+)/$', views.post_sale, name='postsale'),
    url(r'^modelasjson/$', views.model_asjson, name='modelasjson'),
    url(r'^salesasjson/$', views.sales_asjson, name='salesasjson'),
    url(r'^deletesale/(?P<saleId>.+)/$', views.delete_sale, name='deletesale'),
    # DP 현황
    url(r'^showdisplaystatus/$', views.show_displaystatus, name='showdisplaystatus'),
    url(r'^postdisplay/$', views.post_display, name='postdisplay'),
    url(r'^displayasjson/$', views.display_asjson, name='displayasjson'),
    url(r'^deletedisplay/(?P<displayId>.+)/$', views.delete_display, name='deletedisplay'),
    # 제품 관리
    url(r'^showproducts/$', views.show_products, name='showproducts'),
    url(r'^productasjson/$', views.product_asjson, name='productasjson'),
    url(r'^viewproduct/(?P<productId>.+)/$', views.view_product, name='viewproduct'),
    url(r'^deleteproduct/(?P<productId>.+)/$', views.delete_product, name='deleteproduct'),
    # 사이즈 관리
    url(r'^postsize/(?P<productId>.+)/$', views.post_size, name='postsize'),
    url(r'^deletesize/(?P<sizeId>.+)/$', views.delete_size, name='deletesize'),
    # 창고관리
    url(r'^showwarehouses/$', views.show_warehouses, name='showwarehouses'),
    url(r'^warehousesasjson/$', views.warehouses_asjson, name='warehousesasjson'),
    url(r'^postmaincategory/$', views.post_maincategory, name='postmaincategory'),
    url(r'^postsubcategory/$', views.post_subcategory, name='postsubcategory'),
    url(r'^deletewarehouse/(?P<warehouseId>.+)/$', views.delete_warehouse, name='deletewarehouse'),
    # 일일보고
    url(r'^showdailyreports/$', views.show_dailyreports, name='showdailyreports'),
    url(r'^dailyreportsasjson/$', views.dailyreports_asjson, name='dailyreportsasjson'),
    url(r'^postdailyreport/$', views.post_dailyreport, name='postdailyreport'),
    url(r'^viewdailyreport/(?P<dailyreportId>.+)/$', views.view_dailyreport, name='viewdailyreport'),
    url(r'^deletedailyreport/(?P<dailyreportId>.+)/$', views.delete_dailyreport, name='deletedailyreport'),
]