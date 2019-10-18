from django.contrib.auth.models import User
from django.db.models import Q
from .models import OverHour, ExtraPay
from service.models import Servicereport, Vacation
from scheduler.models import Eventday
import datetime
from django.db.models import Q, F, Value, FloatField, Max, Sum, Case, When, IntegerField, Count, Func
# import pycurl


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
        if extrapay.payStatus !='X':
            sum_overhours = OverHour.objects.filter(Q(extraPayId=extrapay.extraPayId) & Q(overHour__gt=0))\
                                            .aggregate(sumOverhour=Sum('overHour'),
                                                sumOverhourCost=Sum('overHourCost'),
                                                sumFoodCost=Sum('foodCost'))
            sum_foodcosts = OverHour.objects.filter(Q(extraPayId=extrapay.extraPayId) & Q(overHour=0))\
                                            .aggregate(sumFoodCost=Sum('foodCost'))

            if sum_overhours['sumOverhourCost'] > 200000:
                real_cost = 200000
            else:
                real_cost = sum_overhours['sumOverhourCost']

            extrapay_dict['extraPayId'] = extrapay.extraPayId
            extrapay_dict['empDeptName'] = extrapay.empId.empDeptName
            extrapay_dict['empPosition'] = extrapay.empId.empPosition.positionName
            extrapay_dict['empName'] = extrapay.empName
            extrapay_dict['sumOverhour'] = sum_overhours['sumOverhour']
            sumEmp['sumoverHour'] += sum_overhours['sumOverhour']
            extrapay_dict['compensatedHour'] = extrapay.compensatedHour or 0
            sumEmp['sumcompensatedHour'] += extrapay.compensatedHour or 0
            extrapay_dict['sumOverhourFoodCost'] = real_cost + (sum_overhours['sumFoodCost'] or 0)
            sumEmp['sumoverandfoodCost'] += real_cost + (sum_overhours['sumFoodCost'] or 0)
            extrapay_dict['sumFoodCost'] = sum_foodcosts['sumFoodCost'] or 0
            sumEmp['sumfoodCost'] += sum_foodcosts['sumFoodCost'] or 0
            extrapay_dict['sumCost'] = real_cost + (sum_overhours['sumFoodCost'] or 0) + (sum_foodcosts['sumFoodCost'] or 0)
            sumEmp['sumCost'] += real_cost + (sum_overhours['sumFoodCost'] or 0) + (sum_foodcosts['sumFoodCost'] or 0)

        else:
            sum_overhours = OverHour.objects.filter(Q(extraPayId=extrapay.extraPayId) & Q(overHour__isnull=False)) \
                .aggregate(
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


class Round(Func):
    function = 'ROUND'
    template='%(function)s(%(expressions)s, 2)'


# def naver_distance(lat1, lng1, lat2, lng2):
#