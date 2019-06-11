from django.conf.urls import url
from . import views

app_name = 'sales'

urlpatterns = [
    url(r'^postcontract/', views.post_contract, name='postcontract'),
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
]
