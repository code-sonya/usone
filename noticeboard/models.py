from django.db import models
from service.models import Servicereport


class Serviceboard(models.Model):
    serviceTypeChoices = (
        ('교육', '교육'),
        ('마이그레이션', '마이그레이션'),
        ('모니터링', '모니터링'),
        ('미팅&회의', '미팅&회의'),
        ('백업&복구', '백업&복구'),
        ('상주', '상주'),
        ('설치&패치', '설치&패치'),
        ('원격지원', '원격지원'),
        ('일반작업지원', '일반작업지원'),
        ('장애지원', '장애지원'),
        ('정기점검', '정기점검'),
        ('튜닝', '튜닝'),
        ('프로젝트', '프로젝트'),
        ('프리세일즈', '프리세일즈'),
        ('휴가', '휴가')
    )

    serviceBoardId = models.AutoField(primary_key=True)
    serviceId = models.ForeignKey(Servicereport, on_delete=models.CASCADE)
    serviceDate = models.DateField()
    companyName = models.CharField(max_length=100)
    serviceType = models.CharField(max_length=30, choices=serviceTypeChoices)
    empDeptName = models.CharField(max_length=30)
    empName = models.CharField(max_length=10)
    serviceBoardWriter = models.CharField(max_length=10)
    serviceBoardTitle = models.CharField(max_length=200, help_text="제목을 작성해 주세요.")
    serviceBoardDetails = models.TextField(help_text="상세 내용을 작성해 주세요.")
    serviceBoardFiles = models.FileField(null=True, blank=True)
    serviceBoardWriteDatetime = models.DateTimeField()
    serviceBoardEditDatetime = models.DateTimeField()

    def __str__(self):
        return 'Serviceboard : {} {}'.format(self.serviceBoardWriter, self.serviceBoardTitle)


class Board(models.Model):
    boardId = models.AutoField(primary_key=True)
    boardWriter = models.CharField(max_length=10)
    boardTitle = models.CharField(max_length=200, help_text="제목을 작성해 주세요.")
    boardDetails = models.TextField(help_text="상세 내용을 작성해 주세요.")
    boardFiles = models.FileField(null=True, blank=True)
    boardWriteDatetime = models.DateTimeField()
    boardEditDatetime = models.DateTimeField()

    def __str__(self):
        return 'Board : {} {}'.format(self.boardWriter, self.boardTitle)
