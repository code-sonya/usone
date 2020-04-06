from django.contrib import admin
from .models import Board, NoticeList, NoticeCategory, NoticeSubject, Notice, NoticeFile, NoticeComment, NoticeTag


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('boardId', 'serviceId', 'boardWriter', 'boardTitle')
    list_filter = ('boardWriter',)
    list_display_links = ['boardId', 'serviceId', 'boardWriter', 'boardTitle']


@admin.register(NoticeList)
class NoticeListAdmin(admin.ModelAdmin):
    list_display = ('list',)
    list_display_links = ('list',)


@admin.register(NoticeCategory)
class NoticeCategoryAdmin(admin.ModelAdmin):
    list_display = ('noticeList', 'category',)
    list_filter = ('noticeList',)
    list_display_links = ('noticeList', 'category',)


@admin.register(NoticeSubject)
class NoticeSubjectAdmin(admin.ModelAdmin):
    list_display = ('noticeCategory', 'subject', 'color',)
    list_filter = ('noticeCategory',)
    list_display_links = ('noticeCategory', 'subject', 'color',)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('noticeCategory', 'title', 'author', 'updated',)
    list_filter = ('author',)
    list_display_links = ('noticeCategory', 'title', 'author', 'updated',)


@admin.register(NoticeFile)
class NoticeFileAdmin(admin.ModelAdmin):
    list_display = ('notice', 'fileName', 'fileSize',)
    list_filter = ('notice',)
    list_display_links = ('notice', 'fileName', 'fileSize',)


@admin.register(NoticeComment)
class NoticeCommentAdmin(admin.ModelAdmin):
    list_display = ('notice', 'author', 'comment', 'updated',)
    list_filter = ('notice',)
    list_display_links = ('notice', 'author', 'comment', 'updated',)


@admin.register(NoticeTag)
class NoticeTagAdmin(admin.ModelAdmin):
    list_display = ('notice', 'tag',)
    list_filter = ('notice',)
    list_display_links = ('notice', 'tag',)
