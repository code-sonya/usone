from django.contrib import admin

from .models import AppToken

# Register your models here.
@admin.register(AppToken)
class AppTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'empId', 'token')
    list_filter = ('empId',)
    list_display_links = ['id', 'empId', 'token']
