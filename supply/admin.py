from django.contrib import admin
from .models import Book, Bookrental, Saving, SavingQuantity


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('bookId', 'name', 'author', 'publisher', 'status')
    list_filter = ('publisher', 'status',)
    list_display_links = ['bookId', 'name', 'author', 'publisher', 'status']


@admin.register(Bookrental)
class BookrentalAdmin(admin.ModelAdmin):
    list_display = ('rentalId', 'bookId', 'renter', 'rentDate')
    list_filter = ('renter',)
    list_display_links = ['rentalId', 'bookId', 'renter', 'rentDate']


@admin.register(Saving)
class SavingAdmin(admin.ModelAdmin):
    list_display = ('savingId', 'name')
    list_filter = ('name',)
    list_display_links = ['savingId', 'name']


@admin.register(SavingQuantity)
class SavingQuantityAdmin(admin.ModelAdmin):
    list_display = ('quantityId', 'savingId', 'quantity', 'purchaseDate')
    list_filter = ('savingId',)
    list_display_links = ['quantityId', 'savingId', 'quantity', 'purchaseDate']
