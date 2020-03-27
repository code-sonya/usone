# -*- coding: utf-8 -*-
from django.db import models
from service.models import Servicereport
from hr.models import Employee


class Board(models.Model):
    boardId = models.AutoField(primary_key=True)
    boardWriter = models.ForeignKey(Employee, on_delete=models.CASCADE)
    serviceId = models.ForeignKey(Servicereport, on_delete=models.CASCADE, null=True, blank=True)
    boardTitle = models.CharField(max_length=200, help_text="제목을 작성해 주세요.")
    boardDetails = models.TextField(help_text="상세 내용을 작성해 주세요.")
    boardFiles = models.FileField(null=True, blank=True, upload_to="board/%Y_%m")
    boardWriteDatetime = models.DateTimeField()
    boardEditDatetime = models.DateTimeField()

    def __str__(self):
        return 'Board : {} {}'.format(self.boardWriter, self.boardTitle)


class NoticeList(models.Model):
    list = models.CharField(max_length=200)


class NoticeCategory(models.Model):
    noticeList = models.ForeignKey(NoticeList, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=200)


class NoticeSubject(models.Model):
    noticeCategory = models.ForeignKey(NoticeCategory, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.CharField(max_length=200)
    color = models.CharField(max_length=50,)


class Notice(models.Model):
    approvalFormatChoices = (('Y', '상단노출'), ('N', '해당없음'),)

    noticeCategory = models.ForeignKey(NoticeCategory, on_delete=models.SET_NULL, null=True, blank=True)
    noticeSubject = models.ForeignKey(NoticeSubject, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    topExposure = models.CharField(max_length=10, choices=approvalFormatChoices, default='N')
    views = models.IntegerField(default=0)
    title = models.CharField(max_length=200)
    contents = models.TextField()
    thumbnail = models.ImageField(upload_to="notice/thumbnail/%Y_%m", max_length=200)


class NoticeFile(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)
    file = models.FileField(upload_to="notice/file/%Y_%m")
    fileName = models.CharField(max_length=200)
    fileSize = models.FloatField()


class NoticeComment(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)
    author = models.ForeignKey(Employee, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    comment = models.TextField()


class NoticeTag(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)
    tag = models.CharField(max_length=200)
