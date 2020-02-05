from django.db import models
from hr.models import Employee
from django.utils import timezone

class Center(models.Model):
    centerId = models.AutoField(primary_key=True)
    centerName = models.CharField(max_length=30)
    centerStatus = models.CharField(max_length=10, default='Y')

    def __str__(self):
        return str(self.centerId)


class CenterManager(models.Model):
    centerManagerId = models.AutoField(primary_key=True)
    writeEmp = models.ForeignKey(Employee, on_delete=models.CASCADE)
    createdDatetime = models.DateTimeField(default=timezone.now)
    startDate = models.DateField(null=True, blank=True)
    endDate = models.DateField(null=True, blank=True)
    centerManagerStatus = models.CharField(max_length=10, default='Y')

    def __str__(self):
        return str(self.centerManagerId)


class CenterManagerEmp(models.Model):
    managerId = models.AutoField(primary_key=True)
    centerManagerId = models.ForeignKey(CenterManager, null=True, blank=True, on_delete=models.CASCADE)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    manageArea = models.ForeignKey(Center, null=True, blank=True, on_delete=models.SET_NULL, related_name='manageArea')
    additionalArea = models.CharField(max_length=30, null=True, blank=True)
    cleanupArea = models.ForeignKey(Center, null=True, blank=True, on_delete=models.SET_NULL, related_name='cleanupArea')

    def __str__(self):
        return str(self.managerId)
