from django.contrib.auth.models import User
from django.db.models import Q
from .models import OverHour, ExtraPay, Fuel, Oil
from service.models import Servicereport, Vacation, Geolocation
from hr.models import Employee
from scheduler.models import Eventday
import datetime
from usone.security import naverMapId, naverMapKey
from django.db.models import Q, F, Value, FloatField, Max, Sum, Case, When, IntegerField, Count, Func


def cal_overhour(services):
    services_lst = []
    for s in services:
        # 초과 근무 시간 체크
        if s.overHour > 0:
            # 휴일, 평일 체크
            pass
        else:
            print()
    return services_lst

def cal_extraPay(empDeptName, todayYear, todayMonth):
    extrapays = ExtraPay.objects.filter(Q(overHourDate__year=todayYear) &
                                        Q(overHourDate__month=todayMonth) &
                                        Q(empId__empDeptName__in=empDeptName) &
                                        Q(empId__empRewardAvailable='가능')).order_by('empId__empDeptName', 'empId__empPosition')
    table = []
    sumEmp = {'sumoverHour': 0, 'sumcompensatedHour': 0, 'sumoverandfoodCost': 0, 'sumfoodCost': 0, 'sumCost': 0}

    for extrapay in extrapays:
        extrapay_dict = {}
        employee = Employee.objects.get(empId=str(extrapay.empId_id))
        if extrapay.payStatus == 'N':
            sum_overhours = OverHour.objects.filter(
                Q(extraPayId=extrapay.extraPayId) &
                Q(overHourStatus='Y') &
                Q(overHour__gt=0)).aggregate(
                sumOverhour=Sum('overHour'),
                sumFoodCost=Sum('foodCost'))

            sum_foodcosts = OverHour.objects.filter(
                Q(extraPayId=extrapay.extraPayId) &
                Q(overHourStatus='Y') &
                Q(overHour=0)).aggregate(
                sumFoodCost=Sum('foodCost'))

            if ((sum_overhours['sumOverhour']or 0)-(extrapay.compensatedHour or 0))*1.5*employee.empSalary > 200000:
                real_cost = 200000
            else:
                real_cost = ((sum_overhours['sumOverhour']or 0)-(extrapay.compensatedHour or 0))*1.5*employee.empSalary

            extrapay_dict['extraPayId'] = extrapay.extraPayId
            extrapay_dict['empDeptName'] = extrapay.empId.empDeptName
            extrapay_dict['empPosition'] = extrapay.empId.empPosition.positionName
            extrapay_dict['empName'] = extrapay.empName
            extrapay_dict['sumOverhour'] = sum_overhours['sumOverhour'] or 0
            sumEmp['sumoverHour'] += (sum_overhours['sumOverhour'] or 0)
            extrapay_dict['compensatedHour'] = extrapay.compensatedHour or 0
            sumEmp['sumcompensatedHour'] += extrapay.compensatedHour or 0
            extrapay_dict['sumOverhourFoodCost'] = real_cost + (sum_overhours['sumFoodCost'] or 0)
            sumEmp['sumoverandfoodCost'] += real_cost + (sum_overhours['sumFoodCost'] or 0)
            extrapay_dict['sumFoodCost'] = sum_foodcosts['sumFoodCost'] or 0
            sumEmp['sumfoodCost'] += sum_foodcosts['sumFoodCost'] or 0
            extrapay_dict['sumCost'] = real_cost + (sum_overhours['sumFoodCost'] or 0) + (sum_foodcosts['sumFoodCost'] or 0)
            sumEmp['sumCost'] += real_cost + (sum_overhours['sumFoodCost'] or 0) + (sum_foodcosts['sumFoodCost'] or 0)

        else:
            sum_overhours = OverHour.objects.filter(
                Q(extraPayId=extrapay.extraPayId) &
                Q(overHourStatus='Y') &
                Q(overHour__isnull=False)).aggregate(
                sumOverhour=Sum('overHour'),
                sumOverhourWeekday=Sum('overHourWeekDay'),
                sumOverhourCost=Sum('overHourCost'),
                overHourCostWeekDay=Sum('overHourCostWeekDay'),
            )
            if sum_overhours['sumOverhour']:
                sumoverhour = sum_overhours['sumOverhour'] / 24
            else:
                sumoverhour = 0

            if sum_overhours['sumOverhourWeekday']:
                sumoverhourweekday = sum_overhours['sumOverhourWeekday'] / 24
            else:
                sumoverhourweekday = 0

            extrapay_dict['extraPayId'] = extrapay.extraPayId
            extrapay_dict['empDeptName'] = extrapay.empId.empDeptName
            extrapay_dict['empPosition'] = extrapay.empId.empPosition.positionName
            extrapay_dict['empName'] = extrapay.empName
            extrapay_dict['sumOverhour'] = sumoverhour
            extrapay_dict['sumOverhourWeekday'] = sumoverhourweekday
            extrapay_dict['sumOverhourCost'] = sum_overhours['sumOverhourCost'] or 0
            extrapay_dict['overHourCostWeekDay'] = sum_overhours['overHourCostWeekDay'] or 0
            extrapay_dict['sumCost'] = (sum_overhours['sumOverhourCost'] or 0) + (sum_overhours['overHourCostWeekDay'] or 0)
            sumEmp = extrapay_dict

        table.append(extrapay_dict)

    return table, sumEmp


def cal_fuel(todayYear, todayMonth, empDeptName=None):
    fuels = Fuel.objects.filter(
        Q(geolocationId__serviceId__serviceDate__year=todayYear) &
        Q(geolocationId__serviceId__serviceDate__month=todayMonth) &
        Q(fuelStatus='Y')
    )
    oil = Oil.objects.filter(
        Q(oilDate__year=todayYear) &
        Q(oilDate__month=todayMonth)
    )

    if empDeptName:
        fuels = fuels.filter(geolocationId__serviceId__empDeptName=empDeptName)

        fuelsEmp = fuels.values(
            'geolocationId__serviceId__empId',
            'geolocationId__distanceRatio',
        ).annotate(
            empId=F('geolocationId__serviceId__empId'),
            sumDistance=Sum('geolocationId__distance'),
            empDeptName=F('geolocationId__serviceId__empDeptName'),
            empPosition=F('geolocationId__serviceId__empId__empPosition__positionName'),
            empName=F('geolocationId__serviceId__empName'),
            sumFuelMoney=Sum('fuelMoney'),
            sumTollMoney=Sum('geolocationId__tollMoney'),
            sumTotalMoney=F('sumFuelMoney') + F('sumTollMoney'),
            distanceRatio=F('geolocationId__distanceRatio'),
            countFuel=Count('geolocationId__serviceId__empName'),
        )

        for f in fuelsEmp:
            emp = Employee.objects.get(empId=f['empId'])
            oilMpk = oil.get(carId__carId=emp.carId_id).mpk
            f['oilMpk'] = oilMpk

    else:
        fuelsEmp = fuels.aggregate(
            sumDistance=Sum('geolocationId__distance'),
            sumTollMoney=Sum('geolocationId__tollMoney'),
            sumFuelMoney=Sum('fuelMoney'),
            sumTotalMoney=Sum('geolocationId__tollMoney') + Sum('fuelMoney'),
        )

    return fuelsEmp


class Round(Func):
    function = 'ROUND'
    template='%(function)s(%(expressions)s, 2)'
