from django.contrib import admin
from .models import Book, Bookrental


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
