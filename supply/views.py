import json
from datetime import datetime, timedelta

from django.shortcuts import render, HttpResponse, redirect
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, FloatField, F, Case, When, Count, Q, Min, Max, Value, CharField

from .models import Book, Bookrental, Saving, SavingQuantity
from hr.models import Employee


@login_required
@csrf_exempt
def show_rentals(request):
    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        renterDept = request.POST['renterDept']
        renterName = request.POST['renterName']
    else:
        startdate = ''
        enddate = ''
        renterDept = ''
        renterName = ''

    # 보유도서
    allBook = Book.objects.all().count()
    # 대출도서
    rentalBook = Book.objects.filter(status='N').count()
    # 연체도서
    overdueBook = Book.objects.filter(status='N', rentalId__predictReturnDate__lte=datetime.today()).count()

    context = {
        'startdate': startdate,
        'enddate': enddate,
        'renterDept': renterDept,
        'renterName': renterName,
        'allBook': allBook,
        'rentalBook': rentalBook,
        'overdueBook': overdueBook,
    }
    return render(request, 'supply/showrentals.html', context)


@login_required
@csrf_exempt
def rentals_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    renterDept = request.POST['renterDept']
    renterName = request.POST['renterName']

    rentals = Bookrental.objects.all()
    if startdate:
        rentals = rentals.filter(rentDate__gte=startdate)
    if enddate:
        rentals = rentals.filter(rentDate__lte=enddate)
    if renterDept:
        rentals = rentals.filter(renter__empDeptName__icontains=renterDept)
    if renterName:
        rentals = rentals.filter(renter__empName__icontains=renterName)
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


@login_required
def post_rentals(request):
    context = {}
    return render(request, 'supply/postrentals.html', context)


@login_required
@csrf_exempt
def books_asjson(request):
    books = Book.objects.all()
    result = books.values(
        'bookId', 'name', 'author', 'publisher', 'status', 'rentalId__predictReturnDate', 'rentalId__renter__empId',
    )
    structure = json.dumps(list(result), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_rent(request):
    if request.method == 'POST':

        if request.POST['type'] == 'rent':
            returnDate = timedelta(days=14)

            book = Book.objects.get(bookId=request.POST['bookId'])

            rental = Bookrental.objects.create(
                bookId=book,
                renter=request.user.employee,
                predictReturnDate=datetime.today() + returnDate,
            )

            book.status = 'N'
            book.rentalId = rental
            book.save()

        elif request.POST['type'] == 'return':
            book = Book.objects.get(bookId=request.POST['bookId'])

            rental = Bookrental.objects.get(rentalId=book.rentalId.rentalId)
            rental.returnDate = datetime.today()
            rental.save()

            book.status = 'Y'
            book.rentalId = None
            book.save()

        return redirect('supply:postrentals')


@login_required
def show_savings(request):
    emps = Employee.objects.filter(empStatus='Y')
    savings = Saving.objects.all()

    context = {
        'emps': emps,
        'savings': savings,
    }
    return render(request, 'supply/showsavings.html', context)


@login_required
@csrf_exempt
def savings_asjson(request):
    result = []

    savings = Saving.objects.all()
    for saving in savings:
        quantity = SavingQuantity.objects.filter(savingId=saving)
        quantity = quantity.order_by('-purchaseDate', '-quantityId').first()
        result.append(
            {
                'savingId': saving.savingId,
                'name': saving.name,
                'quantity': quantity.quantity,
                'standard': quantity.standard,
                'purchaseCompany': quantity.purchaseCompany,
                'location': quantity.location,
                'purchaseDate': quantity.purchaseDate,
                'purchaseEmp__empName': quantity.purchaseEmp.empName,
                'comment': quantity.comment,
            }
        )
    structure = json.dumps(list(result), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_saving(request):
    if request.method == 'POST':
        if request.POST['newSaving'] == 'true':
            newSaving = True
        elif request.POST['newSaving'] == 'false':
            newSaving = False
        else:
            result = 'error'
            structure = json.dumps(result, cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')

        if newSaving:
            if Saving.objects.filter(name=request.POST['name']):
                result = 'N'
            else:
                savingId = Saving.objects.create(name=request.POST['name'])
                SavingQuantity.objects.create(
                    savingId=savingId,
                    quantity=request.POST['quantity'],
                    standard=request.POST['standard'],
                    purchaseCompany=request.POST['purchaseCompany'],
                    purchaseDate=request.POST['purchaseDate'] or None,
                    location=request.POST['location'],
                    purchaseEmp=Employee.objects.get(empId=request.POST['purchaseEmp']),
                    comment=request.POST['comment'],
                )
                result = 'Y'

        else:
            savingId = Saving.objects.get(savingId=request.POST['name'])
            SavingQuantity.objects.create(
                savingId=savingId,
                quantity=request.POST['quantity'],
                standard=request.POST['standard'],
                purchaseCompany=request.POST['purchaseCompany'],
                purchaseDate=request.POST['purchaseDate'] or None,
                location=request.POST['location'],
                purchaseEmp=Employee.objects.get(empId=request.POST['purchaseEmp']),
                comment=request.POST['comment'],
            )
            result = 'Y'

        structure = json.dumps(result, cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
def view_saving(request, savingId):
    saving = Saving.objects.get(savingId=savingId)
    quantity = SavingQuantity.objects.filter(savingId__savingId=savingId).order_by('-purchaseDate', '-quantityId')
    lastQuantity = quantity.first()
    emps = Employee.objects.filter(empStatus='Y')

    context = {
        'saving': saving,
        'quantity': quantity,
        'lastQuantity': lastQuantity,
        'emps': emps,
    }
    return render(request, 'supply/viewsaving.html', context)


@login_required
def delete_saving(request, savingId):
    Saving.objects.get(savingId=savingId).delete()

    return redirect("supply:showsavings")