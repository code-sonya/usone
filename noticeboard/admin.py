from django.contrib import admin
from .models import Serviceboard, Board


@admin.register(Serviceboard)
class ServiceboardAdmin(admin.ModelAdmin):
    list_display = ('serviceBoardId', 'serviceBoardWriter', 'serviceBoardTitle', 'serviceBoardEditDatetime')
    list_filter = ('serviceBoardWriter',)
    list_display_links = ['serviceBoardId']


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('boardId', 'boardWriter', 'boardTitle', 'boardEditDatetime')
    list_filter = ('boardWriter',)
    list_display_links = ['boardId']
