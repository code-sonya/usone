from django.db import models

from hr.models import Employee


class AppToken(models.Model):
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    token = models.CharField(max_length=254)

    def __str__(self):
        return self.empId.empName
