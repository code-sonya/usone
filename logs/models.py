from django.db import models
from hr.models import Employee
from sales.models import Contract


class DownloadLog(models.Model):
    downloadLogId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    downloadDatetime = models.DateTimeField()
    downloadType = models.CharField(max_length=50, null=True, blank=True)
    downloadUrl = models.CharField(max_length=100)

    def __str__(self):
        return str(self.downloadLogId)

class OrderLog(models.Model):
    orderLogId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    toEmail = models.CharField(max_length=50)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    orderDatetime = models.DateTimeField()
    orderUrl = models.CharField(max_length=100)

    def __str__(self):
        return str(self.orderLogId)


class ApprovalLog(models.Model):
    approvalLogId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    toEmail = models.CharField(max_length=50)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    approvalDatetime = models.DateTimeField()
    approvalUrl = models.CharField(max_length=100)

    def __str__(self):
        return str(self.approvalLogId)