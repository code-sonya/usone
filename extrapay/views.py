# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, F, Value, FloatField, Max, Sum, Case, When, IntegerField, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import Coalesce, Concat
from xhtml2pdf import pisa
from service.functions import link_callback

from hr.models import Employee
from service.models import Servicereport, Geolocation
from service.functions import latlng_distance
from .models import OverHour, Car, Oil, Fuel, ExtraPay
from .functions import cal_overhour, Round, cal_extraPay
from usone.security import MAP_KEY, testMAP_KEY


@login_required
def over_hour(request):
    template = loader.get_template('extrapay/overhourlist.html')

    if request.method == "POST":
        searchdate = request.POST['searchdate']
        filter = 'Y'


    else:
        searchdate = ''
        filter = 'N'

    employee = Employee.objects.filter(Q(empStatus='Y'))

    context = {
        'filter': filter,
        'searchdate': searchdate,
        'employee': employee,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def over_asjson(request):
    searchdate = request.POST['searchdate']
    searchYear = searchdate[:4]
    searchMonth = searchdate[5:7]

    extrapay = ExtraPay.objects.all()
    if searchdate:
        extrapay = ExtraPay.filter(Q(overHourDate__year=searchYear) & Q(overHourDate__month=searchMonth))

    extrapaylist = extrapay.values('overHourDate', 'empId__empDeptName', 'empName', 'sumOverHour', 'compensatedHour', 'payHour', 'compensatedComment', 'extraPayId')
    structure = json.dumps(list(extrapaylist), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def post_car(request):
    cars = Car.objects.all().order_by('-oilType', 'carType')

    if request.method == "POST":
        jsonCar = json.loads(request.POST['jsonCar'])
        carId = [i[0] for i in cars.values_list('carId')]
        jsonCarId = []
        for car in jsonCar:
            if car["carId"] == "추가":
                Car.objects.create(
                    oilType=car["oilType"],
                    carType=car["carType"],
                    comment=car["comment"],
                    kpl=car["kpl"],
                )
            else:
                carInstance = cars.get(carId=int(car["carId"]))
                carInstance.oilType = car["oilType"]
                carInstance.carType = car["carType"]
                carInstance.comment = car["comment"]
                carInstance.kpl = car["kpl"]
                carInstance.save()
                jsonCarId.append(int(car["carId"]))

        delCarId = list(set(carId) - set(jsonCarId))
        if delCarId:
            for Id in delCarId:
                Car.objects.filter(carId=Id).delete()

    context = {
        'cars': cars,
    }

    return render(request, 'extrapay/postcar.html', context)


@login_required
@csrf_exempt
def show_oils(request):
    if request.POST:
        selectMonth = datetime(int(request.POST['findDate'][:4]), int(request.POST['findDate'][5:7]), 1).date()
    else:
        todayMonth = datetime(datetime.today().year, datetime.today().month, 1).date()
        oilMonth = Oil.objects.aggregate(maxMonth=Max('oilDate'))['maxMonth']
        selectMonth = todayMonth

        if todayMonth != oilMonth:
            selectMonth = todayMonth - relativedelta(months=1)

    oils = Oil.objects.filter(oilDate=selectMonth).order_by('-carId__oilType', 'carId__carType')
    lastOils = Oil.objects.filter(oilDate=selectMonth-relativedelta(months=1))

    joinOils = []

    for oil in oils:
        if lastOils:
            lastmpk = lastOils.filter(carId=oil.carId).first().mpk
        else:
            lastmpk = '-'
        temp = {
            'oilType': oil.carId.oilType,
            'carType': oil.carId.carType,
            'carComment': oil.carId.comment,
            'lastmpk': lastmpk,
            'mpk': oil.mpk,
            'kpl': oil.carId.kpl,
            'oilMoney': oil.oilMoney,
        }
        if lastmpk != '-':
            iad = temp['mpk'] - temp['lastmpk']
            if iad > 0:
                temp['iad'] = str(abs(iad)) + '원상승'
            elif iad < 0:
                temp['iad'] = str(abs(iad)) + '원하락'
            else:
                temp['iad'] = '동일'
        else:
            temp['iad'] = '-'

        joinOils.append(temp)

    context = {
        'selectMonth': selectMonth,
        'joinOils': joinOils,
    }

    return render(request, 'extrapay/showoils.html', context)


@login_required
@csrf_exempt
def post_oils(request):
    if request.method == "POST":
        cars = Car.objects.all()
        if Oil.objects.filter(oilDate=request.POST['oilDate']+'-01'):
            Oil.objects.filter(oilDate=request.POST['oilDate']+'-01').delete()
        for car in cars:
            if car.oilType == '휘발유':
                oilMoney = float(request.POST['gasoline'])
            elif car.oilType == '경유':
                oilMoney = float(request.POST['diesel'])
            elif car.oilType == 'LPG':
                oilMoney = float(request.POST['lpg'])
            else:
                oilMoney = 0
            Oil.objects.create(
                oilDate=request.POST['oilDate'] + '-01',
                carId=car,
                oilMoney=oilMoney,
                mpk=round(oilMoney/car.kpl),
            )
        return redirect('extrapay:showoils')


@login_required
@csrf_exempt
def show_fuel(request):
    if request.method == 'POST':
        y = int(request.POST['findDate'][:4])
        m = int(request.POST['findDate'][5:7])
    else:
        y = datetime.today().year
        m = datetime.today().month
    startdate = str(datetime(y, m, 1).date())
    enddate = str((datetime(y, m+1, 1) - timedelta(days=1)).date())
    context = {
        'startdate': startdate,
        'enddate': enddate,
    }
    return render(request, 'extrapay/showfuel.html', context)


@login_required
@csrf_exempt
def post_fuel(request):
    if request.method == 'POST':
        mpk = Oil.objects.filter(Q(oilDate=request.POST['startdate']) & Q(carId=request.user.employee.carId))
        if mpk:
            mpk = mpk.values('mpk')[0]['mpk']
        else:
            mpk = 0
        serviceIds = json.loads(request.POST['serviceId'])
        for serviceId in serviceIds:
            geo = Geolocation.objects.get(serviceId=serviceId)
            fuelMoney = geo.distance * 1.2 * mpk
            Fuel.objects.create(
                serviceId=Servicereport.objects.get(serviceId=serviceId),
                fuelMoney=fuelMoney,
            )
    return redirect('extrapay:showfuel')


def admin_fuel(request):
    if request.method == 'POST':
        y = int(request.POST['findDate'][:4])
        m = int(request.POST['findDate'][5:7])
    else:
        y = datetime.today().year
        m = datetime.today().month
    startdate = str(datetime(y, m, 1).date())
    enddate = str((datetime(y, m+1, 1) - timedelta(days=1)).date())
    context = {
        'startdate': startdate,
        'enddate': enddate,
    }
    return render(request, 'extrapay/adminfuel.html', context)


def approval_fuel(request, empId):
    if request.method == 'POST':
        y = int(request.POST['findDate'][:4])
        m = int(request.POST['findDate'][5:7])
    else:
        y = datetime.today().year
        m = datetime.today().month
    startdate = str(datetime(y, m, 1).date())
    enddate = str((datetime(y, m+1, 1) - timedelta(days=1)).date())
    empName = Employee.objects.get(empId=empId).empName

    context = {
        'startdate': startdate,
        'enddate': enddate,
        'empName': empName,
        'empId': empId,
        'testMAP_KEY': testMAP_KEY,
        # 'approvalStatus': approvalStatus,
    }
    return render(request, 'extrapay/approvalfuel.html', context)


def approval_post_fuel(request):
    if request.method == 'POST':
        yid = json.loads(request.POST['yid'])
        nid = json.loads(request.POST['nid'])
        for y in yid:
            instance = Fuel.objects.get(fuelId=y)
            instance.fuelStatus = 'Y'
            instance.save()
        for n in nid:
            instance = Fuel.objects.get(fuelId=n[0])
            instance.comment = n[1]
            instance.fuelStatus = 'R'
            instance.save()
        return redirect('extrapay:approvalfuel', request.POST['empId'])


@login_required
@csrf_exempt
def approvalfuel_asjson(request):
    if request.method == 'POST':
        empId = request.POST['empId']
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        status = request.POST['status']

        if status == 'N':
            services = Fuel.objects.select_related().filter(
                Q(serviceId__empId=empId) &
                Q(serviceId__serviceStatus='Y') &
                Q(serviceId__serviceDate__gte=startdate) &
                Q(serviceId__serviceDate__lte=enddate) &
                Q(fuelStatus='N')
            ).annotate(
                serviceDate=F('serviceId__serviceDate'),
                companyName=F('serviceId__companyName__companyName'),
                serviceTitle=F('serviceId__serviceTitle'),
            )

            services = services.values(
                'fuelId', 'serviceId__serviceId', 'serviceDate', 'companyName', 'serviceTitle',
                'fuelMoney', 'comment', 'fuelStatus',
            )
            for service in services:
                service['distance'] = Geolocation.objects.get(
                    serviceId=service['serviceId__serviceId']
                ).distance

            structure = json.dumps(list(services), cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')

        elif status == 'YR':
            services = Fuel.objects.select_related().filter(
                Q(serviceId__empId=empId) &
                Q(serviceId__serviceStatus='Y') &
                Q(serviceId__serviceDate__gte=startdate) &
                Q(serviceId__serviceDate__lte=enddate) &
                Q(fuelStatus__in=['Y', 'R'])
            ).annotate(
                serviceDate=F('serviceId__serviceDate'),
                companyName=F('serviceId__companyName__companyName'),
                serviceTitle=F('serviceId__serviceTitle'),
            )

            services = services.values(
                'fuelId', 'serviceId__serviceId', 'serviceDate', 'companyName', 'serviceTitle',
                'fuelMoney', 'comment', 'fuelStatus',
            )
            for service in services:
                service['distance'] = Geolocation.objects.get(
                    serviceId=service['serviceId__serviceId']
                ).distance

            structure = json.dumps(list(services), cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')
    elif request.method == 'GET':
        geo = Geolocation.objects.get(serviceId=request.GET['serviceId'])
        distanceMessage = '정상'
        if geo.distanceCode == 1:
            distanceMessage = '출발지와 도착지가 동일'
        elif geo.distanceCode == 2:
            distanceMessage = '출발지 또는 도착지가 도로 주변이 아님'
        elif geo.distanceCode == 3:
            distanceMessage = '자동차 길찾기 결과 제공 불가'
        elif geo.distanceCode == 4:
            distanceMessage = '경유지가 도로 주변이 아님'
        elif geo.distanceCode == 5:
            distanceMessage = '요청 경로가 1500km 이상'

        path = [i.split(", ") for i in geo.path[2:-2].split("], [")]
        pathCenter =len(path)//2

        geos = {
            'beginLatitude': geo.beginLatitude,
            'beginLongitude': geo.beginLongitude,
            'startLatitude': geo.startLatitude,
            'startLongitude': geo.startLongitude,
            'endLatitude': geo.endLatitude,
            'endLongitude': geo.endLongitude,
            'finishLatitude': geo.finishLatitude,
            'finishLongitude': geo.finishLongitude,
            'distance': geo.distance,
            'distanceMessage': distanceMessage,
            'serviceId': request.GET['serviceId'],
            'path': path,
            'pathCenterLong': float(path[pathCenter][0]),
            'pathCenterLat': float(path[pathCenter][1]),
        }

        structure = json.dumps(geos, cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def adminfuel_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']

    fuels = Fuel.objects.select_related().filter(
        Q(serviceId__serviceStatus='Y') &
        Q(serviceId__serviceDate__gte=startdate) &
        Q(serviceId__serviceDate__lte=enddate)
    ).values('serviceId__empId').annotate(
        empDeptName=F('serviceId__empId__empDeptName'),
        empPosition=F('serviceId__empId__empPosition__positionName'),
        empName=F('serviceId__empId__empName'),
        car=Concat(F('serviceId__empId__carId__oilType'), Value(', '), F('serviceId__empId__carId__carType')),
        progress=Count('fuelStatus', filter=Q(fuelStatus='N')),
        approval=Count('fuelStatus', filter=Q(fuelStatus='Y')),
        reject=Count('fuelStatus', filter=Q(fuelStatus='R')),
        # sum_distance=Coalesce(Sum('totalDistance', filter=Q(fuelStatus='Y')), 0),
        sum_fuelMoney=Coalesce(Sum('fuelMoney', filter=Q(fuelStatus='Y')), 0),
    )

    fuels = fuels.values(
        'serviceId__empId', 'empDeptName', 'empPosition', 'empName',
        'car', 'progress', 'approval', 'reject', 'sum_fuelMoney',
    )

    for fuel in fuels:
        fuel['sum_distance'] = Geolocation.objects.filter(
            serviceId__empId=fuel['serviceId__empId']
        ).aggregate(sum=Sum('distance'))['sum']

    structure = json.dumps(list(fuels), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def fuel_asjson(request):
    empId = request.user.employee.empId
    carId = request.user.employee.carId
    status = request.POST['status']
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']

    if status == 'post':
        mpk = Oil.objects.filter(Q(oilDate=startdate) & Q(carId=carId))
        if mpk:
            mpk = mpk.values('mpk')[0]['mpk']
        else:
            mpk = 0

        fuels = Fuel.objects.select_related().filter(
            Q(serviceId__empId=empId) &
            Q(serviceId__serviceStatus='Y') &
            Q(serviceId__serviceDate__gte=startdate) &
            Q(serviceId__serviceDate__lte=enddate)
        ).values('serviceId__serviceId')

        services = Geolocation.objects.select_related().filter(
            Q(serviceId__empId=empId) &
            Q(serviceId__serviceStatus='Y') &
            Q(serviceId__serviceDate__gte=startdate) &
            Q(serviceId__serviceDate__lte=enddate)
        ).exclude(
            serviceId__in=[i['serviceId__serviceId'] for i in fuels]
        ).annotate(
            serviceDate=F('serviceId__serviceDate'),
            companyName=F('serviceId__companyName__companyName'),
            serviceTitle=F('serviceId__serviceTitle'),
        )

        services = services.values(
            'serviceId', 'serviceId__serviceId', 'serviceDate', 'companyName',
            'serviceTitle', 'distance', 'distanceCode',
            'beginLatitude', 'beginLongitude', 'startLatitude', 'startLongitude',
            'endLatitude', 'endLongitude', 'finishLatitude', 'finishLongitude', 'serviceId__empId__carId'
        )

        for service in services:
            service['fuelMoney'] = service['distance'] * mpk

        structure = json.dumps(list(services), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')

    elif status == 'show':
        services = Fuel.objects.select_related().filter(
            Q(serviceId__empId=empId) &
            Q(serviceId__serviceStatus='Y') &
            Q(serviceId__serviceDate__gte=startdate) &
            Q(serviceId__serviceDate__lte=enddate)
        ).annotate(
            serviceDate=F('serviceId__serviceDate'),
            companyName=F('serviceId__companyName__companyName'),
            serviceTitle=F('serviceId__serviceTitle'),
        )

        services = services.values(
            'serviceId__serviceId', 'serviceDate', 'companyName', 'serviceTitle',
            'fuelMoney', 'fuelStatus', 'comment'
        )
        for service in services:
            service['distance'] = Geolocation.objects.get(
                serviceId=service['serviceId__serviceId']
            ).distance
        structure = json.dumps(list(services), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_overhour(request, extraPayId):
    extrapay = ExtraPay.objects.filter(Q(extraPayId=extraPayId))\
        .values('overHourDate__year', 'overHourDate__month', 'empId__empName', 'empId__empSalary', 'empId__empDeptName', 'empId__empCode', 'extraPayId', 'empId__empPosition_id__positionName',
                'compensatedComment', 'compensatedHour', 'payStatus').first()
    overhours = OverHour.objects.filter(Q(extraPayId=extraPayId) & Q(overHour__isnull=False))
    sum_overhours = overhours.aggregate(sumOverhour=Sum('overHour'),
                                        sumOverhourWeekDay=Sum('overHourWeekDay'),
                                        sumServicehour=Round(Sum('serviceId__serviceHour')),
                                        sumOverhourCost=Sum('overHourCost'),
                                        sumOverhourCostWeekDay=Sum('overHourCostWeekDay'),
                                        sumFoodCost=Sum('foodCost'))
    foodcosts = OverHour.objects.filter(Q(extraPayId=extraPayId) & Q(overHour__isnull=True))
    sum_foodcosts = foodcosts.aggregate(sumServicehour=Sum('serviceId__serviceHour'), sumFoodCost=Sum('foodCost'))


    if extrapay['payStatus'] == 'N':
        real_extraPay = int((sum_overhours['sumOverhour']-(extrapay['compensatedHour'] or 0))*1.5*extrapay['empId__empSalary'])
        if real_extraPay > 200000:
            real_extraPay = 200000

        sum_costs = {
            'extraPayDate': '{}.{}'.format(extrapay['overHourDate__year'], extrapay['overHourDate__month']),
            'overHour': sum_overhours['sumOverhour'],
            'compensatedHour': extrapay['compensatedHour'],
            'extraPayHour': sum_overhours['sumOverhour']-(extrapay['compensatedHour'] or 0),
            'extraPay': real_extraPay,
            'foodCost': int(sum_overhours['sumFoodCost']+(sum_foodcosts['sumFoodCost'] or 0)),
            'sumPay': int(real_extraPay + sum_overhours['sumFoodCost']+(sum_foodcosts['sumFoodCost'] or 0))
        }
    else:
        sum_costs = {
            'extraPayDate': '{}.{}'.format(extrapay['overHourDate__year'], extrapay['overHourDate__month']),
            'overHour': sum_overhours['sumOverhour'] + sum_overhours['sumOverhourWeekDay'],
            'compensatedHour': extrapay['compensatedHour'],
            'extraPayHour': sum_overhours['sumOverhour'] + sum_overhours['sumOverhourWeekDay']-(extrapay['compensatedHour'] or 0),
            'extraPay': int(sum_overhours['sumOverhourCost'] + sum_overhours['sumOverhourCostWeekDay']),
            'foodCost': 0,
            'sumPay': int(sum_overhours['sumOverhourCost'] + sum_overhours['sumOverhourCostWeekDay']),
        }
    context={
        'overhour': overhours,
        'extrapay': extrapay,
        'foodcosts': foodcosts,
        'sum_overhours': sum_overhours,
        'sum_foodcosts': sum_foodcosts,
        'sum_costs': sum_costs,
    }
    return render(request, 'extrapay/viewoverhour.html', context)


@login_required
@csrf_exempt
def overhour_all(request,searchdate):
    if request.method == 'POST':
        todayYear = int(request.POST['searchdate'][:4])
        todayMonth = int(request.POST['searchdate'][5:7])
        today = request.POST['searchdate'][:7]
    else:
        todayYear = datetime.today().year
        todayMonth = datetime.today().month
        today = '{}-{}'.format(todayYear, todayMonth)

    extrapayInfra, sumInfra = cal_extraPay('인프라서비스사업팀', todayYear, todayMonth)
    extrapaySolution, sumSolution = cal_extraPay('솔루션지원팀', todayYear, todayMonth)
    extrapayDB, sumDB = cal_extraPay('DB지원팀', todayYear, todayMonth)
    extrapaySupport, sumSupport = cal_extraPay('미정', todayYear, todayMonth)

    sumEmp = {'sumoverHour': 0, 'sumcompensatedHour': 0, 'sumoverandfoodCost': 0, 'sumfoodCost': 0, 'sumCost': 0}

    for sum in [sumInfra, sumSolution, sumDB]:
        sumEmp['sumoverHour'] += sum['sumoverHour']
        sumEmp['sumcompensatedHour'] += sum['sumcompensatedHour']
        sumEmp['sumoverandfoodCost'] += sum['sumoverandfoodCost']
        sumEmp['sumfoodCost'] += sum['sumfoodCost']
        sumEmp['sumCost'] += sum['sumCost']

    sumAll = (sumEmp['sumCost'] or 0) + (sumSupport['sumCost'] or 0)
    print('today:', today)
    context = {
            'today':today,
            'todayYear': todayYear,
            'todayMonth': todayMonth,
            'extrapayInfra': extrapayInfra,
            'extrapaySolution': extrapaySolution,
            'extrapayDB': extrapayDB,
            'extrapaySupport': extrapaySupport,
            'sumEmp': sumEmp,
            'sumSupport': sumSupport,
            'sumAll': sumAll,
            }
    return render(request, 'extrapay/overhourall.html', context)


@login_required
@csrf_exempt
def post_overhour(request):
    if request.method == "POST":
        overhourDate = request.POST['overhourDate']
        empType = request.POST['empType']
        empId = request.POST['empName']
        hourType = request.POST['hourType']
        # 평일
        overHourWeekDay = request.POST['overHourWeekDay']
        overHourCostWeekDay = request.POST['overHourCostWeekDay']
        # 주말
        overhour = request.POST['overhour']
        overHourCost = request.POST['overHourCost']
        overhouYear = overhourDate[:4]
        overhourMonth = overhourDate[5:7]

        if empType == '특수직':
            status = 'X'

        if hourType == '일':
            if overhour:
                overHourCost = float(overhour) * int(overHourCost)
                overhour = float(overhour)*24
            else:
                overHourCost = 0
                overhour = 0

            if overHourWeekDay:
                overHourCostWeekDay = float(overHourWeekDay) * int(overHourCostWeekDay)
                overHourWeekDay = float(overHourWeekDay)*24
            else:
                overHourCostWeekDay = 0
                overHourWeekDay = 0
        else:
            if overhour:
                overhour = float(overhour)
                overHourCost = overhour * int(overHourCost)
            else:
                overhour = 0
                overHourCost = 0

            if overHourWeekDay:
                overHourWeekDay = float(overHourWeekDay)
                overHourCostWeekDay = overHourWeekDay * int(overHourCostWeekDay)
            else:
                overHourWeekDay = 0
                overHourCostWeekDay = 0

        print(request.POST)

        ## IF문으로 해당 엔지니어의 월별 정보가 extrapay에 있는지 확인하고 없으면 생성
        emp = Employee.objects.get(empId=empId)
        extrapay = ExtraPay.objects.filter(Q(overHourDate__year=overhouYear) & Q(overHourDate__month=overhourMonth) & Q(empId=emp)).first()

        if extrapay:
            sumOverHour = extrapay.sumOverHour
            payHour = extrapay.payHour
            extrapay.sumOverHour = float(sumOverHour) + overhour + overHourWeekDay
            extrapay.payHour = payHour + overhour
            extrapay.save()
        else:
            extrapay = ExtraPay.objects.create(
                empId=emp,
                empName=emp.empName,
                overHourDate='{}-01'.format(overhourDate),
                sumOverHour=overhour+overHourWeekDay,
                payHour=overhour+overHourWeekDay,
                payStatus=status,
            )

        OverHour.objects.create(
            empId=emp,
            empName=emp.empName,
            overHour=overhour,
            overHourWeekDay=overHourWeekDay,
            overHourCost=overHourCost,
            overHourCostWeekDay=overHourCostWeekDay,
            extraPayId=extrapay,
        )
    return redirect('extrapay:overhour')


@login_required
@csrf_exempt
def save_overhourtable(request):
    compensatedHour = request.GET.getlist('compensatedHour')
    compensatedComment = request.GET.getlist('compensatedComment')
    extraPayId = request.GET.getlist('extraPayId')
    print(request.GET)

    for a, b, c in zip(extraPayId, compensatedHour, compensatedComment):
        extraPay = ExtraPay.objects.get(extraPayId=a)
        extraPay.compensatedHour = b
        extraPay.compensatedComment = c
        extraPay.save()

    return redirect('extrapay:overhour')


@login_required
def view_extrapay_pdf(request, yearmonth):
    todayYear = int(yearmonth[:4])
    todayMonth = int(yearmonth[5:7])

    extrapayInfra, sumInfra = cal_extraPay('인프라서비스사업팀', todayYear, todayMonth)
    extrapaySolution, sumSolution = cal_extraPay('솔루션지원팀', todayYear, todayMonth)
    extrapayDB, sumDB = cal_extraPay('DB지원팀', todayYear, todayMonth)
    extrapaySupport, sumSupport = cal_extraPay('미정', todayYear, todayMonth)

    sumEmp = {'sumoverHour': 0, 'sumcompensatedHour': 0, 'sumoverandfoodCost': 0, 'sumfoodCost': 0, 'sumCost': 0}

    for sum in [sumInfra, sumSolution, sumDB]:
        sumEmp['sumoverHour'] += sum['sumoverHour']
        sumEmp['sumcompensatedHour'] += sum['sumcompensatedHour']
        sumEmp['sumoverandfoodCost'] += sum['sumoverandfoodCost']
        sumEmp['sumfoodCost'] += sum['sumfoodCost']
        sumEmp['sumCost'] += sum['sumCost']

    sumAll = (sumEmp['sumCost'] or 0) + (sumSupport['sumCost'] or 0)
    context = {
        'todayYear': todayYear,
        'todayMonth': todayMonth,
        'extrapayInfra': extrapayInfra,
        'extrapaySolution': extrapaySolution,
        'extrapayDB': extrapayDB,
        'extrapaySupport': extrapaySupport,
        'sumEmp': sumEmp,
        'sumSupport': sumSupport,
        'sumAll': sumAll,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{}년{}월시간외수당근무내역.pdf"'.format(todayYear,todayMonth)

    template = get_template('extrapay/viewextrapaypdf.html')
    html = template.render(context, request)
    # create a pdf
    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


def post_distance(request):
    if request.method == 'POST':
        geo = Geolocation.objects.get(serviceId=request.POST['serviceId'])
        geo.distance = request.POST['distance']
        geo.save()
        return redirect('extrapay:approvalfuel', request.POST['empId'])
