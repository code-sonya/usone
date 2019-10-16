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
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import Coalesce, Concat

from hr.models import Employee
from service.models import Servicereport, Geolocation
from service.functions import latlng_distance
from .models import OverHour, Car, Oil, Fuel, ExtraPay
from .functions import cal_overhour


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
    print(employee)

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
    print(extrapaylist)
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
            distance1 = latlng_distance(geo.beginLatitude, geo.beginLongitude, geo.startLatitude, geo.startLongitude)
            distance2 = latlng_distance(geo.startLatitude, geo.startLongitude, geo.endLatitude, geo.endLongitude)
            distance3 = latlng_distance(geo.endLatitude, geo.endLongitude, geo.finishLatitude, geo.finishLongitude)
            totalDistance = distance1 + distance2 + distance3
            fuelMoney = totalDistance * mpk
            Fuel.objects.create(
                serviceId=Servicereport.objects.get(serviceId=serviceId),
                distance1=distance1,
                distance2=distance2,
                distance3=distance3,
                totalDistance=totalDistance,
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
        sum_distance=Coalesce(Sum('totalDistance', filter=Q(fuelStatus='Y')), 0),
        sum_fuelMoney=Coalesce(Sum('fuelMoney', filter=Q(fuelStatus='Y')), 0),
    )

    fuels = fuels.values(
        'empDeptName', 'empPosition', 'empName', 'car', 'progress', 'approval', 'reject',
        'sum_distance', 'sum_fuelMoney',
    )

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
            distance=Value(0, output_field=FloatField()),
        )

        services = services.values(
            'serviceId', 'serviceId__serviceId', 'serviceDate', 'companyName', 'serviceTitle', 'distance',
            'beginLatitude', 'beginLongitude', 'startLatitude', 'startLongitude',
            'endLatitude', 'endLongitude', 'finishLatitude', 'finishLongitude', 'serviceId__empId__carId'
        )

        for service in services:
            service['distance'] = latlng_distance(
                service['beginLatitude'],
                service['beginLongitude'],
                service['startLatitude'],
                service['startLongitude'],
            ) + latlng_distance(
                service['startLatitude'],
                service['startLongitude'],
                service['endLatitude'],
                service['endLongitude'],
            ) + latlng_distance(
                service['endLatitude'],
                service['endLongitude'],
                service['finishLatitude'],
                service['finishLongitude'],
            )
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
            'totalDistance', 'fuelMoney', 'fuelStatus',
        )

        structure = json.dumps(list(services), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_overhour(request, extraPayId):
    extrapay = ExtraPay.objects.filter(Q(extraPayId=extraPayId))\
        .values('overHourDate__year', 'overHourDate__month', 'empId__empName', 'empId__empSalary', 'empId__empDeptName', 'empId__empCode', 'extraPayId', 'empId__empPosition_id__positionName',
                'compensatedComment', 'compensatedHour').first()
    overhours = OverHour.objects.filter(Q(extraPayId=extraPayId) & Q(overHour__isnull=False))
    sum_overhours = overhours.aggregate(sumOverhour=Sum('overHour'), sumServicehour=Sum('serviceId__serviceHour'), sumOverhourCost=Sum('overHourCost'), sumFoodCost=Sum('foodCost'))
    foodcosts = OverHour.objects.filter(Q(extraPayId=extraPayId) & Q(overHour__isnull=True))
    sum_foodcosts = foodcosts.aggregate(sumServicehour=Sum('serviceId__serviceHour'), sumFoodCost=Sum('foodCost'))

    sum_costs = {
        'extraPayDate': '{}.{}'.format(extrapay['overHourDate__year'], extrapay['overHourDate__month']),
        'overHour': sum_overhours['sumOverhour'],
        'compensatedHour': extrapay['compensatedHour'],
        'extraPayHour': sum_overhours['sumOverhour']-extrapay['compensatedHour'],
        'extraPay': int((sum_overhours['sumOverhour']-extrapay['compensatedHour'])*1.5*extrapay['empId__empSalary']),
        'foodCost': int(sum_overhours['sumFoodCost']+sum_foodcosts['sumFoodCost']),
        'sumPay': int((sum_overhours['sumOverhour']-extrapay['compensatedHour'])*1.5*extrapay['empId__empSalary'] + sum_overhours['sumFoodCost']+sum_foodcosts['sumFoodCost'])
    }
    print(sum_costs)


    context={
        'overhour': overhours,
        'extrapay': extrapay,
        'foodcosts': foodcosts,
        'sum_overhours': sum_overhours,
        'sum_foodcosts': sum_foodcosts,
        'sum_costs': sum_costs,
    }
    return render(request, 'extrapay/viewoverhour.html', context)


def overhour_all(request):
    context = {}
    return render(request, 'extrapay/overhourall.html', context)


def post_overhour(request):
    if request.method == "POST":
        overhourDate = request.POST['overhourDate']
        empType = request.POST['empType']
        empId = request.POST['empName']
        hourType = request.POST['hourType']
        overhour = request.POST['overhour']
        overhour_weekend = request.POST['overhour_weekend']
        overhouYear = overhourDate[:4]
        overhourMonth = overhourDate[5:7]

        if empType == '특수직':
            status = 'X'
        else:
            status = 'N'

        if hourType == '일':
            if overhour:
                overhour = float(overhour)*24
            else:
                overhour = 0

            if overhour_weekend:
                overhour_weekend = float(overhour_weekend)*24
            else:
                overhour_weekend = 0
        else:
            if overhour:
                overhour = float(overhour)
            else:
                overhour = 0

            if overhour_weekend:
                overhour_weekend = float(overhour_weekend)
            else:
                overhour_weekend = 0


        ## IF문으로 해당 엔지니어의 월별 정보가 extrapay에 있는지 확인하고 없으면 생성
        emp = Employee.objects.get(empId=empId)
        extrapay = ExtraPay.objects.filter(Q(overHourDate__year=overhourMonth) & Q(overHourDate__month=overhourMonth) & Q(empId=emp)).first()
        print('extrapay:', extrapay)
        if extrapay:
            print('exit')
            sumOverHour = extrapay.sumOverHour
            payHour = extrapay.payHour
            extrapay.sumOverHour = float(sumOverHour) + overhour + overhour_weekend
            extrapay.payHour = payHour + overhour
            extrapay.save()
        else:
            print('new')
            extrapay = ExtraPay.objects.create(
                empId=emp,
                empName=emp.empName,
                overHourDate='{}-01'.format(overhourDate),
                sumOverHour=overhour+overhour_weekend,
                payHour=overhour+overhour_weekend,
            )

        # OverHour.objects.create(
        #     empId=emp,
        #     empName=service.empName,
        #     overHour=overhour,
        #     overHourWeekDay=overhour_weekend,
        #     overHourCost=overhourcost,
        #     foodCost=foodcosts,
        #     extraPayId=extrapay,
        # )


        print(request.POST)
    return redirect('extrapay:overhour')

