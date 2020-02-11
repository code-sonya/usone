# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views


app_name = 'supply'

urlpatterns = [
    url(r'^showrentals/$', views.show_rentals, name='showrentals'),
    url(r'^rentalsasjson/$', views.rentals_asjson, name='rentalsasjson'),
    url(r'^postbook/$', views.post_book, name='postbook'),
    url(r'^postrentals/$', views.post_rentals, name='postrentals'),
    url(r'^booksasjson/$', views.books_asjson, name='booksasjson'),
    url(r'^postrent/$', views.post_rent, name='postrent'),
    url(r'^showsavings/$', views.show_savings, name='showsavings'),
    url(r'^savingsasjson/$', views.savings_asjson, name='savingsasjson'),
    url(r'^postsaving/$', views.post_saving, name='postsaving'),
    url(r'^viewsaving/(?P<savingId>.+)/$', views.view_saving, name='viewsaving'),
]
