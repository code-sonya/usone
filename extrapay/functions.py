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

    for extrapay in extrapays:
        print(extrapay)
        sum_overhours = OverHour.objects.filter(Q(extraPayId=extrapay.extraPayId) & Q(overHour__isnull=False)).aggregate(sumOverhour=Sum('overHour'),
                                            sumOverhourWeekDay=Sum('overHourWeekDay'),
                                            sumServicehour=Round(Sum('serviceId__serviceHour')),
                                            sumOverhourCost=Sum('overHourCost'),
                                            sumOverhourCostWeekDay=Sum('overHourCostWeekDay'),
                                            sumFoodCost=Sum('foodCost'))
        sum_foodcosts = OverHour.objects.filter(Q(extraPayId=extrapay.extraPayId) & (Q(overHour__isnull=True) | Q(overHour=0)))\
                                        .aggregate(sumServicehour=Sum('serviceId__serviceHour'), sumFoodCost=Sum('foodCost'))

        # 일반이랑 특수직 따로 따기


class Round(Func):
    function = 'ROUND'
    template='%(function)s(%(expressions)s, 2)'


# def naver_distance(lat1, lng1, lat2, lng2):
#