from django.contrib import admin
from .models import OverHour


@admin.register(OverHour)
class OverHourAdmin(admin.ModelAdmin):
    list_display = ('overHourId', 'empName', 'overHourDate', 'sumOverHour', 'compensatedHour', 'payHour')
    list_filter = ('empName', 'overHourDate')
    list_display_links = ['overHourId', 'empName', 'overHourDate']