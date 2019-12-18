from django.conf.urls import url
from . import views

app_name = 'sales'

urlpatterns = [
    url(r'^postcontract/', views.post_contract, name='postcontract'),
    url(r'^copycontract/(?P<contractId>.+)/$', views.copy_contract, name='copycontract'),
    url(r'^showcontracts/', views.show_contracts, name='showcontracts'),
    url(r'^salemanagerjson/$', views.salemanager_asjson, name='salemanager_ajax_url'),
    url(r'^viewcontract/(?P<contractId>.+)/$', views.view_contract, name='viewcontract'),
    url(r'^empdeptjson/$', views.empdept_asjson, name='empdept_ajax_url'),
    url(r'^contractsasjson/$', views.contracts_asjson, name='contracts_ajax_url'),
    url(r'^categoryjson/$', views.category_asjson, name="category_ajax_url"),
    url(r'^modifycontract/(?P<contractId>.+)/$', views.modify_contract, name='modifycontract'),
    url(r'^showrevenues/', views.show_revenues, name='showrevenues'),
    url(r'^revenueasjson/$', views.revenues_asjson, name='revenues_ajax_url'),
    url(r'^viewrevenue/(?P<revenueId>.+)/$', views.view_revenue, name='viewrevenue'),
    url(r'^deletecontract/(?P<contractId>.+)/$', views.delete_contract, name='deletecontract'),
    url(r'^deleterevenue/(?P<contractId>.+)/$', views.delete_revenue, name='deleterevenue'),
    url(r'^postgoal/$', views.post_goal, name='postgoal'),
    url(r'^showgoals/$', views.show_goals, name='showgoals'),
    url(r'^goalsjson/$', views.goals_asjson, name='goals_ajax_url'),
    url(r'^viewgoal/(?P<goalId>.+)/$', views.view_goal, name='viewrgoal'),
    url(r'^modifygoal/(?P<goalId>.+)/$', views.modify_goal, name='modifygoal'),
    url(r'^deletegoal/(?P<goalId>.+)/$', views.delete_goal, name='deletegoal'),
    url(r'^showpurchases/', views.show_purchases, name='showpurchases'),
    url(r'^purchasesasjson/$', views.purchases_asjson, name='purchases_ajax_url'),
    url(r'^uploadpurchase/', views.upload_purchase, name='uploadpurchase'),
    url(r'^uploadcsv/', views.upload_csv, name='uploadcsv'),
    url(r'^savepurchase/', views.save_purchase, name='savepurchase'),
    url(r'^savepurchasetable/', views.save_purchasetable, name='savepurchasetable'),
    url(r'^viewpurchase/(?P<purchaseId>.+)/$', views.view_purchase, name='viewpurchase'),
    url(r'^saverevenuetable/', views.save_revenuetable, name='saverevenuetable'),
    url(r'^viewcontractpdf/(?P<contractId>.+)/$', views.view_contract_pdf, name='viewcontractpdf'),
    url(r'^showoutstandingcollections/', views.show_outstandingcollections, name='showoutstandingcollections'),
    url(r'^showaccountspayables/', views.show_accountspayables, name='showaccountspayables'),
    url(r'^changepredictpurchase/', views.change_predictpurchase, name='changepredictpurchase'),
    url(r'^savepredictpurchase/', views.save_predictpurchase, name='savepredictpurchase'),
    url(r'^changepredictrevenue/', views.change_predictrevenue, name='changepredictrevenue'),
    url(r'^savepredictrevenue/', views.save_predictrevenue, name='savepredictrevenue'),
    url(r'^transfercontract/', views.transfer_contract, name='transfercontract'),
    url(r'^empidjson/$', views.empid_asjson, name='empid_ajax_url'),
    url(r'^savetransfercontract/', views.save_transfercontract, name='savetransfercontract'),
    url(r'^showpurchaseinadvance/', views.show_purchaseinadvance, name='showpurchaseinadvance'),
    url(r'^savecompany/', views.save_company, name='savecompany'),
    url(r'^dailyreport/', views.daily_report, name='dailyreport'),
    url(r'^outstandingasjson/$', views.outstanding_asjson, name='outstanding_ajax_url'),
    url(r'^checkgp/$', views.check_gp, name='checkgp'),
    url(r'^checkservice/$', views.check_service, name='checkservice'),
    url(r'^inadvanceasjson/$', views.inadvance_asjson, name='inadvance_ajax_url'),
    url(r'^showpurchaseinadvance/', views.show_purchaseinadvance, name='showpurchaseinadvance'),
    url(r'^showrevenueinadvance/', views.show_revenueinadvance, name='showrevenueinadvance'),
    url(r'^contractrevenues/$', views.contract_revenues, name='contractrevenues'),
    url(r'^contractpurchases/$', views.contract_purchases, name='contractpurchases'),
    url(r'^contractcosts/$', views.contract_costs, name='contractcosts'),
    url(r'^contractdetails/$', views.contract_details, name='contractdetails'),
    url(r'^contractservices/$', views.contract_services, name='contractservices'),
    url(r'^viewincentive/(?P<empId>.+)/$', views.view_incentive, name='viewincentive'),
    url(r'^viewincentiveall/$', views.view_incentiveall, name='view_incentiveall'),
    url(r'^uploadprofitloss/', views.upload_profitloss, name='uploadprofitloss'),
    url(r'^saveprofitloss/$', views.save_profitloss, name='saveprofitloss'),
    url(r'^savecost/$', views.save_cost, name='savecost'),
    url(r'^showincentives/$', views.show_incentives, name='showincentives'),
    url(r'^incentivesasjson/$', views.incentives_asjson, name='incentives_ajax_url'),
    url(r'^changeincentiveall/$', views.change_incentive_all, name='changeincentiveall'),
    url(r'^saveincentivetable/$', views.save_incentivetable, name='saveincentivetable'),
    url(r'^deleteincentive/$', views.delete_incentive, name='deleteincentive'),
    url(r'^monthlybill/$', views.monthly_bill, name='monthlybill'),
    url(r'^viewincentiveallpdf/(?P<quarter>.+)/$', views.view_incentiveall_pdf, name='viewincentiveallpdf'),
    url(r'^viewsalaryallpdf/(?P<year>.+)/$', views.view_salaryall_pdf, name='viewsalaryallpdf'),
    url(r'^viewsalaryall/$', views.view_salaryall, name='viewsalaryall'),
    url(r'^viewincentivepdf/(?P<empId>.+)/$', views.view_incentive_pdf, name='viewincentivepdf'),
    url(r'^savecontractfiles/(?P<contractId>.+)/$', views.save_contract_files, name='savecontractfiles'),
    url(r'^savepurchasefiles/(?P<contractId>.+)/$', views.save_purchase_files, name='savepurchasefiles'),
    url(r'^viewordernotipdf/(?P<contractId>.+)/$', views.view_ordernoti_pdf, name='viewordernotipdf'),
    url(r'^viewconfirmpdf/(?P<contractId>.+)/$', views.view_confirm_pdf, name='viewconfirmpdf'),
    url(r'^savecustomer/$', views.save_customer, name='savecustomer'),
    url(r'^changecontractstep/(?P<contractStep>.+)/(?P<contractId>.+)/$', views.change_contract_step, name='changecontractstep'),
    url(r'^savecategory/$', views.save_category, name='savecategory'),
    url(r'^maincategoryasjson/$', views.maincategory_asjson, name='maincategory_ajax_url'),
    url(r'^classificationasjson/$', views.classification_asjson, name='classification_ajax_url'),
    url(r'^saveclassification/$', views.save_classification, name='saveclassification'),
    url(r'^calculatebilling/$', views.calculate_billing, name='calculatebilling'),
    url(r'^postpurchaseorder/(?P<contractId>.+)/(?P<purchaseOrderCompany>.+)/$', views.post_purchase_order, name='postpurchaseorder'),
]
