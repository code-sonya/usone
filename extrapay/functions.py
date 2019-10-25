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
    extrapays = ExtraPay.objects.filter(Q(overHourDate__year=todayYear) & Q(overHourDate__month=todayMonth) & Q(empId__empDeptName=empDeptName))
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

            extrapay_dict['empDeptName']=extrapay.empId.empDeptName
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


def cal_fuel(empDeptName, todayYear, todayMonth):
    fuels = Fuel.objects.filter(Q(serviceId__serviceDate__year=todayYear) & Q(serviceId__serviceDate__month=todayMonth) & Q(serviceId__empDeptName=empDeptName) & Q(fuelStatus='Y'))
    oil = Oil.objects.filter(Q(oilDate__year=todayYear) & Q(oilDate__month=todayMonth))
    table = []
    sumEmp = {'sumFuelMoney': 0, 'sumDistance': 0, 'sumDistanceCountry': 0}
    fuelsEmp = fuels.values('serviceId__empName').annotate(countFuel=Count('serviceId__empName'))
    fuelsEmpList = [x['serviceId__empName'] for x in fuelsEmp]
    for employee in fuelsEmpList:
        emp = Employee.objects.get(Q(empName=employee))
        oilMpk = oil.get(Q(carId__carId=emp.carId_id)).mpk
        fuel = fuels.filter(serviceId__empName=employee)
        fuel_dict={'sumDistance': 0,'sumDistanceCountry': 0}
        for f in fuel:
            geolocation = Geolocation.objects.get(Q(serviceId=f.serviceId))
            if geolocation.distanceRatio == 1.2:
                fuel_dict['sumDistance'] += geolocation.distance
            else:
                fuel_dict['sumDistanceCountry'] += geolocation.distance
            fuel_dict['empDeptName'] = f.serviceId.empDeptName
            fuel_dict['empPosition'] = f.serviceId.empId.empPosition.positionName
            fuel_dict['empName'] = f.serviceId.empName
        fuel_dict['sumFuelMoney'] = fuel.aggregate(sumFuelMoney=Sum('fuelMoney'))['sumFuelMoney']
        fuel_dict['oilMpk'] = oilMpk
        sumEmp['sumFuelMoney'] += fuel_dict['sumFuelMoney']
        sumEmp['sumDistance'] += fuel_dict['sumDistance']

        if fuel_dict['sumDistanceCountry'] == 0 and fuel_dict['sumDistance'] != 0:
            fuel_dict['distanceRatio'] = 1.2
            table.append(fuel_dict)
        elif fuel_dict['sumDistanceCountry'] != 0 and fuel_dict['sumDistance'] == 0:
            fuel_dict['distanceRatio'] = 1.0
            fuel_dict['sumDistance'] = fuel_dict['sumDistanceCountry']
            table.append(fuel_dict)
        else:
            fuel_dict['distanceRatio'] = 1.2
            table.append(fuel_dict)
            fuel_dict['distanceRatio'] = 1.0
            fuel_dict['sumDistance'] = fuel_dict['sumDistanceCountry']
            table.append(fuel_dict)

    return table, sumEmp


class Round(Func):
    function = 'ROUND'
    template='%(function)s(%(expressions)s, 2)'
