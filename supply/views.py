import json

from django.shortcuts import render, HttpResponse, redirect
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import Book, Bookrental


@login_required
@csrf_exempt
def show_rentals(request):
    context = {}
    return render(request, 'supply/showrentals.html', context)


@login_required
@csrf_exempt
def rentals_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    status = request.POST['status']
    renter = request.POST['renter']

    rentals = Bookrental.objects.all()
    if startdate:
        rentals = rentals.filter(rentDate__gte=startdate)
    if enddate:
        rentals = rentals.filter(rentDate__lte=enddate)
    if status:
        if status == 'Y':
            rentals = rentals.filter(returnDate__isnull=False)
        elif status == 'N':
            rentals = rentals.filter(returnDate__isnull=True)
    if renter:
        rentals = rentals.filter(renter__empName__icontains=renter)
    result = rentals.values(
        'rentDate', 'bookId__name', 'bookId__author', 'bookId__publisher', 'renter__empName',
        'returnDate', 'comment', 'rentalId'
    )
    structure = json.dumps(list(result), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_book(request):
    if request.method == 'POST':
        if Book.objects.filter(name=request.POST['name']):
            result = 'N'
        else:
            Book.objects.create(
                name=request.POST['name'],
                author=request.POST['author'],
                publisher=request.POST['publisher'],
            )
            result = 'Y'

        structure = json.dumps(result, cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')
