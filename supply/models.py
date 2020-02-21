from django.db import models
from hr.models import Employee
from client.models import Company, Customer
from sales.models import Contract
from extrapay.models import OverHour
from daesungwork.models import Center


class Book(models.Model):
    statusChoices = (('Y', 'Y'), ('N', 'N'))

    bookId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    author = models.CharField(max_length=100)
    publisher = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=statusChoices, default='Y')
    rentalId = models.ForeignKey('Bookrental', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class Bookrental(models.Model):
    rentalId = models.AutoField(primary_key=True)
    bookId = models.ForeignKey(Book, on_delete=models.CASCADE)
    renter = models.ForeignKey(Employee, on_delete=models.CASCADE)
    rentDate = models.DateField(auto_now_add=True)
    returnDate = models.DateField(null=True, blank=True)
    predictReturnDate = models.DateField(null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return str(self.renter.empName) + ', ' + str(self.bookId.name)


class Saving(models.Model):
    savingId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    # quantity = models.IntegerField(default=0)
    # money = models.BigIntegerField(default=0)

    def __str__(self):
        return self.name


class SavingQuantity(models.Model):
    quantityId = models.AutoField(primary_key=True)
    savingId = models.ForeignKey(Saving, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    money = models.BigIntegerField(default=0)
    standard = models.CharField(max_length=100, null=True, blank=True)
    purchaseCompany = models.CharField(max_length=100, null=True, blank=True)
    purchaseDate = models.DateField(null=True, blank=True)
    location = models.ForeignKey(Center, null=True, blank=True, on_delete=models.SET_NULL, related_name='location')
    purchaseEmp = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.savingId.name
