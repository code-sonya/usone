from django.db import models
from hr.models import Employee


class ExtraPay(models.Model):
    extraPayId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    empName = models.CharField(max_length=10)
    overHourDate = models.DateField(null=True, blank=True)
    sumOverHour = models.FloatField(null=True, blank=True)
    compensatedHour = models.FloatField(null=True, blank=True)
    compensatedComment = models.CharField(max_length=30, null=True, blank=True)
    payHour = models.FloatField(null=True, blank=True)
    payStatus = models.CharField(max_length=10, default='N')

    def __str__(self):
        return str(self.extraPayId)


class OverHour(models.Model):
    overHourId = models.AutoField(primary_key=True)
    serviceId = models.ForeignKey("service.Servicereport", on_delete=models.CASCADE, null=True, blank=True)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True)
    empName = models.CharField(max_length=10, null=True, blank=True)
    overHourStartDate = models.DateTimeField(null=True, blank=True)
    overHourEndDate = models.DateTimeField(null=True, blank=True)
    overHour = models.FloatField(null=True, blank=True)
    overHourWeekDay = models.FloatField(null=True, blank=True)
    overHourCost = models.FloatField(null=True, blank=True)
    overHourCostWeekDay = models.FloatField(null=True, blank=True)
    foodCost = models.FloatField(null=True, blank=True)
    comment = models.CharField(max_length=30, null=True, blank=True)
    extraPayId = models.ForeignKey(ExtraPay, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.overHourId)


class Car(models.Model):
    carId = models.AutoField(primary_key=True)
    oilType = models.CharField(max_length=10)
    carType = models.CharField(max_length=10)
    comment = models.CharField(max_length=20, null=True, blank=True)
    kpl = models.FloatField()

    def __str__(self):
        return self.oilType + ', ' + self.carType


class Oil(models.Model):
    oilId = models.AutoField(primary_key=True)
    oilDate = models.DateField()
    carId = models.ForeignKey(Car, on_delete=models.CASCADE)
    oilMoney = models.FloatField()
    mpk = models.IntegerField()

    def __str__(self):
        return str(self.oilDate) + ', ' + str(self.carId)


class Fuel(models.Model):
    fuelId = models.AutoField(primary_key=True)
    serviceId = models.ForeignKey("service.Servicereport", on_delete=models.CASCADE)
    distance1 = models.FloatField(default=0)
    distance2 = models.FloatField(default=0)
    distance3 = models.FloatField(default=0)
    totalDistance = models.FloatField()
    fuelMoney = models.IntegerField(null=True, blank=True)
    fuelStatus = models.CharField(max_length=1, default='N')

    def __str__(self):
        return str(self.fuelId)
