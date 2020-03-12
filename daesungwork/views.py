from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from hr.models import Employee, Authorization
from client.models import Company
from .models import Center, CenterManager, CenterManagerEmp, CheckList, ConfirmCheckList, Affiliate, Product, Size, Warehouse, \
    WarehouseMainCategory, WarehouseSubCategory, Sale, DailyReport, Display, Reproduction, Type, Buy, StockCheck, ProductCheck, StockManagement
from .forms import CenterManagerForm, SaleForm, ProductForm, WarehouseForm, DailyReportForm, DisplayForm, ReproductionForm, BuyForm, StockManagementForm
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, FloatField, F, Case, When, Count, Q, Min, Max, Value, CharField, IntegerField
import json
import datetime
from dateutil.relativedelta import relativedelta
from xhtml2pdf import pisa
from service.functions import link_callback
import calendar
import json


@login_required
def show_displaystatus(request):
    template = loader.get_template('daesungwork/showdisplaystatus.html')
    products = Product.objects.filter(productStatus='Y')
    form = DisplayForm()

    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        filterProduct = request.POST['filterProduct']
        filterSize = request.POST['filterSize']
    else:
        startdate = ''
        enddate = ''
        filterProduct = ''
        filterSize = ''

    context = {
        'form': form,
        'products': products,
        'startdate': startdate,
        'enddate': enddate,
        'filterProduct': filterProduct,
        'filterSize': filterSize,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def post_display(request):
    if request.method == 'POST':
        form = DisplayForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('daesungwork:showdisplaystatus')
        else:
            return HttpResponse("유효하지 않은 형식입니다. 관리자에게 문의하세요 :(")


@login_required
@csrf_exempt
def display_asjson(request):
    displays = Display.objects.all()

    if request.POST['startdate']:
        displays = displays.filter(postDate__gte=request.POST['startdate'])
    if request.POST['enddate']:
        displays = displays.filter(postDate__lte=request.POST['enddate'])
    if request.POST['filterProduct']:
        displays = displays.filter(product__modelName__icontains=request.POST['filterProduct'])
    if request.POST['filterSize']:
        displays = displays.filter(size__size__icontains=request.POST['filterSize'])

    displays = displays.values(
        'displayId', 'postDate', 'product__modelName', 'size__size', 'quantity', 'comment'
    )
    structure = json.dumps(list(displays), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def delete_display(request, displayId):
    display = Display.objects.get(displayId=displayId)
    display.delete()
    return redirect('daesungwork:showdisplaystatus')


@login_required
@csrf_exempt
def insert_display(request):
    postDate = request.POST['postDate']
    jsonDisplay = json.loads(request.POST['jsonDisplay'])
    for display in jsonDisplay:
        Display.objects.create(
            postDate=postDate,
            product=Product.objects.get(productId=int(display['product'])),
            size=Size.objects.get(sizeId=int(display['size'])),
            quantity=int(display['quantity']),
            comment=display['comment'] or '',
        )
    return redirect('daesungwork:showdisplaystatus')


@login_required
def show_reproductionstatus(request):
    template = loader.get_template('daesungwork/showreproductionstatus.html')
    products = Product.objects.filter(productStatus='Y')
    form = ReproductionForm()

    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        filterProduct = request.POST['filterProduct']
        filterSize = request.POST['filterSize']
    else:
        startdate = ''
        enddate = ''
        filterProduct = ''
        filterSize = ''

    context = {
        'form': form,
        'products': products,
        'startdate': startdate,
        'enddate': enddate,
        'filterProduct': filterProduct,
        'filterSize': filterSize,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def post_reproduction(request):
    if request.method == 'POST':
        form = ReproductionForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('daesungwork:showreproductionstatus')
        else:
            return HttpResponse("유효하지 않은 형식입니다. 관리자에게 문의하세요 :(")


@login_required
@csrf_exempt
def reproduction_asjson(request):
    reproductions = Reproduction.objects.all()

    if request.POST['startdate']:
        reproductions = reproductions.filter(postDate__gte=request.POST['startdate'])
    if request.POST['enddate']:
        reproductions = reproductions.filter(postDate__lte=request.POST['enddate'])
    if request.POST['filterProduct']:
        reproductions = reproductions.filter(product__modelName__icontains=request.POST['filterProduct'])
    if request.POST['filterSize']:
        reproductions = reproductions.filter(size__size__icontains=request.POST['filterSize'])

    reproductions = reproductions.values(
        'reproductionId', 'postDate', 'product__modelName', 'size__size', 'quantity', 'comment'
    )
    structure = json.dumps(list(reproductions), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def delete_reproduction(request, reproductionId):
    reproduction = Reproduction.objects.get(reproductionId=reproductionId)
    reproduction.delete()
    return redirect('daesungwork:showreproductionstatus')


@login_required
@csrf_exempt
def insert_reproduction(request):
    postDate = request.POST['postDate']
    jsonReproduction = json.loads(request.POST['jsonReproduction'])
    for reproduction in jsonReproduction:
        Reproduction.objects.create(
            postDate=postDate,
            product=Product.objects.get(productId=int(reproduction['product'])),
            size=Size.objects.get(sizeId=int(reproduction['size'])),
            quantity=int(reproduction['quantity']),
            comment=reproduction['comment'] or '',
        )
    return redirect('daesungwork:showreproductionstatus')


@login_required
@csrf_exempt
def show_buystatus(request):
    template = loader.get_template('daesungwork/showbuystatus.html')
    # 일간
    today = datetime.datetime.today()
    # 연간
    todayYear = today.year
    # 월간
    todayMonth = today.month
    # 주간
    thisMonday = today - datetime.timedelta(days=today.weekday())
    thisSunday = thisMonday + datetime.timedelta(days=6)

    form = BuyForm()

    buys = Buy.objects.all()
    clients = Company.objects.filter(companyStatus="Y")

    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        filterClient = request.POST['filterClient']
        filterProduct = request.POST['filterProduct']

        if startdate:
            buys = buys.filter(buyDate__gte=startdate)
        if enddate:
            buys = buys.filter(buyDate__lte=enddate)
        if filterClient:
            buys = buys.filter(client=filterClient)
        if filterProduct:
            buys = buys.filter(product__icontains=filterProduct)

    else:
        startdate = ''
        enddate = ''
        filterClient = ''
        filterProduct = ''

    buys = buys.aggregate(
        yearly=Sum(
            Case(
                When(buyDate__year=todayYear, then='totalPrice'),
                default=0, output_field=IntegerField()
            )
        ),
        monthly=Sum(
            Case(
                When(Q(buyDate__year=todayYear) & Q(buyDate__month=todayMonth), then='totalPrice'),
                default=0, output_field=IntegerField()
            )
        ),
        weekly=Sum(
            Case(
                When(Q(buyDate__gte=thisMonday) & Q(buyDate__lte=thisSunday), then='totalPrice'),
                default=0, output_field=IntegerField()
            )
        ),
        today=Sum(
            Case(
                When(buyDate=today, then='totalPrice'),
                default=0, output_field=IntegerField()
            )
        ),
        total=Sum('totalPrice'),
        count=Count('buyId'),
    )
    context = {
        'form': form,
        'buys': buys,
        'clients': clients,
        'startdate': startdate,
        'enddate': enddate,
        'filterClient': filterClient,
        'filterProduct': filterProduct,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def post_buy(request):
    form = BuyForm(request.POST)

    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect('daesungwork:showbuystatus')
    else:
        return HttpResponse("유효하지 않은 형식입니다. 관리자에게 문의하세요 : (")


@login_required
@csrf_exempt
def buys_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    filterClient = request.POST['filterClient']
    filterProduct = request.POST['filterProduct']

    buys = Buy.objects.all()
    if startdate:
        buys = buys.filter(buyDate__gte=startdate)
    if enddate:
        buys = buys.filter(buyDate__lte=enddate)
    if filterClient:
        buys = buys.filter(client=filterClient)
    if filterProduct:
        buys = buys.filter(product__icontains=filterProduct)

    buys = buys.values(
        'buyId', 'buyDate', 'client__companyName', 'product', 'quantity',
        'salePrice', 'vatPrice', 'totalPrice', 'comment',
    ).order_by('-buyDate')

    structure = json.dumps(list(buys), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def delete_buy(request, buyId):
    buy = Buy.objects.get(buyId=buyId)
    buy.delete()
    return redirect('daesungwork:showbuystatus')


@login_required
@csrf_exempt
def insert_buy(request):
    buyDate = request.POST['buyDate']
    client = request.POST['insertClient']

    jsonBuy = json.loads(request.POST['jsonBuy'])
    for buy in jsonBuy:
        Buy.objects.create(
            buyDate=buyDate,
            client=Company.objects.get(companyName=client),
            product=buy['product'],
            quantity=int(buy['quantity']),
            salePrice=int(buy['salePrice']),
            vatPrice=int(buy['vatPrice']),
            totalPrice=int(buy['totalPrice']),
            comment=buy['comment'] or '',
        )
    return redirect('daesungwork:showbuystatus')


@login_required
def show_centermanagers(request):
    template = loader.get_template('daesungwork/showcentermanagers.html')
    today = datetime.datetime.today()
    centermanager = CenterManager.objects.filter(Q(centerManagerStatus='Y') & Q(startDate__lte=today) & Q(endDate__gte=today)).order_by('-endDate').first()
    if centermanager:
        centermanageremps = CenterManagerEmp.objects.filter(centerManagerId=centermanager.centerManagerId)
    else:
        centermanageremps = None
    context = {
        'centermanager': centermanager,
        'centermanageremps': centermanageremps,
        'today': today,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def post_manager(request):
    template = loader.get_template('daesungwork/postmanager.html')
    if request.method == 'POST':
        form = CenterManagerForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.writeEmp = Employee.objects.get(empId=request.user.employee.empId)
            post.save()

            jsonManagerEmp = json.loads(request.POST['jsonManagerEmp'])

            for item in jsonManagerEmp:
                CenterManagerEmp.objects.create(
                    centerManagerId=post,
                    empId=Employee.objects.get(empId=item["empId"]),
                    manageArea=Center.objects.get(Q(centerName=item["manageArea"]) & Q(centerStatus='Y')),
                    additionalArea=item["additionalArea"],
                    cleanupArea=Center.objects.filter(Q(centerName=item["cleanupArea"]) & Q(centerStatus='Y')).first(),
                )

            return redirect('daesungwork:showcentermanagers')

    else:
        form = CenterManagerForm()
        context = {
            'form': form
        }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def modify_centermanager(request, centerManagerId):
    template = loader.get_template('daesungwork/postmanager.html')
    centerManagerInstance = CenterManager.objects.get(centerManagerId=centerManagerId)
    if request.method == 'POST':
        form = CenterManagerForm(request.POST, instance=centerManagerInstance)

        if form.is_valid():
            post = form.save(commit=False)
            post.writeEmp = Employee.objects.get(empId=request.user.employee.empId)
            post.save()

            jsonManagerEmp = json.loads(request.POST['jsonManagerEmp'])
            managerEmpId = list(i[0] for i in CenterManagerEmp.objects.filter(centerManagerId=centerManagerId).values_list('managerId'))
            jsonManagerEmpId = []
            for item in jsonManagerEmp:
                if item['centerManagerEmpId'] == '추가':
                    CenterManagerEmp.objects.create(
                        centerManagerId=post,
                        empId=Employee.objects.get(empId=item["empId"]),
                        manageArea=Center.objects.get(Q(centerName=item["manageArea"]) & Q(centerStatus='Y')),
                        additionalArea=item["additionalArea"],
                        cleanupArea=Center.objects.filter(Q(centerName=item["cleanupArea"]) & Q(centerStatus='Y')).first(),
                    )
                else:
                    managerEmpInstance = CenterManagerEmp.objects.get(managerId=int(item['centerManagerEmpId']))
                    managerEmpInstance.centerManagerId = post
                    managerEmpInstance.empId = Employee.objects.get(empId=item["empId"])
                    managerEmpInstance.manageArea = Center.objects.get(Q(centerName=item["manageArea"]) & Q(centerStatus='Y'))
                    managerEmpInstance.additionalArea = item["additionalArea"]
                    managerEmpInstance.cleanupArea = Center.objects.filter(Q(centerName=item["cleanupArea"]) & Q(centerStatus='Y')).first()
                    managerEmpInstance.save()
                    jsonManagerEmpId.append(int(item['centerManagerEmpId']))

            delManagerEmpId = list(set(managerEmpId) - set(jsonManagerEmpId))
            if delManagerEmpId:
                for Id in delManagerEmpId:
                    CenterManagerEmp.objects.filter(managerId=Id).delete()
            return redirect('daesungwork:showcentermanagers')
        else:
            return HttpResponse('유효하지 않은 형식입니다.')

    else:
        form = CenterManagerForm(instance=centerManagerInstance)
        centerManagerEmps = CenterManagerEmp.objects.filter(centerManagerId=centerManagerId)
        context = {
            'centerManagerId': centerManagerId,
            'form': form,
            'centerManagerEmps': centerManagerEmps,
        }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def center_asjson(request):
    centerManagerId = request.POST['centerManagerId']
    if centerManagerId:
        centers = Center.objects.filter(centerStatus='Y').values('centerName').order_by('centerName')
        employees = Employee.objects.filter(empStatus='Y').values('empName', 'empId').order_by('empId')
        centerManagerEmps = CenterManagerEmp.objects.filter(centerManagerId=centerManagerId)\
            .values('empId', 'empId__empName', 'manageArea__centerName', 'additionalArea', 'cleanupArea__centerName')
        jsonList = []
        jsonList.append(list(centers))
        jsonList.append(list(employees))
        jsonList.append(list(centerManagerEmps))

    else:
        centers = Center.objects.filter(centerStatus='Y').values('centerName').order_by('centerName')
        employees = Employee.objects.filter(empStatus='Y').values('empName', 'empId').order_by('empId')
        jsonList = []
        jsonList.append(list(centers))
        jsonList.append(list(employees))

    structure = json.dumps(jsonList, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def centermanager_asjson(request):
    centermanagers = CenterManager.objects.filter(centerManagerStatus='Y')\
        .values('centerManagerId', 'writeEmp__empName', 'startDate', 'endDate', 'createdDatetime').order_by('centerManagerId')
    structure = json.dumps(list(centermanagers), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_centermanager(request, centerManagerId):
    template = loader.get_template('daesungwork/viewcentermanager.html')
    centermanager = CenterManager.objects.get(centerManagerId=centerManagerId)
    centermanageremps = CenterManagerEmp.objects.filter(centerManagerId=centermanager.centerManagerId)
    context = {
        'centermanager': centermanager,
        'centermanageremps': centermanageremps,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def delete_centermanager(request, centerManagerId):
    centermanager = CenterManager.objects.get(centerManagerId=centerManagerId)
    centermanager.delete()
    return redirect('daesungwork:showcentermanagers')


@login_required
@csrf_exempt
def show_checklist(request):
    template = loader.get_template('daesungwork/showchecklist.html')
    checklist = CheckList.objects.filter(checkListStatus="Y").order_by('checkListId')
    confirmCheckList = ConfirmCheckList.objects.all()
    today = datetime.datetime.today()
    centers = Center.objects.filter(Q(centerStatus="Y"))

    # 등록된 센터 정보 있는지(ex.자수실, 비품실 등)
    if centers:
        # 등록된 점검 항목 목록이 있는지(ex. 소등상태, 냉난방기구 전원 등)
        if CheckList.objects.all():
            if request.method == 'POST':
                # 조회 기간
                searchDay = request.POST['searchDay']
                thisMonday = datetime.datetime(int(searchDay[:4]), int(searchDay[5:7]), int(searchDay[8:10]))
                thisSunday = thisMonday + datetime.timedelta(days=6)
                lastMonday = thisMonday - datetime.timedelta(days=7)
                nextMonday = thisMonday + datetime.timedelta(days=7)

                if request.user.is_staff:
                    employees = Employee.objects.filter(empStatus='Y')
                else:
                    # 담당한 센터가 있는지 확인
                    centermanager = CenterManagerEmp.objects.filter(Q(empId=request.user.employee.empId))
                    employees = Employee.objects.filter(empId=request.user.employee.empId)
                    centermanager = centermanager.filter(Q(centerManagerId__endDate__gte=thisMonday) & Q(centerManagerId__startDate__lte=thisSunday))
                    centers = centers.filter(centerId__in=centermanager.values_list('manageArea__centerId'))

                # 센터 정보
                centerName = request.POST['centerName']
                confirmCheckList = confirmCheckList.filter(centerId__centerName=centerName)
                confirmCheckList = confirmCheckList.filter(Q(confirmDate__gte=thisMonday) & Q(confirmDate__lte=thisSunday)).order_by('checkListId')

            else:
                # 조회 기간
                thisMonday = today - datetime.timedelta(days=today.weekday())
                thisSunday = thisMonday + datetime.timedelta(days=6)
                lastMonday = thisMonday - datetime.timedelta(days=7)
                nextMonday = thisMonday + datetime.timedelta(days=7)
                searchDay = thisMonday

                if request.user.is_staff:
                    employees = Employee.objects.filter(empStatus='Y')
                else:
                    # 담당한 센터가 있는지 확인
                    centermanager = CenterManagerEmp.objects.filter(Q(empId=request.user.employee.empId))
                    employees = Employee.objects.filter(empId=request.user.employee.empId)
                    centermanager = centermanager.filter(Q(centerManagerId__endDate__gte=thisMonday) & Q(centerManagerId__startDate__lte=thisSunday))
                    centers = centers.filter(centerId__in=centermanager.values_list('manageArea__centerId'))

                if centers:
                    # 센터 정보
                    centerName = centers.first().centerName
                    confirmCheckList = confirmCheckList.filter(centerId__centerName=centerName)
                    confirmCheckList = confirmCheckList.filter(Q(confirmDate__gte=thisMonday) & Q(confirmDate__lte=thisSunday)).order_by('checkListId')
                else:
                    return HttpResponse('배정받은 센터가 없어 접근이 불가능합니다. : (')

            cheklistDict = {}
            for check in checklist:
                cheklistDict[check.checkListId] = ''
            dateList = []
            for day in range(0, 7):
                data = confirmCheckList.filter(confirmDate=(thisMonday + relativedelta(days=day))).order_by('checkListId')
                dateList.append({'empName': data.values('empId__empName').first(),
                                 'confirmDate': (thisMonday + relativedelta(days=day)),
                                 'data': data})
            context = {
                'today': today,
                'thisMonday': thisMonday,
                'thisSunday': thisSunday,
                'lastMonday': lastMonday.date,
                'nextMonday': nextMonday.date,
                'centers': centers,
                'employees': employees,
                'checklist': checklist,
                'confirmCheckList': confirmCheckList,
                'dateList': dateList,
                'centerName': centerName,
                'searchDay': searchDay,
                'checklists': checklist,
            }
            return HttpResponse(template.render(context, request))
        else:
            return HttpResponse('점검 항목이 없습니다. 점검항목을 등록해 주세요.')
    else:
        return redirect('daesungwork:showcenters')

@login_required
@csrf_exempt
def post_checklist(request):
    if request.POST:
        centerName = request.POST['modalCenterName']
        modalEmpName = request.POST['modalEmpName']
        modalCheckDate = request.POST['modalCheckDate']
        centerId = Center.objects.get(Q(centerName=centerName) & Q(centerStatus='Y'))
        empId = Employee.objects.get(empId=modalEmpName)

        if CenterManagerEmp.objects.filter(Q(empId=empId) & Q(manageArea=centerId.centerId) & Q(centerManagerId__startDate__lte=modalCheckDate) & Q(centerManagerId__endDate__gte=modalCheckDate)) or empId.user.is_staff:
            jsonCheckList = json.loads(request.POST['jsonCheckList'])
            ConfirmCheckList.objects.filter(Q(confirmDate=modalCheckDate) & Q(centerId__centerName=centerName)).delete()
            for item in jsonCheckList:
                if item['checkListBox']:
                    checkListStatus = 'Y'
                else:
                    checkListStatus = 'N'

                file = None
                if item['checkListFiles']:
                    fileName = item['checkListFiles'].split('\\')[-1]
                    for f in request.FILES.getlist('checkListFiles'):
                        if f.name == fileName:
                            file = f
                            break

                ConfirmCheckList.objects.create(
                    centerId=centerId,
                    empId=empId,
                    confirmDate=modalCheckDate,
                    checkListId=CheckList.objects.get(checkListName=item['checkListName']),
                    checkListStatus=checkListStatus,
                    comment=item['checkListComment'],
                    file=file,
                )
            return redirect('daesungwork:showchecklist')
        else:
            return HttpResponse('{}는(은) {}에 {}의 담당자가 아닙니다. 담당자배정정보를 확인 해주세요.'.format(empId.empName, modalCheckDate, centerName))

    else:
        return HttpResponse('점검 항목이 없습니다. 점검항목을 등록해 주세요.')


@login_required
@csrf_exempt
def view_checklist_pdf(request, month):
    todayYear = month[:4]
    todayMonth = month[5:]
    centers = Center.objects.filter(centerStatus="Y")
    checklists = CheckList.objects.filter(checkListStatus="Y").order_by('checkListId')
    table = []
    for center in centers:
        for checklist in checklists:
            rowDict = {'centerName': center.centerName, 'checkListId': checklist.checkListId, 'checkListName': checklist.checkListName}
            confirmCheckList = ConfirmCheckList.objects.filter(Q(centerId=center.centerId) & Q(checkListId=checklist.checkListId))
            dateTuple = calendar.monthrange(int(todayYear), int(todayMonth))
            dateDict = []
            for date in range(1, dateTuple[1]+1):
                try:
                    dateDict.append(confirmCheckList.get(confirmDate='{}-{}-{}'.format(todayYear, todayMonth, date)).checkListStatus)
                except:
                    dateDict.append('-')
            rowDict['dateDict'] = dateDict
            table.append(rowDict)

    context = {
        'todayYear': todayYear,
        'todayMonth': todayMonth,
        'checklists': checklists,
        'table': table,
        'days':  range(1, dateTuple[1]+1)
    }
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{} 센터별 체크리스트.pdf"'.format(month)

    template = get_template('daesungwork/viewchecklistpdf.html')
    html = template.render(context, request)
    # create a pdf
    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@login_required
@csrf_exempt
def show_centers(request):
    template = loader.get_template('daesungwork/showcenters.html')
    if request.method == 'POST':
        centerName = request.POST['centerName']
        Center.objects.create(
            centerName=centerName.replace(" ", "")
        )
    centers = Center.objects.filter(centerStatus="Y")
    context = {
        "centers": centers,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def delete_center(request):
    if request.method == 'POST':
        try:
            centerId = request.POST.get('centerId', None)
            center = Center.objects.get(centerId=centerId)
            center.centerStatus = 'N'
            center.save()
            return redirect('daesungwork:showcenters')
        except Exception as e:
            print(e)
            return redirect('daesungwork:showcenters')
    else:
        print('else')
        return HttpResponse('오류발생! 관리자에게 문의하세요 :(')


@login_required
@csrf_exempt
def show_salestatus(request, affiliateId):
    template = loader.get_template('daesungwork/showsalestatus.html')
    # 일간
    today = datetime.datetime.today()
    # 연간
    todayYear = today.year
    # 월간
    todayMonth = today.month
    # 주간
    thisMonday = today - datetime.timedelta(days=today.weekday())
    thisSunday = thisMonday + datetime.timedelta(days=6)

    form = SaleForm()
    affiliates = Affiliate.objects.all()
    sales = Sale.objects.all()
    clients = Company.objects.filter(companyStatus="Y")
    products = Product.objects.filter(productStatus='Y')

    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        filterClient = request.POST['filterClient']
        filterProduct = request.POST['filterProduct']
        filterSize = request.POST['filterSize']

        if startdate:
            sales = sales.filter(saleDate__gte=startdate)

        if enddate:
            sales = sales.filter(saleDate__lte=enddate)

        if filterClient:
            sales = sales.filter(client=filterClient)

        if filterProduct:
            sales = sales.filter(product__modelName__icontains=filterProduct)

        if filterSize:
            # iexact - 대소문자 구별하지 않음.
            sales = sales.filter(size__size__iexact=filterSize)

    else:
        startdate = ''
        enddate = ''
        filterClient = ''
        filterProduct = ''
        filterSize = ''

    if affiliateId != 'all':
        affiliateId = int(affiliateId)
        sales = sales.filter(affiliate=affiliateId)

    sales = sales.aggregate(
        yearly=Sum(
                Case(
                    When(saleDate__year=todayYear, then='salePrice'),
                    default=0, output_field=IntegerField()
                    )
                ),
        monthly=Sum(
                Case(
                    When(Q(saleDate__year=todayYear) & Q(saleDate__month=todayMonth), then='salePrice'),
                    default=0, output_field=IntegerField()
                    )
                ),
        weekly=Sum(
            Case(
                When(Q(saleDate__gte=thisMonday) & Q(saleDate__lte=thisSunday), then='salePrice'),
                default=0, output_field=IntegerField()
            )
        ),
        today=Sum(
            Case(
                When(saleDate=today, then='salePrice'),
                default=0, output_field=IntegerField()
            )
        ),
        total=Sum('salePrice'),
        count=Count('saleId'),
    )
    context = {
        'form': form,
        'affiliates': affiliates,
        'affiliateId': affiliateId,
        'sales': sales,
        'clients': clients,
        'products': products,
        'startdate': startdate,
        'enddate': enddate,
        'filterClient': filterClient,
        'filterProduct': filterProduct,
        'filterSize': filterSize,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def show_products(request):
    template = loader.get_template('daesungwork/showproducts.html')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('daesungwork:showproducts')

    else:
        form = ProductForm()
        context = {
            'form': form,
        }
        return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def product_asjson(request):
    products = Product.objects.filter(productStatus='Y').values(
        'productId', 'modelName', 'productName', 'unitPrice', 'productPicture',
        'position__mainCategory__categoryName', 'position__subCategory__categoryName', 'typeName__typeName'
    ).order_by('productId')
    structure = json.dumps(list(products), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_product(request, productId):
    template = loader.get_template('daesungwork/viewproduct.html')
    instance = Product.objects.get(productId=productId)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=instance)
        post = form.save(commit=False)
        post.save()
        return redirect('daesungwork:viewproduct', productId)

    else:
        form = ProductForm(instance=instance)
        sizes = Size.objects.filter(productId=productId).order_by('size')
        if instance.position:
            warehouseImage = instance.position.warehouseDrawing
        else:
            warehouseImage = 'warehouse/noimage.png'

        context = {
            'form': form,
            'instance': instance,
            'sizes': sizes,
            'productId': productId,
            'productImage': instance.productPicture,
            'warehouseImage': warehouseImage,
        }

        return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def delete_product(request, productId):
    product = Product.objects.get(productId=productId)
    product.productStatus = 'N'
    product.save()
    return redirect('daesungwork:showproducts')


@login_required
@csrf_exempt
def delete_size(request, sizeId):
    size = Size.objects.get(sizeId=sizeId)
    productId = size.productId
    size.delete()
    return redirect('daesungwork:viewproduct', productId)



@login_required
@csrf_exempt
def post_size(request, productId):
    product = Product.objects.get(productId=productId)
    sizeList = request.POST['size']
    sizeList = sizeList.split(',')

    returnSize = []
    for size in sizeList:
        size = size.strip()
        sizes = Size.objects.filter(Q(productId=productId) & Q(size=size))
        if len(sizes) > 0:
            returnSize.append(size)
        else:
            Size.objects.create(
                productId=product,
                size=size
            )

    if returnSize:
        return HttpResponse(
            ', '.join(returnSize) + ' 사이즈는 이미 등록되어있습니다. 나머지 사이즈는 등록되었습니다.<br><br>' +
            '<a href="/daesungwork/viewproduct/' + productId + '" role="button">제품보기</a>'
        )
    else:
        return redirect('daesungwork:viewproduct', productId)


@login_required
@csrf_exempt
def show_warehouses(request):
    template = loader.get_template('daesungwork/showwarehouses.html')
    if request.method == 'POST':
        form = WarehouseForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            warehouses = Warehouse.objects.filter(Q(mainCategory__categoryName=post.mainCategory) & Q(subCategory__categoryName=post.subCategory))
            if len(warehouses) > 0:
                return HttpResponse("이미 등록된 섹션정보입니다.")
            else:
                post.save()
        else:
            return HttpResponse("유효하지 않은 형식입니다.")

        return redirect('daesungwork:showwarehouses')

    else:
        form = WarehouseForm()
        context = {
            'form': form,
        }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def warehouses_asjson(request):
    warehouses = Warehouse.objects.all()\
        .values('warehouseId', 'mainCategory__categoryName', 'subCategory__categoryName', 'warehouseDrawing').order_by('warehouseId')
    structure = json.dumps(list(warehouses), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def post_maincategory(request):
    categoryName = request.POST['mainCategoryName']
    maincategorys = WarehouseMainCategory.objects.filter(Q(categoryName=categoryName))

    if len(maincategorys) > 0:
        return HttpResponse("이미 등록된 창고명 입니다.")
    else:
        WarehouseMainCategory.objects.create(
            categoryName=categoryName
        )
        return redirect('daesungwork:showwarehouses')


@login_required
@csrf_exempt
def post_subcategory(request):
    categoryName = request.POST['subCategoryName']
    subcategorys = WarehouseSubCategory.objects.filter(Q(categoryName=categoryName))

    if len(subcategorys) > 0:
        return HttpResponse("이미 등록된 섹션명 입니다.")
    else:
        WarehouseSubCategory.objects.create(
            categoryName=categoryName
        )
        return redirect('daesungwork:showwarehouses')


@login_required
@csrf_exempt
def delete_warehouse(request, warehouseId):
    warehouse = Warehouse.objects.get(warehouseId=warehouseId)
    warehouse.delete()
    return redirect('daesungwork:showwarehouses')


@login_required
@csrf_exempt
def model_asjson(request):
    productId = request.POST['modelName']
    models = Product.objects.filter(productId=productId)\
        .values('productId', 'modelName', 'productName', 'unitPrice').order_by('productId')
    sizes = Size.objects.filter(productId=productId).order_by('size').values()

    jsonList = []
    jsonList.append(list(models))
    jsonList.append(list(sizes))
    structure = json.dumps(jsonList, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def sales_asjson(request):
    affiliateId = request.POST['affiliateId']
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    filterClient = request.POST['filterClient']
    filterProduct = request.POST['filterProduct']
    filterSize = request.POST['filterSize']

    sales = Sale.objects.all()
    if affiliateId != 'all':
        sales = sales.filter(affiliate=affiliateId)

    if startdate:
        sales = sales.filter(saleDate__gte=startdate)

    if enddate:
        sales = sales.filter(saleDate__lte=enddate)

    if filterClient:
        sales = sales.filter(client=filterClient)

    if filterProduct:
        sales = sales.filter(product__modelName__icontains=filterProduct)

    if filterSize:
        sales = sales.filter(size__size__iexact=filterSize)

    sales = sales.values('saleId', 'saleDate', 'product__productId', 'affiliate__affiliateName', 'client__companyName', 'product__modelName', 'size__size', 'unitPrice', 'quantity', 'salePrice').order_by('-saleDate')

    structure = json.dumps(list(sales), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def post_sale(request, affiliateId):
    if request.method == 'POST':
        form = SaleForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('daesungwork:showsalestatus', affiliateId)
        else:
            return HttpResponse("유효하지 않은 형식입니다. 관리자에게 문의하세요 : (")


@login_required
@csrf_exempt
def insert_sale(request):
    saleDate = request.POST['saleDate']
    affiliates = Affiliate.objects.get(affiliateId=request.POST['affiliates'])
    client = Company.objects.get(companyName=request.POST['client'])
    jsonSale = json.loads(request.POST['jsonSale'])
    for sale in jsonSale:
        Sale.objects.create(
            saleDate=saleDate,
            affiliate=affiliates,
            client=client,
            product=Product.objects.get(productId=int(sale['product'])),
            size=Size.objects.get(sizeId=int(sale['size'])),
            unitPrice=sale['unitPrice'],
            quantity=sale['quantity'],
            salePrice=sale['salePrice'],
        )
    return redirect('daesungwork:showsalestatus', request.POST['affiliates'])


@login_required
@csrf_exempt
def delete_sale(request, saleId):
    sale = Sale.objects.get(saleId=saleId)
    sale.delete()
    return redirect('daesungwork:showsalestatus', 'all')


@login_required
@csrf_exempt
def show_dailyreports(request):
    template = loader.get_template('daesungwork/showdailyreports.html')
    employees = Employee.objects.all()
    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        writer = request.POST['writer']
    else:
        startdate = ''
        enddate = ''
        writer = ''

    form = DailyReportForm(initial={'writeEmp': request.user.employee.empId})
    context = {
        'form': form,
        'startdate': startdate,
        'enddate': enddate,
        'writer': writer,
        'employees': employees,
    }

    return HttpResponse(template.render(context, request))



@login_required
@csrf_exempt
def dailyreports_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    writer = request.POST['writer']

    if request.user.is_staff:
        dailyreports = DailyReport.objects.all()
    else:
        dailyreports = DailyReport.objects.filter(writeEmp=request.user.employee.empId)

    if startdate:
        dailyreports = dailyreports.filter(workDate__gte=startdate)

    if enddate:
        dailyreports = dailyreports.filter(workDate__lte=enddate)

    if writer:
        dailyreports = dailyreports.filter(writeEmp=writer)

    dailyreports = dailyreports.values('dailyreportId', 'workDate', 'writeEmp__empName', 'title', 'writeDatetime')
    structure = json.dumps(list(dailyreports), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def post_dailyreport(request):
    if request.method == 'POST':
        form = DailyReportForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('daesungwork:showdailyreports')
        else:
            return HttpResponse("유효하지 않은 형식입니다. 관리자에게 문의하세요 : (")

    else:
        return HttpResponse("잘못된 접근입니다. : (")


@login_required
@csrf_exempt
def view_dailyreport(request, dailyreportId):
    template = loader.get_template('daesungwork/viewdailyreport.html')
    dailyreportInstance = DailyReport.objects.get(dailyreportId=dailyreportId)

    if request.method == 'POST':
        form = DailyReportForm(request.POST, request.FILES, instance=dailyreportInstance)
        if form.is_valid():
            post = form.save(commit=False)
            post.modifyDatetime = datetime.datetime.now()
            post.save()

            return redirect('daesungwork:showdailyreports')
        else:
            return HttpResponse('유효하지 않은 형식입니다.')

    else:
        form = DailyReportForm(instance=dailyreportInstance)
        writer = dailyreportInstance.writeEmp.empName
        fileName = dailyreportInstance.files
        context = {
            'form': form,
            'writer': writer,
            'dailyreportId': dailyreportId,
            'fileName': fileName,
        }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def delete_dailyreport(request, dailyreportId):
    dailyreport = DailyReport.objects.get(dailyreportId=dailyreportId)
    dailyreport.delete()
    return redirect('daesungwork:showdailyreports')


@login_required
@csrf_exempt
def show_productlocation(request):
    template = loader.get_template('daesungwork/showproductlocation.html')
    employees = Employee.objects.all()
    maincategorys = WarehouseMainCategory.objects.all()
    subcategorys = WarehouseSubCategory.objects.all()
    products = Product.objects.filter(productStatus='Y')

    if request.method == 'POST':
        selectType = request.POST['selectType']
        # 창고명 또는 위치 변경하였을 때
        if selectType == 'location':
            productId = ''
            maincategoryId = int(request.POST['maincategoryId'])
            subcategoryId = int(request.POST['subcategoryId'])
            sectionImage = Warehouse.objects.filter(
                Q(mainCategory=maincategoryId) & Q(subCategory=subcategoryId)
            ).first()
        # 모델명 변경하였을 때
        elif selectType == 'product':
            productId = int(request.POST['productId'])
            if Product.objects.get(productId=productId).position:
                sectionImage = Warehouse.objects.get(
                    Q(warehouseId=Product.objects.get(productId=productId).position.warehouseId)
                )
                maincategoryId = int(sectionImage.mainCategory.categoryId)
                subcategoryId = int(sectionImage.subCategory.categoryId)
            else:
                sectionImage = ''
                maincategoryId = maincategorys.first().categoryId
                subcategoryId = subcategorys.first().categoryId
        # 여기로 오면 오류
        else:
            productId = ''
            maincategoryId = maincategorys.first().categoryId
            subcategoryId = subcategorys.first().categoryId
            sectionImage = Warehouse.objects.filter(
                Q(mainCategory=maincategoryId) & Q(subCategory=subcategoryId)
            ).first()
    else:
        productId = ''
        maincategoryId = maincategorys.first().categoryId
        subcategoryId = subcategorys.first().categoryId
        sectionImage = Warehouse.objects.filter(
            Q(mainCategory=maincategoryId) & Q(subCategory=subcategoryId)
        ).first()

    context = {
        'productId': productId,
        'employees': employees,
        'maincategorys': maincategorys,
        'subcategorys': subcategorys,
        'maincategoryId': maincategoryId,
        'subcategoryId': subcategoryId,
        'sectionImage': sectionImage,
        'products': products,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def location_asjson(request):
    productId = request.POST['productId']
    sizeId = request.POST['sizeId']
    maincategoryId = request.POST['maincategoryId']
    subcategoryId = request.POST['subcategoryId']

    products = Product.objects.filter(productStatus='Y')

    if productId:
        products = products.filter(productId=productId)

    if sizeId:
        products = products.filter(size=sizeId)

    if maincategoryId:
        products = products.filter(position__mainCategory__categoryId=maincategoryId)

    if subcategoryId:
        products = products.filter(position__subCategory__categoryId=subcategoryId)

    products = products.values('productId', 'productPicture', 'modelName', 'size__size', 'unitPrice')
    structure = json.dumps(list(products), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def show_stocks(request):
    template = loader.get_template('daesungwork/showstocks.html')
    types = Type.objects.all()

    if request.method == 'POST':

        if request.POST['typeId']:
            typeId = int(request.POST['typeId'])
        else:
            typeId = ''

    else:
        typeId = ''

    context = {
        'types': types,
        'typeId': typeId,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def stocks_asjson(request):
    typeId = request.POST['typeId']
    stockchecks = StockCheck.objects.all()
    if typeId:
        stockchecks = stockchecks.filter(typeName__typeId=typeId)
    stockchecks = stockchecks.values('stockcheckId', 'typeName__typeName', 'checkDate', 'checkEmp__empName', 'modifyDate')
    structure = json.dumps(list(stockchecks), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def post_stock(request, typeId):
    template = loader.get_template('daesungwork/poststocks.html')
    today = datetime.datetime.today()
    types = Type.objects.all()

    if request.method == 'POST':
        stockChecks = StockCheck.objects.create(
            checkDate=request.POST['checkDate'],
            typeName=Type.objects.get(typeId=request.POST['typeId']),
            checkEmp=Employee.objects.get(empId=request.user.employee.empId)
        )
        jsonStocks = json.loads(request.POST['jsonStocks'])

        for item in jsonStocks:
            if Size.objects.filter(Q(productId=item["productId"]) & Q(size=item["size"])).first():
                ProductCheck.objects.create(
                    product=Product.objects.get(productId=item["productId"]),
                    size=Size.objects.filter(Q(productId=item["productId"]) & Q(size=item["size"])).first(),
                    productGap=item["productGap"],
                    stockcheck=stockChecks,
                )

        return redirect('daesungwork:showstocks')
    else:
        if typeId == 'None':
            typeId = types.first().typeId
        else:
            typeId = int(typeId)


    products = Product.objects.filter(Q(productStatus='Y') & Q(typeName__typeId=typeId) & Q(size__isnull=False))
    sizes = products.values('size__size').distinct()
    products = products.values('productId', 'modelName').distinct()
    context = {
        "types": types,
        "typeId": typeId,
        'products': products,
        "sizes": sizes,
        "sizecount": len(sizes),
        "today": today,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def modify_stock(request, stockcheckId):
    template = loader.get_template('daesungwork/poststocks.html')
    stockInstance = StockCheck.objects.get(stockcheckId=stockcheckId)
    productNames = ProductCheck.objects.filter(stockcheck=stockcheckId).values('product_id').distinct()
    types = Type.objects.all()
    if request.method == 'POST':
        jsonStocks = json.loads(request.POST['jsonStocks'])
        stocksId = list(i[0] for i in ProductCheck.objects.filter(stockcheck=stockcheckId).values_list('productcheckId'))
        jsonStocksId = []

        for item in jsonStocks:
            if item['itemId'] == '추가':
                # 새로운 모델 추가
                ProductCheck.objects.create(
                    product=Product.objects.get(productId=item["productId"]),
                    size=Size.objects.filter(Q(productId=item["productId"]) & Q(size=item["size"])).first(),
                    productGap=item["productGap"],
                    stockcheck=stockInstance,
                )
            else:
                # 해당 모델에 해당 사이즈가 있는 경우
                if Size.objects.filter(Q(productId=item["productId"]) & Q(size=item["size"])).first():
                    try:
                        productCheckInstance = ProductCheck.objects.get(Q(stockcheck=stockInstance.stockcheckId) & Q(product__productId=item["productId"]) & Q(size__size=item["size"]))
                        productCheckInstance.productGap = item["productGap"]
                        productCheckInstance.save()
                        jsonStocksId.append(int(productCheckInstance.productcheckId))
                    except:
                        ProductCheck.objects.create(
                            product=Product.objects.get(Q(productId=item["productId"])),
                            size=Size.objects.filter(Q(productId=item["productId"]) & Q(size=item["size"])).first(),
                            productGap=item["productGap"],
                            stockcheck=stockInstance,
                        )

        delStocksId = list(set(stocksId) - set(jsonStocksId))
        if delStocksId:
            for Id in delStocksId:
                ProductCheck.objects.filter(productcheckId=Id).delete()

        # 수정일자 수정
        stockInstance.modifyDate = datetime.datetime.now()
        stockInstance.save()
        return redirect('daesungwork:showstocks')
    else:
        typeId = stockInstance.typeName_id
        checkDate = stockInstance.checkDate
        checkStockList = []
        for stock in productNames:
            checkStockList.append(ProductCheck.objects.filter(Q(stockcheck=stockcheckId) & Q(product=stock['product_id'])))
    products = Product.objects.filter(Q(productStatus='Y') & Q(typeName__typeId=typeId) & Q(size__isnull=False))
    sizes = products.values('size__size').distinct()
    products = products.values('productId', 'modelName').distinct()
    context = {
        "types": types,
        "typeId": typeId,
        'products': products,
        "sizes": sizes,
        "sizecount": len(sizes),
        "stockInstance": stockInstance,
        "checkDate": checkDate,
        "checkStockList": checkStockList,
        "productNames": productNames,
    }

    return HttpResponse(template.render(context, request))

@login_required
@csrf_exempt
def typeproducts_asjson(request):
    typeId = request.POST['typeId']
    stockcheckId = request.POST['stockcheckId']
    if stockcheckId:
        jsonList = []
        products = Product.objects.filter(Q(productStatus='Y') & Q(typeName__typeId=typeId) & Q(size__isnull=False)).values('productId', 'modelName').distinct()
        jsonList.append(list(products))
        productNames = ProductCheck.objects.filter(stockcheck=stockcheckId).values('product_id').distinct()
        jsonList.append(list(productNames))
        checkStockList = []
        for stock in productNames:
            checkStockList.append(list(ProductCheck.objects.filter(Q(stockcheck=stockcheckId) & Q(product=stock['product_id'])).values_list('product__productId', 'size__size', 'productGap')))
        jsonList.append({'gap': checkStockList})

    else:
        products = Product.objects.filter(Q(productStatus='Y') & Q(typeName__typeId=typeId) & Q(size__isnull=False)).values('productId', 'modelName').distinct()
        jsonList = list(products)
    structure = json.dumps(list(jsonList), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_stock_pdf(request, stockcheckId):
    stockInstance = StockCheck.objects.get(stockcheckId=stockcheckId)
    productInstance = ProductCheck.objects.filter(stockcheck=stockcheckId).order_by('product', 'size__size')
    context = {
        "stockInstance": stockInstance,
        "productInstance": productInstance,
    }
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{} 재고 현황.pdf"'.format(stockInstance.checkDate)

    template = get_template('daesungwork/viewstockpdf.html')
    html = template.render(context, request)
    # create a pdf
    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@login_required
@csrf_exempt
def show_stockinout(request):
    template = loader.get_template('daesungwork/showstockinout.html')
    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        modelName = request.POST['filterProduct']
        sizeName = request.POST['filterSize']
    else:
        startdate = ''
        enddate = ''
        modelName = ''
        sizeName = ''

    product = ''
    size = ''
    stockmanagement = StockManagement.objects.all()
    if startdate:
        stockmanagement = stockmanagement.filter(createdDateTime__gte=startdate)
    if enddate:
        stockmanagement = stockmanagement.filter(createdDateTime__lte=enddate)
    if modelName:
        stockmanagement = stockmanagement.filter(productName=modelName)
        product = Product.objects.get(productId=modelName).modelName
    if sizeName:
        stockmanagement = stockmanagement.filter(sizeName=sizeName)
        size = Size.objects.get(sizeId=sizeName).size

    inRemaining = stockmanagement.filter(typeName='입고').aggregate(sum=Sum('quantity'))['sum'] or 0
    outRemaining = stockmanagement.filter(typeName='출고').aggregate(sum=Sum('quantity'))['sum'] or 0
    remaining = inRemaining - outRemaining
    form = StockManagementForm()
    products = Product.objects.filter(productStatus="Y")
    authorizations = Authorization.objects.filter(Q(empId=request.user.employee.empId) & Q(menuId__codeName__in=['s35', 's35-1', 's35-2']))
    if authorizations:
        context = {
            "form": form,
            "startdate": startdate,
            "enddate": enddate,
            "modelName": modelName,
            "sizeName": sizeName,
            "products": products,
            "authorizations": authorizations.exclude(menuId__codeName='s35'),

            # 상단 카드
            "product": product,
            "size": size,
            "remaining": remaining,
        }
        return HttpResponse(template.render(context, request))
    else:
        return HttpResponse("접근권한이 없습니다.")



@login_required
@csrf_exempt
def post_stockinout(request, typeName):
    if request.method == 'POST':
        form = StockManagementForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.managerEmp = Employee.objects.get(empId=request.user.employee.empId)
            post.typeName = typeName
            post.save()
            return redirect('daesungwork:showstockinout')
        else:
            return HttpResponse('유효하지 않은 형식입니다.')

    else:
        return HttpResponse("잘못된 접근입니다. : (")


@login_required
@csrf_exempt
def stockinout_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    modelName = request.POST['modelName']
    sizeName = request.POST['sizeName']

    stockmanagement = StockManagement.objects.all()
    if startdate:
        stockmanagement = stockmanagement.filter(createdDateTime__gte=startdate)
    if enddate:
        stockmanagement = stockmanagement.filter(createdDateTime__lte=enddate)
    if modelName:
        stockmanagement = stockmanagement.filter(productName=modelName)
    if sizeName:
        stockmanagement = stockmanagement.filter(sizeName=sizeName)

    stockmanagement = stockmanagement.values('stockManagementId', 'managerEmp__empName', 'typeName', 'productName__productPicture', 'productName__modelName', 'sizeName__size', 'quantity', 'createdDateTime')
    structure = json.dumps(list(stockmanagement), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def inoutcheck_asjson(request):
    modelName = request.POST['modelName']
    sizeName = request.POST['sizeName']
    remainingQuantity = StockManagement.objects.filter(Q(productName=modelName) & Q(sizeName=sizeName))
    inRemaining = remainingQuantity.filter(typeName='입고').aggregate(sum=Sum('quantity'))['sum'] or 0
    outRemaining = remainingQuantity.filter(typeName='출고').aggregate(sum=Sum('quantity'))['sum'] or 0
    # 잔여 수량
    remaining = inRemaining - outRemaining
    structure = json.dumps(str(remaining), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def warehouseimage_asjson(request):
    warehouseId = request.POST['warehouseId']
    warehouseDrawing = Warehouse.objects.get(warehouseId=warehouseId).warehouseDrawing
    warehouse = {'img': str(warehouseDrawing)}
    structure = json.dumps(warehouse, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')