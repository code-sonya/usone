from django.db import models
from hr.models import Employee

class OverHour(models.Model):
    overHourId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    empName = models.CharField(max_length=10)
    overHourDate = models.DateField()
    sumOverHour = models.FloatField(null=True, blank=True)
    compensatedHour = models.FloatField(null=True, blank=True)

    def __str__(self):
        return str(self.overHourId)
