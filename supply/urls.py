# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views


app_name = 'supply'

urlpatterns = [
    url(r'^showrentals/$', views.show_rentals, name='showrentals'),
    url(r'^rentalsasjson/$', views.rentals_asjson, name='rentalsasjson'),
    url(r'^postbook/$', views.post_book, name='postbook'),
    url(r'^modifybook/$', views.modify_book, name='modifybook'),
    url(r'^deletebook/$', views.delete_book, name='deletebook'),
    url(r'^postrentals/$', views.post_rentals, name='postrentals'),
    url(r'^booksasjson/$', views.books_asjson, name='booksasjson'),
    url(r'^postrent/$', views.post_rent, name='postrent'),
    url(r'^showsavings/$', views.show_savings, name='showsavings'),
    url(r'^showbooks/$', views.show_books, name='showbooks'),
    url(r'^savingsasjson/$', views.savings_asjson, name='savingsasjson'),
    url(r'^postsaving/$', views.post_saving, name='postsaving'),
    url(r'^viewsaving/(?P<savingId>.+)/(?P<centerId>.+)/$', views.view_saving, name='viewsaving'),
    url(r'^deletesaving/(?P<savingId>.+)/$', views.delete_saving, name='deletesaving'),
]
