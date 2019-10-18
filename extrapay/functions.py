from django.contrib.auth.models import User
from django.db.models import Q
from .models import OverHour
from service.models import Servicereport, Vacation
from scheduler.models import Eventday
import datetime
import pycurl
import re
from io import BytesIO
import json
from usone.security import naverMapId, naverMapKey


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


def naver_distance(latlngs):
    start_lat = latlngs[0][0]
    start_lng = latlngs[0][1]
    goal_lat = latlngs[-1][0]
    goal_lng = latlngs[-1][1]
    waypoints = ""
    for i in range(1, len(latlngs)-1):
        waypoints += latlngs[i][1] + ',' + latlngs[i][0] + '|'
    waypoints = waypoints[:-1]
    option = [
        "trafast",          # 실시간 빠른길
        "tracomfort",       # 실시간 편한길
        "traoptimal",       # 실시간 최적길
        "traavoidtoll",     # 무료 우선
        "traavoidcaronly",  # 자동차 전용도로 회피 우선
    ]
    url = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving" + \
          "?start=" + start_lng + "," + start_lat + \
          "&goal=" + goal_lng + "," + goal_lat + \
          "&waypoints=" + waypoints + \
          "&option=" + option[1]

    header = [
        "X-NCP-APIGW-API-KEY-ID: sgk3r29y7a",
        "X-NCP-APIGW-API-KEY: RAqGrso7cuVX2YLFcCMCwENGbxpdCKG0ves2VFhV",
    ]
    buffer = BytesIO()
    c = pycurl.Curl()

    c.setopt(pycurl.HTTPHEADER, header)
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.SSL_VERIFYPEER, False)
    c.perform()
    c.close()

    body = buffer.getvalue().decode('utf-8')
    body = json.loads(body)
    if body['code'] > 0:
        distance = 0
    else:
        distance = round((body['route']['tracomfort'][0]['summary']['distance'] / 1000), 1)
    buffer.close()

    return distance
