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
]
