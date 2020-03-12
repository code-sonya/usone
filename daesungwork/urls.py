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
    # 구매 현황
    url(r'^showbuystatus/$', views.show_buystatus, name='showbuystatus'),
    url(r'^postbuy/$', views.post_buy, name='postbuy'),
    url(r'^buysasjson/$', views.buys_asjson, name='buysasjson'),
    url(r'^deletebuy/(?P<buyId>.+)/$', views.delete_buy, name='deletebuy'),
    url(r'^insertbuy/$', views.insert_buy, name='insertbuy'),
    # 판매 현황
    url(r'^showsalestatus/(?P<affiliateId>.+)/$', views.show_salestatus, name='showsalestatus'),
    url(r'^postsale/(?P<affiliateId>.+)/$', views.post_sale, name='postsale'),
    url(r'^modelasjson/$', views.model_asjson, name='modelasjson'),
    url(r'^salesasjson/$', views.sales_asjson, name='salesasjson'),
    url(r'^deletesale/(?P<saleId>.+)/$', views.delete_sale, name='deletesale'),
    url(r'^insertsale/$', views.insert_sale, name='insertsale'),
    # 재생 현황
    url(r'^showreproductionstatus/$', views.show_reproductionstatus, name='showreproductionstatus'),
    url(r'^postreproduction/$', views.post_reproduction, name='postreproduction'),
    url(r'^reproductionasjson/$', views.reproduction_asjson, name='reproductionasjson'),
    url(r'^deletereproduction/(?P<reproductionId>.+)/$', views.delete_reproduction, name='deletereproduction'),
    url(r'^insertreproduction/$', views.insert_reproduction, name='insertreproduction'),
    # DP 현황
    url(r'^showdisplaystatus/$', views.show_displaystatus, name='showdisplaystatus'),
    url(r'^postdisplay/$', views.post_display, name='postdisplay'),
    url(r'^displayasjson/$', views.display_asjson, name='displayasjson'),
    url(r'^deletedisplay/(?P<displayId>.+)/$', views.delete_display, name='deletedisplay'),
    url(r'^insertdisplay/$', views.insert_display, name='insertdisplay'),
    # 제품 관리
    url(r'^showproducts/$', views.show_products, name='showproducts'),
    url(r'^productasjson/$', views.product_asjson, name='productasjson'),
    url(r'^viewproduct/(?P<productId>.+)/$', views.view_product, name='viewproduct'),
    url(r'^deleteproduct/(?P<productId>.+)/$', views.delete_product, name='deleteproduct'),
    url(r'^warehouseimageasjson/$', views.warehouseimage_asjson, name='warehouseimageasjson'),
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
    # 제품위치 조회
    url(r'^showproductlocation/$', views.show_productlocation, name='showproductlocation'),
    url(r'^locationasjson/$', views.location_asjson, name='locationasjson'),
    # 재고관리
    url(r'^showstocks/$', views.show_stocks, name='showstocks'),
    url(r'^stocksasjson/$', views.stocks_asjson, name='stocksasjson'),
    url(r'^poststock/(?P<typeId>.+)/$', views.post_stock, name='poststock'),
    url(r'^modifystock/(?P<stockcheckId>.+)/$', views.modify_stock, name='modifystock'),
    url(r'^typeproductsasjson/$', views.typeproducts_asjson, name='typeproductsasjson'),
    url(r'^viewstockpdf/(?P<stockcheckId>.+)/$', views.view_stock_pdf, name='viewstockpdf'),
    # 입출고 관리
    url(r'^showstockinout/$', views.show_stockinout, name='showstockinout'),
    url(r'^poststockinout/(?P<typeName>.+)/$', views.post_stockinout, name='sohwstockinout'),
    url(r'^stockinoutasjson/$', views.stockinout_asjson, name='stockinoutasjson'),
    url(r'^inoutcheckasjson/$', views.inoutcheck_asjson, name='inoutcheckasjson'),
]