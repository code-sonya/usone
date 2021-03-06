"""usone URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings
from service import views
import datetime

urlpatterns = [
    path('admin/', admin.site.urls),
    path(r'', views.day_report),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^client/', include('client.urls')),
    url(r'^dashboard/', include('dashboard.urls')),
    url(r'^hr/', include('hr.urls')),
    url(r'^mail/', include('mail.urls')),
    url(r'^noticeboard/', include('noticeboard.urls')),
    url(r'^scheduler/', include('scheduler.urls')),
    url(r'^service/', include('service.urls')),
    url(r'^signature/', include('signature.urls')),
    url(r'^sales/', include('sales.urls')),
    url(r'^extrapay/', include('extrapay.urls')),
    url(r'^approval/', include('approval.urls')),
    url(r'^logs/', include('logs.urls')),

]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)

# if settings.DEBUG: # setting.py의 DEBUG = True인 경우
#     import debug_toolbar
#     urlpatterns += [
#         url(r'^__debug__/', include(debug_toolbar.urls)),
