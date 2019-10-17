from django.contrib.auth.models import User
from django.db.models import Q
from .models import OverHour
from service.models import Servicereport, Vacation
from scheduler.models import Eventday
import datetime
import pycurl


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


# def naver_distance(lat1, lng1, lat2, lng2):
#