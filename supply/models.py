from django.db import models
from hr.models import Employee
from client.models import Company, Customer
from sales.models import Contract
from extrapay.models import OverHour


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
