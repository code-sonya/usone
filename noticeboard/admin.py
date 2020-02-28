from django.contrib import admin
from .models import Board


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('boardId', 'serviceId', 'boardWriter', 'boardTitle')
    list_filter = ('boardWriter',)
    list_display_links = ['boardId', 'serviceId', 'boardWriter', 'boardTitle']
