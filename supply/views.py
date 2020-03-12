import json
from datetime import datetime, timedelta

from django.shortcuts import render, HttpResponse, redirect
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, FloatField, F, Case, When, Count, Q, Min, Max, Value, CharField

from .models import Book, Bookrental, Saving, SavingQuantity
from hr.models import Employee
from daesungwork.models import Center


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
        'rentDate', 'bookId__name', 'bookId__author', 'bookId__publisher', 'bookId__code',
        'renter__empName', 'returnDate', 'comment', 'rentalId'
    )
    structure = json.dumps(list(result), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_book(request):
    if request.method == 'POST':
        if Book.objects.filter(name=request.POST['name']):
            codeNumber = Book.objects.filter(name=request.POST['name']).count() + 1
        else:
            codeNumber = 1
        code = int(request.POST['code'])
        for i in range(code):
            Book.objects.create(
                name=request.POST['name'],
                author=request.POST['author'],
                publisher=request.POST['publisher'],
                code='#' + str(codeNumber)
            )
            codeNumber += 1
        result = 'Y'

        structure = json.dumps(result, cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
def modify_book(request):
    if request.method == 'POST':
        book = Book.objects.get(bookId=request.POST['bookId'])
        book.name = request.POST['name']
        book.author = request.POST['author']
        book.publisher = request.POST['publisher']
        book.code = request.POST['code']
        book.save()
        result = 'Y'

        structure = json.dumps(result, cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
def delete_book(request):
    if request.method == 'POST':
        book = Book.objects.get(bookId=request.POST['bookId'])
        book.delete()
        result = 'Y'

        structure = json.dumps(result, cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
def show_books(request):
    # 보유도서
    allBook = Book.objects.all().count()
    # 대출도서
    rentalBook = Book.objects.filter(status='N').count()
    # 연체도서
    overdueBook = Book.objects.filter(status='N', rentalId__predictReturnDate__lte=datetime.today()).count()

    context = {
        'allBook': allBook,
        'rentalBook': rentalBook,
        'overdueBook': overdueBook,
    }
    return render(request, 'supply/showbooks.html', context)


@login_required
def post_rentals(request):
    context = {}
    return render(request, 'supply/postrentals.html', context)


@login_required
@csrf_exempt
def books_asjson(request):
    books = Book.objects.all()
    result = books.values(
        'bookId', 'name', 'author', 'publisher', 'code', 'status', 'rentalId__predictReturnDate', 'rentalId__renter__empId',
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
@csrf_exempt
def show_savings(request):
    emps = Employee.objects.filter(empStatus='Y')
    savings = Saving.objects.all()
    centers = Center.objects.filter(centerStatus='Y')
    if centers:
        if request.method == "POST":
            if request.POST['centerId']:
                centerId = int(request.POST['centerId'])
            else:
                centerId = ''
        else:
            centerId = ''
        context = {
            'emps': emps,
            'savings': savings,
            'centers': centers,
            'centerId': centerId,
        }
        return render(request, 'supply/showsavings.html', context)
    else:
        return redirect('daesungwork:showcenters')


@login_required
@csrf_exempt
def savings_asjson(request):
    quantity = SavingQuantity.objects.all()
    centerId = request.POST['centerId']
    if centerId:
        quantity = quantity.filter(location=centerId)
    quantity = quantity.values('savingId', 'savingId__name').annotate(quantity=Sum('quantity'), money=Sum('money'))

    structure = json.dumps(list(quantity), cls=DjangoJSONEncoder)
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
                savingId = Saving.objects.create(
                    name=request.POST['name'],
                )
                SavingQuantity.objects.create(
                    savingId=savingId,
                    quantity=request.POST['quantity'],
                    money=request.POST['money'],
                    standard=request.POST['standard'],
                    purchaseCompany=request.POST['purchaseCompany'],
                    purchaseDate=request.POST['purchaseDate'] or None,
                    location=Center.objects.get(Q(centerStatus='Y') & Q(centerId=request.POST['location'])),
                    purchaseEmp=Employee.objects.get(empId=request.POST['purchaseEmp']),
                    comment=request.POST['comment'],
                )
                result = 'Y'

        else:
            savingId = Saving.objects.get(savingId=request.POST['name'])
            SavingQuantity.objects.create(
                savingId=savingId,
                quantity=request.POST['quantity'],
                money=request.POST['money'],
                standard=request.POST['standard'],
                purchaseCompany=request.POST['purchaseCompany'],
                purchaseDate=request.POST['purchaseDate'] or None,
                location=Center.objects.get(Q(centerStatus='Y') & Q(centerId=request.POST['location'])),
                purchaseEmp=Employee.objects.get(empId=request.POST['purchaseEmp']),
                comment=request.POST['comment'],
            )
            result = 'Y'

        structure = json.dumps(result, cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
def view_saving(request, savingId, centerId):
    saving = Saving.objects.get(savingId=savingId)
    quantity = SavingQuantity.objects.filter(savingId__savingId=savingId).order_by('-purchaseDate', '-quantityId')
    emps = Employee.objects.filter(empStatus='Y')
    if centerId != '전체':
        quantity = quantity.filter(location=centerId)

    sumQuantity = quantity.aggregate(quantity=Sum('quantity'), money=Sum('money'))
    context = {
        'saving': saving,
        'quantity': quantity,
        'sumQuantity': sumQuantity,
        'emps': emps,
    }
    return render(request, 'supply/viewsaving.html', context)


@login_required
def delete_saving(request, savingId):
    Saving.objects.get(savingId=savingId).delete()

    return redirect("supply:showsavings")