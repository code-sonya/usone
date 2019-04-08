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
