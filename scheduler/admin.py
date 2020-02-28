from django.contrib import admin
from .models import Eventday


@admin.register(Eventday)
class EventdayAdmin(admin.ModelAdmin):
    list_display = ('eventDate', 'eventName', 'eventType')
    list_filter = ('eventDate',)
    list_display_links = ['eventDate', 'eventName', 'eventType']
