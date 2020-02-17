# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta
from math import ceil

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

from hr.models import Employee, Department
from service.models import Servicereport, Geolocation
from .models import OverHour, Car, Oil, Fuel, ExtraPay
from .functions import cal_overhour, Round, cal_extraPay, cal_fuel
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
        extrapay = extrapay.filter(
            Q(overHourDate__year=searchYear) &
            Q(overHourDate__month=searchMonth)
        )

    extrapaylist = extrapay.values('overHourDate', 'empId__empDeptName', 'empName', 'sumOverHour', 'compensatedHour', 'compensatedComment', 'extraPayId')
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
    if m == 12:
        enddate = str((datetime(y+1, 1, 1) - timedelta(days=1)).date())
    else:
        enddate = str((datetime(y, m+1, 1) - timedelta(days=1)).date())

    btnStatus = 'N'
    if m == 12:
        if datetime(y+1, 1, 7) > datetime.today():
            btnStatus = 'Y'
    else:
        if datetime(y, m+1, 7) > datetime.today():
            btnStatus = 'Y'
    context = {
        'empId': request.user.employee.empId,
        'startdate': startdate,
        'enddate': enddate,
        'btnStatus': btnStatus,
        'MAP_KEY': MAP_KEY,
        'testMAP_KEY': testMAP_KEY,
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

        geolocationIds = json.loads(request.POST['geolocationId'])
        for geolocationId in geolocationIds:
            geo = Geolocation.objects.get(geolocationId=geolocationId)
            fuelMoney = ceil(geo.distance * geo.distanceRatio * mpk)
            Fuel.objects.create(
                geolocationId=geo,
                fuelMoney=fuelMoney,
            )
    return redirect('extrapay:showfuel')


@login_required
@csrf_exempt
def del_fuel(request):
    if request.method == 'POST':
        fuelIds = json.loads(request.POST['fuelId'])
        for fuelId in fuelIds:
            Fuel.objects.get(fuelId=fuelId).delete()
    return redirect('extrapay:showfuel')


def admin_fuel(request):
    if request.method == 'POST':
        y = int(request.POST['findDate'][:4])
        m = int(request.POST['findDate'][5:7])
    else:
        y = datetime.today().year
        m = datetime.today().month
    startdate = str(datetime(y, m, 1).date())
    if m == 12:
        enddate = str((datetime(y+1, 1, 1) - timedelta(days=1)).date())
    else:
        enddate = str((datetime(y, m+1, 1) - timedelta(days=1)).date())
    context = {
        'yearmonth': '{}-{}'.format(y, m),
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
    if m == 12:
        enddate = str((datetime(y + 1, 1, 1) - timedelta(days=1)).date())
    else:
        enddate = str((datetime(y, m + 1, 1) - timedelta(days=1)).date())
    empName = Employee.objects.get(empId=empId).empName
    empDeptName = Employee.objects.get(empId=empId).empDeptName

    btnStatus = 'N'
    if m == 12:
        approvalDate = datetime(y+1, 1, 15)
    else:
        approvalDate = datetime(y, m+1, 15)
    if approvalDate > datetime.today():
        btnStatus = 'Y'

    context = {
        'startdate': startdate,
        'enddate': enddate,
        'empName': empName,
        'empDeptName': empDeptName,
        'empId': empId,
        'MAP_KEY': MAP_KEY,
        'testMAP_KEY': testMAP_KEY,
        'btnStatus': btnStatus,
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
                Q(geolocationId__serviceId__empId=empId) &
                Q(geolocationId__serviceId__serviceDate__gte=startdate) &
                Q(geolocationId__serviceId__serviceDate__lte=enddate) &
                Q(fuelStatus='N')
            ).annotate(
                serviceId=F('geolocationId__serviceId__serviceId'),
                distance=F('geolocationId__distance'),
                distanceCode=F('geolocationId__distanceCode'),
                serviceDate=F('geolocationId__serviceId__serviceDate'),
                companyName=F('geolocationId__serviceId__companyName__companyName'),
                serviceTitle=F('geolocationId__serviceId__serviceTitle'),
                tollMoney=F('geolocationId__tollMoney'),
                totalMoney=F('tollMoney') + F('fuelMoney')
            )

            services = services.values(
                'fuelId', 'serviceId', 'serviceDate', 'companyName', 'serviceTitle', 'totalMoney',
                'tollMoney', 'fuelMoney', 'comment', 'fuelStatus', 'distance', 'distanceCode',
            )

            structure = json.dumps(list(services), cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')

        elif status == 'YR':
            services = Fuel.objects.select_related().filter(
                Q(geolocationId__serviceId__empId=empId) &
                Q(geolocationId__serviceId__serviceDate__gte=startdate) &
                Q(geolocationId__serviceId__serviceDate__lte=enddate) &
                Q(fuelStatus__in=['Y', 'R'])
            ).annotate(
                serviceId=F('geolocationId__serviceId__serviceId'),
                distance=F('geolocationId__distance'),
                distanceCode=F('geolocationId__distanceCode'),
                serviceDate=F('geolocationId__serviceId__serviceDate'),
                companyName=F('geolocationId__serviceId__companyName__companyName'),
                serviceTitle=F('geolocationId__serviceId__serviceTitle'),
                tollMoney=F('geolocationId__tollMoney'),
                totalMoney=F('tollMoney') + F('fuelMoney'),
            )

            services = services.values(
                'fuelId', 'serviceId', 'serviceDate', 'companyName', 'serviceTitle', 'totalMoney',
                'tollMoney', 'fuelMoney', 'comment', 'fuelStatus', 'distance', 'distanceCode',
            )

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
        elif geo.distanceCode == 6:
            distanceMessage = '이전 데이터 이관으로 출발, 도착지 없음'

        path = [i.split(", ") for i in geo.path[2:-2].split("], [")]

        maxLat = max(geo.beginLatitude, geo.startLatitude, geo.endLatitude, geo.finishLatitude)
        minLat = min(geo.beginLatitude, geo.startLatitude, geo.endLatitude, geo.finishLatitude)
        maxLng = max(geo.beginLongitude, geo.startLongitude, geo.endLongitude, geo.finishLongitude)
        minLng = min(geo.beginLongitude, geo.startLongitude, geo.endLongitude, geo.finishLongitude)
        pathCenterLong = (maxLng + minLng) / 2
        pathCenterLat = (maxLat + minLat) / 2
        differLat = maxLat - minLat
        differLng = maxLng - minLng
        latZoom, stDifferLat = 13, 0.06
        lngZoom, stDifferLng = 13, 0.14
        for i in range(7):
            if differLat < stDifferLat:
                latZoom -= i
                break
            stDifferLat *= 2
        for i in range(7):
            if differLng < stDifferLng:
                lngZoom -= i
                break
            stDifferLng *= 2
        zoom = min(latZoom, lngZoom)

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
            'beginRegion': geo.beginLocation,
            'startRegion': geo.startLocation,
            'finishRegion': geo.finishLocation,
            'comment': geo.comment,
            'serviceId': request.GET['serviceId'],
            'path': path,
            'pathCenterLong': pathCenterLong,
            'pathCenterLat': pathCenterLat,
            'zoom': zoom,
        }

        structure = json.dumps(geos, cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def adminfuel_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    employee = request.user.employee
    empDeptName = employee.empDeptName
    empDeptLevel = employee.departmentName.deptLevel

    fuels = Fuel.objects.select_related()

    if empDeptLevel == 0 or empDeptName in ['경영지원본부', '경영지원실']:
        None
    elif empDeptLevel == 1:
        empDeptNames = Department.objects.filter(parentDept=employee.departmentName).values_list('deptName', flat=True)
        fuels = fuels.filter(
            Q(geolocationId__serviceId__empId__empDeptName__in=empDeptNames) |
            Q(geolocationId__serviceId__empId__empDeptName=empDeptName)
        )
    elif empDeptLevel == 2:
        fuels = fuels.filter(geolocationId__serviceId__empId__empDeptName=empDeptName)

    fuels = fuels.filter(
        Q(geolocationId__serviceId__serviceDate__gte=startdate) &
        Q(geolocationId__serviceId__serviceDate__lte=enddate)
    ).values('geolocationId__serviceId__empId').annotate(
        empId=F('geolocationId__serviceId__empId'),
        empDeptName=F('geolocationId__serviceId__empId__empDeptName'),
        empPosition=F('geolocationId__serviceId__empId__empPosition__positionName'),
        empName=F('geolocationId__serviceId__empId__empName'),
        car=Concat(
            F('geolocationId__serviceId__empId__carId__oilType'),
            Value(', '),
            F('geolocationId__serviceId__empId__carId__carType')
        ),
        progress=Count('fuelStatus', filter=Q(fuelStatus='N')),
        approval=Count('fuelStatus', filter=Q(fuelStatus='Y')),
        reject=Count('fuelStatus', filter=Q(fuelStatus='R')),
        sum_distance=Coalesce(Sum('geolocationId__distance', filter=Q(fuelStatus='Y')), 0),
        sum_tollMoney=Coalesce(Sum('geolocationId__tollMoney', filter=Q(fuelStatus='Y')), 0),
        sum_fuelMoney=Coalesce(Sum('fuelMoney', filter=Q(fuelStatus='Y')), 0),
        sum_totalMoney=F('sum_tollMoney') + F('sum_fuelMoney'),
    )

    fuels = fuels.values(
        'empId', 'empDeptName', 'empPosition', 'empName', 'car', 'progress', 'approval', 'reject',
        'sum_distance', 'sum_fuelMoney', 'sum_tollMoney', 'sum_totalMoney',
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
            Q(geolocationId__serviceId__empId=empId) &
            Q(geolocationId__serviceId__serviceDate__gte=startdate) &
            Q(geolocationId__serviceId__serviceDate__lte=enddate)
        ).values('geolocationId__geolocationId')

        services = Geolocation.objects.select_related().filter(
            Q(serviceId__empId=empId) &
            Q(serviceId__serviceStatus='Y') &
            Q(serviceId__serviceDate__gte=startdate) &
            Q(serviceId__serviceDate__lte=enddate)
        ).exclude(
            geolocationId__in=[i['geolocationId__geolocationId'] for i in fuels]
        ).annotate(
            serviceDate=F('serviceId__serviceDate'),
            companyName=F('serviceId__companyName__companyName'),
            serviceTitle=F('serviceId__serviceTitle'),
            mpk=Value(mpk, output_field=IntegerField()),
        )

        services = services.values(
            'geolocationId', 'serviceId', 'serviceId__serviceId', 'serviceDate', 'companyName',
            'serviceTitle', 'distance', 'distanceCode', 'distanceRatio', 'mpk', 'tollMoney',
            'beginLatitude', 'beginLongitude', 'startLatitude', 'startLongitude',
            'endLatitude', 'endLongitude', 'finishLatitude', 'finishLongitude', 'serviceId__empId__carId'
        )

        for service in services:
            service['fuelMoney'] = ceil(service['distance'] * service['distanceRatio'] * mpk)
            service['totalMoney'] = service['tollMoney'] + service['fuelMoney']
        structure = json.dumps(list(services), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')

    elif status == 'show':
        services = Fuel.objects.select_related().filter(
            Q(geolocationId__serviceId__empId=empId) &
            Q(geolocationId__serviceId__serviceDate__gte=startdate) &
            Q(geolocationId__serviceId__serviceDate__lte=enddate)
        ).annotate(
            serviceId=F('geolocationId__serviceId__serviceId'),
            distance=F('geolocationId__distance'),
            distanceCode=F('geolocationId__distanceCode'),
            serviceDate=F('geolocationId__serviceId__serviceDate'),
            companyName=F('geolocationId__serviceId__companyName__companyName'),
            serviceTitle=F('geolocationId__serviceId__serviceTitle'),
            tollMoney=F('geolocationId__tollMoney'),
            totalMoney=F('tollMoney') + F('fuelMoney'),
        )

        services = services.values(
            'fuelId', 'serviceId', 'serviceDate', 'companyName', 'serviceTitle',
            'fuelMoney', 'fuelStatus', 'comment', 'distance', 'distanceCode', 'tollMoney', 'totalMoney',
        )
        structure = json.dumps(list(services), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_overhour(request, extraPayId):
    extrapay = ExtraPay.objects.filter(
        Q(extraPayId=extraPayId)
    ).values(
        'overHourDate__year', 'overHourDate__month', 'empId__empName', 'empId__empSalary', 'empId__empDeptName',
        'empId__empCode', 'extraPayId', 'empId__empPosition_id__positionName', 'compensatedComment', 'compensatedHour', 'payStatus'
    ).first()
    overhours = OverHour.objects.filter(
        Q(extraPayId=extraPayId) &
        ~Q(overHour=0) &
        Q(overHourStatus='Y')
    ).order_by('overHourStartDate')
    sum_overhours = overhours.aggregate(
        sumOverhour=Sum('overHour'),
        sumOverhourWeekDay=Sum('overHourWeekDay'),
        sumServicehour=Round(Sum('serviceId__serviceHour')),
        sumOverhourCost=Sum('overHourCost'),
        sumOverhourCostWeekDay=Sum('overHourCostWeekDay'),
        sumFoodCost=Sum('foodCost')
    )
    foodcosts = OverHour.objects.filter(
        Q(extraPayId=extraPayId) &
        Q(overHour=0) &
        Q(overHourStatus='Y')
    )
    sum_foodcosts = foodcosts.aggregate(
        sumServicehour=Sum('serviceId__serviceHour'),
        sumFoodCost=Sum('foodCost')
    )

    if extrapay['payStatus'] == 'N':
        real_extraPay = int(((sum_overhours['sumOverhour'] or 0)-(extrapay['compensatedHour'] or 0))*1.5*extrapay['empId__empSalary'])
        if real_extraPay > 200000:
            real_extraPay = 200000

        sum_costs = {
            'extraPayDate': '{}.{}'.format(extrapay['overHourDate__year'], extrapay['overHourDate__month']),
            'overHour': sum_overhours['sumOverhour'],
            'compensatedHour': extrapay['compensatedHour'],
            'extraPayHour': (sum_overhours['sumOverhour'] or 0) - (extrapay['compensatedHour'] or 0),
            'extraPay': real_extraPay,
            'foodCost': int((sum_overhours['sumFoodCost'] or 0) + (sum_foodcosts['sumFoodCost'] or 0)),
            'sumPay': int(real_extraPay + (sum_overhours['sumFoodCost'] or 0) + (sum_foodcosts['sumFoodCost'] or 0))
        }
    else:
        sum_costs = {
            'extraPayDate': '{}.{}'.format(extrapay['overHourDate__year'], extrapay['overHourDate__month']),
            'overHour': (sum_overhours['sumOverhour'] or 0) + (sum_overhours['sumOverhourWeekDay'] or 0),
            'compensatedHour': extrapay['compensatedHour'],
            'extraPayHour': (sum_overhours['sumOverhour'] or 0) + (sum_overhours['sumOverhourWeekDay'] or 0) - (extrapay['compensatedHour'] or 0),
            'extraPay': int((sum_overhours['sumOverhourCost'] or 0) + (sum_overhours['sumOverhourCostWeekDay'] or 0)),
            'foodCost': 0,
            'sumPay': int((sum_overhours['sumOverhourCost'] or 0) + (sum_overhours['sumOverhourCostWeekDay'] or 0)),
        }
    context = {
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
def overhour_all(request):
    if request.method == 'POST':
        todayYear = int(request.POST['searchdate'][:4])
        todayMonth = int(request.POST['searchdate'][5:7])
        today = request.POST['searchdate'][:7]
    else:
        todayYear = datetime.today().year
        todayMonth = datetime.today().month
        today = '{}-{}'.format(todayYear, todayMonth)

    # 현재 조직도 변경 후 인원
    extrapayPlatform, sumPlatform = cal_extraPay(['platform Biz', '솔루션팀', 'DB Expert팀'], todayYear, todayMonth)
    extrapayStrategy, sumStrategy = cal_extraPay(['R&D 전략사업부', 'Technical Architecture팀', 'AI Platform Labs'], todayYear, todayMonth)

    # 예전 퇴사자들도 표시하기 위해
    extrapayInfra, sumInfra = cal_extraPay(['인프라서비스사업팀'], todayYear, todayMonth)
    extrapaySolution, sumSolution = cal_extraPay(['솔루션지원팀'], todayYear, todayMonth)
    extrapayDB, sumDB = cal_extraPay(['DB지원팀'], todayYear, todayMonth)
    extrapaySupport, sumSupport = cal_extraPay(['미정'], todayYear, todayMonth)

    sumEmp = {'sumoverHour': 0, 'sumcompensatedHour': 0, 'sumoverandfoodCost': 0, 'sumfoodCost': 0, 'sumCost': 0}

    for sum in [sumPlatform, sumStrategy, sumInfra, sumSolution, sumDB]:
        sumEmp['sumoverHour'] += sum['sumoverHour']
        sumEmp['sumcompensatedHour'] += sum['sumcompensatedHour']
        sumEmp['sumoverandfoodCost'] += sum['sumoverandfoodCost']
        sumEmp['sumfoodCost'] += sum['sumfoodCost']
        sumEmp['sumCost'] += sum['sumCost']

    sumEmp['sumoverHour'] = round(sumEmp['sumoverHour'], 2)
    sumEmp['sumcompensatedHour'] = round(sumEmp['sumcompensatedHour'], 2)
    sumEmp['sumoverandfoodCost'] = round(sumEmp['sumoverandfoodCost'], 2)
    sumEmp['sumfoodCost'] = round(sumEmp['sumfoodCost'], 2)
    sumEmp['sumCost'] = round(sumEmp['sumCost'], 2)

    sumAll = (sumEmp['sumCost'] or 0) + (sumSupport['sumCost'] or 0)
    extrapayList = [extrapayPlatform, extrapayStrategy, extrapayInfra, extrapaySolution, extrapayDB]
    context = {
        'today': today,
        'todayYear': todayYear,
        'todayMonth': todayMonth,
        'extrapayInfra': extrapayInfra,
        'extrapaySolution': extrapaySolution,
        'extrapayDB': extrapayDB,
        'extrapaySupport': extrapaySupport,
        'sumEmp': sumEmp,
        'sumSupport': sumSupport,
        'sumAll': sumAll,
        'extrapayList': extrapayList,
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

        ## IF문으로 해당 엔지니어의 월별 정보가 extrapay에 있는지 확인하고 없으면 생성
        emp = Employee.objects.get(empId=empId)
        extrapay = ExtraPay.objects.filter(Q(overHourDate__year=overhouYear) &
                                           Q(overHourDate__month=overhourMonth) &
                                           Q(empId=emp)).first()

        if extrapay:
            sumOverHour = extrapay.sumOverHour
            extrapay.sumOverHour = float(sumOverHour) + overhour + overHourWeekDay
            extrapay.save()
        else:
            extrapay = ExtraPay.objects.create(
                empId=emp,
                empName=emp.empName,
                overHourDate='{}-01'.format(overhourDate),
                sumOverHour=overhour+overHourWeekDay,
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

    for a, b, c in zip(extraPayId, compensatedHour, compensatedComment):
        extraPay = ExtraPay.objects.get(extraPayId=a)
        if b != '':
            extraPay.compensatedHour = float(b)
        extraPay.compensatedComment = c
        extraPay.save()

    return redirect('extrapay:overhour')


@login_required
def view_extrapay_pdf(request, yearmonth):
    todayYear = int(yearmonth[:4])
    todayMonth = int(yearmonth[5:7])

    # 현재 조직도 변경 후 인원
    extrapayPlatform, sumPlatform = cal_extraPay(['platform Biz', '솔루션팀', 'DB Expert팀'], todayYear, todayMonth)
    extrapayStrategy, sumStrategy = cal_extraPay(['R&D 전략사업부', 'Technical Architecture팀', 'AI Platform Labs'], todayYear, todayMonth)

    # 예전 퇴사자들도 표시하기 위해
    extrapayInfra, sumInfra = cal_extraPay(['인프라서비스사업팀'], todayYear, todayMonth)
    extrapaySolution, sumSolution = cal_extraPay(['솔루션지원팀'], todayYear, todayMonth)
    extrapayDB, sumDB = cal_extraPay(['DB지원팀'], todayYear, todayMonth)
    extrapaySupport, sumSupport = cal_extraPay(['미정'], todayYear, todayMonth)

    sumEmp = {'sumoverHour': 0, 'sumcompensatedHour': 0, 'sumoverandfoodCost': 0, 'sumfoodCost': 0, 'sumCost': 0}
    extrapayList = [extrapayPlatform, extrapayStrategy, extrapayInfra, extrapaySolution, extrapayDB]
    for sum in [sumPlatform, sumStrategy, sumInfra, sumSolution, sumDB]:
        sumEmp['sumoverHour'] += sum['sumoverHour']
        sumEmp['sumcompensatedHour'] += sum['sumcompensatedHour']
        sumEmp['sumoverandfoodCost'] += sum['sumoverandfoodCost']
        sumEmp['sumfoodCost'] += sum['sumfoodCost']
        sumEmp['sumCost'] += sum['sumCost']

    sumEmp['sumoverHour'] = round(sumEmp['sumoverHour'], 2)
    sumEmp['sumcompensatedHour'] = round(sumEmp['sumcompensatedHour'], 2)
    sumEmp['sumoverandfoodCost'] = round(sumEmp['sumoverandfoodCost'], 2)
    sumEmp['sumfoodCost'] = round(sumEmp['sumfoodCost'], 2)
    sumEmp['sumCost'] = round(sumEmp['sumCost'], 2)

    sumAll = (sumEmp['sumCost'] or 0) + (sumSupport['sumCost'] or 0)
    extrapayList = [extrapayPlatform, extrapayStrategy, extrapayInfra, extrapaySolution, extrapayDB]
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
        'extrapayList': extrapayList,
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


@login_required
def post_distance(request):
    if request.method == 'POST':
        geo = Geolocation.objects.get(serviceId=request.POST['serviceId'])
        geo.distance = request.POST['distance']
        geo.comment = request.POST['comment']
        geo.beginLocation = request.POST['beginRegion']
        geo.startLocation = request.POST['startRegion']
        geo.endLocation = request.POST['startRegion']
        geo.finishLocation = request.POST['finishRegion']
        geo.save()
        return redirect('extrapay:showfuel')


@login_required
def show_salarys(request):
    template = loader.get_template('extrapay/showsalarys.html')

    if request.method == "POST":
        empName = request.POST['empName']
        filter = 'Y'

    else:
        empName = ''
        filter = 'N'

    employee = Employee.objects.filter(
        Q(empStatus='Y') &
        Q(empRewardAvailable='가능') &
        Q(empSalary=0)
    )

    context = {
        'filter': filter,
        'empName': empName,
        'employee': employee,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def salary_asjson(request):
    empName = request.POST['empName']
    employee = Employee.objects.filter(
        Q(empStatus='Y') &
        Q(empRewardAvailable='가능') &
        Q(empSalary__gt=0)
    )
    if empName:
        employee = Employee.objects.filter(Q(empId=empName))

    emplist = employee.values('empDeptName', 'empName', 'empSalary', 'empId')
    structure = json.dumps(list(emplist), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def save_salarytable(request):
    empSalary = request.GET.getlist('empSalary')
    empId = request.GET.getlist('empId')

    for a, b in zip(empId, empSalary):
        employee = Employee.objects.get(empId=a)
        if b != '':
            employee.empSalary = float(b)
            employee.save()

    return redirect('extrapay:showsalarys')


@login_required
def post_salary(request):
    if request.method == "POST":
        empId = request.POST['empId']
        empSalary = request.POST['empSalary']

        employee = Employee.objects.get(empId=empId)
        if empSalary != '':
            employee.empSalary = float(empSalary)
            employee.save()

    return redirect('extrapay:showsalarys')


@login_required
def view_overhour_pdf(request, extraPayId):
    extrapay = ExtraPay.objects.filter(Q(extraPayId=extraPayId)) \
        .values('overHourDate__year', 'overHourDate__month', 'empId__empName', 'empId__empSalary', 'empId__empDeptName', 'empId__empCode', 'extraPayId', 'empId__empPosition_id__positionName',
                'compensatedComment', 'compensatedHour', 'payStatus').first()
    overhours = OverHour.objects.filter(Q(extraPayId=extraPayId) &
                                        ~Q(overHour=0) &
                                        Q(overHourStatus='Y'))
    sum_overhours = overhours.aggregate(sumOverhour=Sum('overHour'),
                                        sumOverhourWeekDay=Sum('overHourWeekDay'),
                                        sumServicehour=Round(Sum('serviceId__serviceHour')),
                                        sumOverhourCost=Sum('overHourCost'),
                                        sumOverhourCostWeekDay=Sum('overHourCostWeekDay'),
                                        sumFoodCost=Sum('foodCost'))
    foodcosts = OverHour.objects.filter(Q(extraPayId=extraPayId) &
                                        Q(overHour=0) &
                                        Q(overHourStatus='Y'))
    sum_foodcosts = foodcosts.aggregate(sumServicehour=Sum('serviceId__serviceHour'),
                                        sumFoodCost=Sum('foodCost'))

    if extrapay['payStatus'] == 'N':
        real_extraPay = int(((sum_overhours['sumOverhour'] or 0) - (extrapay['compensatedHour'] or 0)) * 1.5 * extrapay['empId__empSalary'])
        if real_extraPay > 200000:
            real_extraPay = 200000

        sum_costs = {
            'extraPayDate': '{}.{}'.format(extrapay['overHourDate__year'], extrapay['overHourDate__month']),
            'overHour': sum_overhours['sumOverhour'],
            'compensatedHour': extrapay['compensatedHour'],
            'extraPayHour': (sum_overhours['sumOverhour'] or 0) - (extrapay['compensatedHour'] or 0),
            'extraPay': real_extraPay,
            'foodCost': int((sum_overhours['sumFoodCost'] or 0) + (sum_foodcosts['sumFoodCost'] or 0)),
            'sumPay': int(real_extraPay + (sum_overhours['sumFoodCost'] or 0) + (sum_foodcosts['sumFoodCost'] or 0))
        }
    else:
        sum_costs = {
            'extraPayDate': '{}.{}'.format(extrapay['overHourDate__year'], extrapay['overHourDate__month']),
            'overHour': sum_overhours['sumOverhour'] + sum_overhours['sumOverhourWeekDay'],
            'compensatedHour': extrapay['compensatedHour'],
            'extraPayHour': sum_overhours['sumOverhour'] + sum_overhours['sumOverhourWeekDay'] - (extrapay['compensatedHour'] or 0),
            'extraPay': int(sum_overhours['sumOverhourCost'] + sum_overhours['sumOverhourCostWeekDay']),
            'foodCost': 0,
            'sumPay': int(sum_overhours['sumOverhourCost'] + sum_overhours['sumOverhourCostWeekDay']),
        }
    context = {
        'overhour': overhours,
        'extrapay': extrapay,
        'foodcosts': foodcosts,
        'sum_overhours': sum_overhours,
        'sum_foodcosts': sum_foodcosts,
        'sum_costs': sum_costs,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{}님시간외수당근무내역.pdf"'.format(extrapay['empId__empName'])

    template = get_template('extrapay/viewoverhourpdf.html')
    html = template.render(context, request)
    # create a pdf
    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@login_required
@csrf_exempt
def delete_overhour(request):
    if request.method == 'POST':
        try:
            overHourId = request.POST.get('overHourId', None)
            overhour = OverHour.objects.get(overHourId=overHourId)
            extraPayId = str(overhour.extraPayId_id)
            extrapay = ExtraPay.objects.get(extraPayId=extraPayId)
            extrapay.sumOverHour = extrapay.sumOverHour - overhour.overHour
            extrapay.save()
            overhour.overHourStatus = 'D'
            overhour.save()
            return redirect('extrapay:viewoverhour', extraPayId)
        except Exception as e:
            print(e)
            return redirect('extrapay:viewoverhour', extraPayId)

    else:
        print('else')
        return HttpResponse('오류발생! 관리자에게 문의하세요 :(')


def view_fuel_pdf(request, yearmonth):
    todayYear = int(yearmonth[:4])
    todayMonth = int(yearmonth[5:7])

    fuels = [
        cal_fuel(todayYear, todayMonth, '경영지원본부'),
        cal_fuel(todayYear, todayMonth, '경영지원실'),
        cal_fuel(todayYear, todayMonth, '인프라솔루션사업부'),
        cal_fuel(todayYear, todayMonth, '영업팀'),
        cal_fuel(todayYear, todayMonth, 'R&D 전략사업부'),
        cal_fuel(todayYear, todayMonth, 'Technical Architecture팀'),
        cal_fuel(todayYear, todayMonth, 'AI Platform Labs'),
        cal_fuel(todayYear, todayMonth, 'Platform Biz'),
        cal_fuel(todayYear, todayMonth, '솔루션팀'),
        cal_fuel(todayYear, todayMonth, 'DB Expert팀'),
    ]

    summary = cal_fuel(todayYear, todayMonth)

    context = {
        'todayYear': todayYear,
        'todayMonth': todayMonth,
        'fuels': fuels,
        'summary': summary,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{}년{}월유류비신청현황.pdf"'.format(todayYear, todayMonth)

    template = get_template('extrapay/viewfuelpdf.html')
    html = template.render(context, request)
    # create a pdf
    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response



