from django.db import models
from hr.models import Employee
from sales.models import Contract, Purchaseorder
from approval.models import Document


class DownloadLog(models.Model):
    downloadLogId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    contractId = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True)
    downloadDatetime = models.DateTimeField()
    downloadType = models.CharField(max_length=50, null=True, blank=True)
    downloadName = models.CharField(max_length=100, null=True, blank=True)
    downloadUrl = models.CharField(max_length=100)

    def __str__(self):
        return str(self.downloadLogId)


class OrderLog(models.Model):
    orderLogId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    toEmail = models.CharField(max_length=50)
    orderId = models.ForeignKey(Purchaseorder, on_delete=models.CASCADE)
    orderDatetime = models.DateTimeField()
    orderStatus = models.CharField(max_length=20, default='전송성공')
    orderError = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return str(self.orderLogId)


class ApprovalLog(models.Model):
    approvalLogId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    toEmail = models.CharField(max_length=50)
    documentId = models.ForeignKey(Document, on_delete=models.CASCADE)
    approvalDatetime = models.DateTimeField()
    approvalStatus = models.CharField(max_length=20, default='전송성공')
    approvalError = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return str(self.approvalLogId)


class ContractLog(models.Model):
    logId = models.AutoField(primary_key=True)
    datetime = models.DateTimeField(auto_now=True)
    empId = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    contractId = models.ForeignKey(Contract, on_delete=models.CASCADE)
    changeCount = models.IntegerField(default=1)
    beforeSalePrice = models.BigIntegerField()
    beforeProfitPrice = models.BigIntegerField()
    beforeProfitRatio = models.FloatField()
    afterSalePrice = models.BigIntegerField()
    afterProfitPrice = models.BigIntegerField()
    afterProfitRatio = models.FloatField()
    diffSalePrice = models.BigIntegerField()
    diffProfitPrice = models.BigIntegerField()
    diffProfitRatio = models.FloatField()

    def __str__(self):
        return self.contractId.contractName
