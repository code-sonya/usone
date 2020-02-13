import datetime
import os
import math
import pycurl
import re
from io import BytesIO
import json

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import QueryDict

from scheduler.models import Eventday
from usone.security import naverMapId, naverMapKey
from .models import Servicereport, Vacation


def date_list(startDatetime, endDatetime):
    startDate = datetime.datetime(year=int(startDatetime[:4]), month=int(startDatetime[5:7]), day=int(startDatetime[8:10]))
    endDate = datetime.datetime(year=int(endDatetime[:4]), month=int(endDatetime[5:7]), day=int(endDatetime[8:10]))
    dateRange = [(startDate + datetime.timedelta(days=x)).date() for x in range(0, (endDate - startDate).days + 1)]
    return dateRange


def month_list(startDatetime, endDatetime):
    startDatetime = datetime.datetime(year=int(startDatetime[:4]), month=int(startDatetime[5:7]), day=int(startDatetime[8:10]))
    endDatetime = datetime.datetime(year=int(endDatetime[:4]), month=int(endDatetime[5:7]), day=int(endDatetime[8:10]))

    monthRange = []
    insertDate = startDatetime
    while insertDate <= endDatetime:
        monthRange.append(insertDate.date())
        insertDate = insertDate + relativedelta(months=1)
    return monthRange


def str_to_timedelta_hour(str_endDatetime, str_startDatetime):
    e = datetime.datetime(year=int(str(str_endDatetime)[:4]), month=int(str(str_endDatetime)[5:7]), day=int(str(str_endDatetime)[8:10]),
                          hour=int(str(str_endDatetime)[11:13]), minute=int(str(str_endDatetime)[14:16]), second=0)
    s = datetime.datetime(year=int(str(str_startDatetime)[:4]), month=int(str(str_startDatetime)[5:7]), day=int(str(str_startDatetime)[8:10]),
                          hour=int(str(str_startDatetime)[11:13]), minute=int(str(str_startDatetime)[14:16]), second=0)
    return round((e-s).total_seconds() / 60 / 60, 1)


def is_holiday(date):
    event = Eventday.objects.filter(Q(eventDate=date) & Q(eventType='휴일'))
    if event.count():
        return True
    else:
        return False


def work_hours(start, end):
    result = end - start
    return int(result.days * 24 + result.seconds / 3600) + 1


def overtime(str_start_datetime, str_end_datetime):
    is_holiday_startdate = is_holiday(datetime.datetime.strptime(str_start_datetime[:10], "%Y-%m-%d").date())
    is_holiday_enddate = is_holiday(datetime.datetime.strptime(str_end_datetime[:10], "%Y-%m-%d").date())
    d_start = pd.Timestamp(str_start_datetime)
    d_finish = pd.Timestamp(str_end_datetime)

    minute_sum = 0

    s_week = d_start.weekday()
    f_week = d_finish.weekday()

    if s_week in [5, 6] or is_holiday_startdate != 0:  # 주말이거나 공휴일 일때
        if d_start.minute != 0:
            minute_sum += (60 - d_start.minute)
            d_start = d_start + datetime.timedelta(minutes=(60 - d_start.minute))

    else:  # 평일 일때
        if d_start.minute != 0:  # 정각 시작하지 않은 경우
            if d_start.hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # 시작 시각이 초과 근무에 해당 할 경우
                minute_sum += (60 - d_start.minute)
                d_start = d_start + datetime.timedelta(minutes=(60 - d_start.minute))
            else:  # 초과 근무에 해당 하지 않는 경우
                d_start = d_start + datetime.timedelta(minutes=(60 - d_start.minute))

    if f_week in [5, 6] or is_holiday_enddate != 0:  # 주말이거나 공휴일 일때
        if d_finish.minute != 0:
            minute_sum += d_finish.minute
            d_finish = d_finish - datetime.timedelta(minutes=d_finish.minute)

    else:  # 평일 일때
        if d_finish.minute != 0:  # 정각에 끝나지 않은 경우
            if d_finish.hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # 종료 시각이 초과 근무에 해당 할 경우
                minute_sum += d_finish.minute
                d_finish = d_finish - datetime.timedelta(minutes=d_finish.minute)
            else:
                d_finish = d_finish - datetime.timedelta(minutes=d_finish.minute)


    for i in range(0, work_hours(d_start, d_finish), 1):
        a = (d_start + datetime.timedelta(hours=i))
        event_a = is_holiday(a.date())
        a_week = a.weekday()

        if d_start <= a <= d_finish:
            if a_week in [5, 6] or event_a != 0:  # 주말이나 공휴일
                if d_start.date() == d_finish.date():
                    minute_sum += int((d_finish - d_start).seconds / 60)
                    break
                elif d_finish == a:
                    pass
                else:
                    minute_sum += 60

            else:  # 평일
                if int(a.hour) in [0, 1, 2, 3, 4, 5, 22, 23]:
                    if d_finish == a:
                        pass
                    else:
                        minute_sum += 60

    return round((int(minute_sum) / 60), 1)


def round_down(startDatetime, endDatetime):
    diff = endDatetime - startDatetime
    h = (diff.days * 24) + (diff.seconds / 3600)
    m = h - int(h)
    if m < 1/6:
        return int(h)
    elif m < 2/6:
        return int(h) + 0.17
    elif m < 3/6:
        return int(h) + 0.33
    elif m < 4/6:
        return int(h) + 0.5
    elif m < 5/6:
        return int(h) + 0.67
    else:
        return int(h) + 0.83


def overtime_extrapay(startDatetime, endDatetime):
    overtime = 0
    minDate = datetime.datetime(3000, 1, 31, 1, 0, 0)
    maxDate = datetime.datetime(1999, 1, 31, 1, 0, 0)
    startDatetime = pd.Timestamp(startDatetime)
    endDatetime = pd.Timestamp(endDatetime)
    beforeOvertime = datetime.datetime(startDatetime.year, startDatetime.month, startDatetime.day, 6, 0)
    startOvertime = datetime.datetime(startDatetime.year, startDatetime.month, startDatetime.day, 22, 0)
    endOvertime = datetime.datetime(startDatetime.year, startDatetime.month, startDatetime.day, 6, 0) + datetime.timedelta(days=1)

    # 같은날이면 초과근무 일수도 있고 아닐수도 있음.
    if startDatetime.date() == endDatetime.date():
        # 주말 (여기에 공휴일도 넣어줘야 함)
        if startDatetime.weekday() >= 5 or is_holiday(startDatetime.date()) != 0:
            if startDatetime < minDate:
                minDate = startDatetime
            if endDatetime > maxDate:
                maxDate = endDatetime
            overtime += round_down(startDatetime, endDatetime)
        # 평일
        else:
            # 같은날 06:00 보다 이전에 시작하는 경우
            if startDatetime <= beforeOvertime:
                if startDatetime < minDate:
                    minDate = startDatetime
                if beforeOvertime > maxDate:
                    maxDate = beforeOvertime
                overtime += round_down(startDatetime, beforeOvertime)
            # 같은날 22:00 보다 끝나는 시간이 크다면 초과근무 맞음
            if endDatetime > startOvertime:
                if startOvertime < minDate:
                    minDate = startOvertime
                if endDatetime > maxDate:
                    maxDate = endDatetime
                overtime += round_down(startOvertime, endDatetime)

    # 다른날이면 무조건 초과근무 있음.
    else:
        tempStartDatetime = startDatetime
        tempEndDatetime = min(endDatetime, endOvertime)
        tempStartOvertime = startOvertime
        tempEndOvertime = endOvertime

        # 주말 (여기에 공휴일도 넣어줘야 함)
        if tempStartDatetime.weekday() >= 5 or is_holiday(tempStartDatetime.date()) != 0:
            if tempStartDatetime < minDate:
                minDate = tempStartDatetime
            if tempEndDatetime > maxDate:
                maxDate = tempEndDatetime
            overtime += round_down(tempStartDatetime, tempEndDatetime)
        # 평일
        else:
            if tempStartDatetime <= beforeOvertime:
                if tempStartDatetime < minDate:
                    minDate = tempStartDatetime
                if beforeOvertime > maxDate:
                    maxDate = beforeOvertime
                overtime += round_down(tempStartDatetime, beforeOvertime)

            if tempStartOvertime < minDate:
                minDate = tempStartOvertime
            if tempEndDatetime > maxDate:
                maxDate = tempEndDatetime
            overtime += round_down(tempStartOvertime, tempEndDatetime)

        while tempEndDatetime != endDatetime:
            tempStartOvertime = tempStartOvertime + datetime.timedelta(days=1)
            tempEndOvertime = tempEndOvertime + datetime.timedelta(days=1)
            tempStartDatetime = tempEndDatetime
            tempEndDatetime = min(endDatetime, tempEndOvertime)

            # 주말 (여기에 공휴일도 넣어줘야 함)
            if tempStartDatetime.weekday() >= 5 or is_holiday(startDatetime.date()) != 0:
                if tempStartDatetime < minDate:
                    minDate = tempStartDatetime
                if tempEndDatetime > maxDate:
                    maxDate = tempEndDatetime
                overtime += round_down(tempStartDatetime, tempEndDatetime)
            # 평일
            elif tempEndDatetime > tempStartOvertime:
                if tempStartOvertime < minDate:
                    minDate = tempStartOvertime
                if tempEndDatetime > maxDate:
                    maxDate = tempEndDatetime
                overtime += round_down(tempStartOvertime, tempEndDatetime)

    if overtime == 0:
        minDate = None
        maxDate = None

    return overtime, overtime, minDate, maxDate


# 이현수대리 조기출근
def overtime_extrapay_etc(startDatetime, endDatetime):
    overtime = 0
    minDate = datetime.datetime(3000, 1, 31, 1, 0, 0)
    maxDate = datetime.datetime(1999, 1, 31, 1, 0, 0)
    startDatetime = pd.Timestamp(startDatetime)
    endDatetime = pd.Timestamp(endDatetime)
    beforeOvertime = datetime.datetime(startDatetime.year, startDatetime.month, startDatetime.day, 6, 0)
    startOvertime = datetime.datetime(startDatetime.year, startDatetime.month, startDatetime.day, 22, 0)
    endOvertime = datetime.datetime(startDatetime.year, startDatetime.month, startDatetime.day + 1, 6, 0)
    beforeOvertime2 = datetime.datetime(startDatetime.year, startDatetime.month, startDatetime.day, 9, 0)
    startOvertime2 = datetime.datetime(startDatetime.year, startDatetime.month, startDatetime.day, 7, 30)

    # 같은날이면 초과근무 일수도 있고 아닐수도 있음.
    if startDatetime.date() == endDatetime.date():
        # 주말 (여기에 공휴일도 넣어줘야 함)
        if startDatetime.weekday() >= 5 or is_holiday(startDatetime.date()) != 0:
            if startDatetime < minDate:
                minDate = startDatetime
            if endDatetime > maxDate:
                maxDate = endDatetime
            overtime += round_down(startDatetime, endDatetime)
        # 평일
        else:
            # 같은날 06:00 보다 이전에 시작하는 경우
            if startDatetime <= beforeOvertime:
                if startDatetime < minDate:
                    minDate = startDatetime
                if beforeOvertime > maxDate:
                    maxDate = beforeOvertime
                overtime += round_down(startDatetime, beforeOvertime)

            # 같은날 07:30 ~ 09:00 사이에 근무하면 초과근무 맞음
            if startDatetime <= beforeOvertime2 or endDatetime <= startOvertime2:
                tmpStartDatetime = startDatetime
                tmpEndDatetime = endDatetime
                if startDatetime < startOvertime2:
                    tmpStartDatetime = startOvertime2
                if endDatetime > beforeOvertime2:
                    tmpEndDatetime = beforeOvertime2
                if tmpStartDatetime < minDate:
                    minDate = tmpStartDatetime
                if tmpEndDatetime > maxDate:
                    maxDate = tmpEndDatetime
                overtime += round_down(tmpStartDatetime, tmpEndDatetime)
                # 같은날 22:00 보다 끝나는 시간이 크다면 초과근무 맞음
            if endDatetime > startOvertime:
                if startOvertime < minDate:
                    minDate = startOvertime
                if endDatetime > maxDate:
                    maxDate = endDatetime
                overtime += round_down(startOvertime, endDatetime)

    # 다른날이면 무조건 초과근무 있음.
    else:
        tempStartDatetime = startDatetime
        tempEndDatetime = min(endDatetime, endOvertime)
        tempStartOvertime = startOvertime
        tempEndOvertime = endOvertime

        # 주말 (여기에 공휴일도 넣어줘야 함)
        if tempStartDatetime.weekday() >= 5 or is_holiday(tempStartDatetime.date()) != 0:
            if tempStartDatetime < minDate:
                minDate = tempStartDatetime
            if tempEndDatetime > maxDate:
                maxDate = tempEndDatetime
            overtime += round_down(tempStartDatetime, tempEndDatetime)
        # 평일
        else:
            # 06:00 보다 이전에 시작하는 경우
            if tempStartDatetime <= beforeOvertime:
                if tempStartDatetime < minDate:
                    minDate = tempStartDatetime
                if beforeOvertime > maxDate:
                    maxDate = beforeOvertime
                overtime += round_down(tempStartDatetime, beforeOvertime)

            # 07:30 ~ 09:00 사이에 근무하면 초과근무 맞음
            if startDatetime <= beforeOvertime2:
                if startDatetime < minDate:
                    minDate = startDatetime
                if endDatetime < beforeOvertime2:
                    maxDate = beforeOvertime2
                if startDatetime < startOvertime2:
                    overtime += round_down(startOvertime2, beforeOvertime2)
                else:
                    overtime += round_down(startDatetime, beforeOvertime2)

            if tempStartOvertime < minDate:
                minDate = tempStartOvertime
            if tempEndDatetime > maxDate:
                maxDate = tempEndDatetime
            overtime += round_down(tempStartOvertime, tempEndDatetime)

        while tempEndDatetime != endDatetime:
            tempStartOvertime = tempStartOvertime + datetime.timedelta(days=1)
            tempEndOvertime = tempEndOvertime + datetime.timedelta(days=1)
            tempStartDatetime = tempEndDatetime
            tempEndDatetime = min(endDatetime, tempEndOvertime)
            print(tempStartOvertime, tempEndOvertime, tempStartDatetime, tempEndDatetime)

            # 주말 (여기에 공휴일도 넣어줘야 함)
            if tempStartDatetime.weekday() >= 5 or is_holiday(tempStartDatetime.date()) != 0:
                if tempStartDatetime < minDate:
                    minDate = tempStartDatetime
                if tempEndDatetime > maxDate:
                    maxDate = tempEndDatetime
                overtime += round_down(tempStartDatetime, tempEndDatetime)
            # 평일
            elif tempEndDatetime > tempStartOvertime:
                if tempStartOvertime < minDate:
                    minDate = tempStartOvertime
                if tempEndDatetime > maxDate:
                    maxDate = tempEndDatetime
                overtime += round_down(tempStartOvertime, tempEndDatetime)

    if overtime == 0:
        minDate = None
        maxDate = None

    return overtime, overtime, minDate, maxDate


def dayreport_query2(empDeptName, day):
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    Date_min = datetime.datetime.combine(Date, datetime.datetime.min.time())
    Date_max = datetime.datetime.combine(Date, datetime.datetime.max.time())
    if datetime.datetime.weekday(Date) >= 5 or Eventday.objects.filter(Q(eventDate=Date) & Q(eventType='휴일')):
        holiday = True
    else:
        holiday = False

    serviceDept = Servicereport.objects.filter(
        Q(empDeptName=empDeptName) &
        (Q(serviceBeginDatetime__lte=Date_max) & Q(serviceFinishDatetime__gte=Date_min))
    ).order_by('serviceBeginDatetime')

    vacationDept = Vacation.objects.filter(
        Q(empDeptName=empDeptName) &
        Q(vacationDate=Date) &
        (Q(vacationStatus='Y') | Q(vacationStatus='N'))
    )

    inDept = User.objects.filter(
        Q(employee__empDeptName=empDeptName) &
        Q(employee__empStatus='Y')
    ).exclude(
        Q(employee__empId__in=serviceDept.values('empId')) |
        Q(employee__empId__in=vacationDept.values('empId'))
    )

    listService = []
    listEducation = []
    listVacation = []

    for service in serviceDept:
        if service.serviceType.typeName == '상주' or service.serviceType.typeName == '프로젝트상주':
            flag = '상주'
        elif service.directgo == 'Y':
            flag = '직출'
        else:
            flag = ''

        if service.serviceType.typeName == '':
            listEducation.append({
                'serviceId': service.serviceId,
                'flag': flag,
                'empName': service.empName,
                'serviceBeginDatetime': service.serviceBeginDatetime,
                'serviceFinishDatetime': service.serviceFinishDatetime,
                'serviceStatus': service.serviceStatus,
                'serviceTitle': service.serviceTitle,
                'sortKey': service.empId.empRank,
            })
        else:
            listService.append({
                'serviceId': service.serviceId,
                'flag': flag,
                'empName': service.empName,
                'serviceBeginDatetime': service.serviceBeginDatetime,
                'serviceFinishDatetime': service.serviceFinishDatetime,
                'serviceStatus': service.serviceStatus,
                'companyName': service.companyName,
                'serviceType': service.serviceType.typeName,
                'serviceTitle': service.serviceTitle,
                'sortKey': service.empId.empRank,
            })

    if not holiday:
        for emp in inDept:
            listService.append({
                'serviceId': '',
                'flag': '',
                'empName': emp.employee.empName,
                'serviceBeginDatetime': datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 9, 0),
                'serviceFinishDatetime': datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 18, 0),
                'serviceStatus': '',
                'companyName': emp.employee.dispatchCompany,
                'serviceType': '',
                'serviceTitle': emp.employee.message,
                'sortKey': emp.employee.empRank,
            })

        for vacation in vacationDept:
            if vacation.vacationStatus == 'Y':
                vacationStatus = ''
            elif vacation.vacationStatus == 'N':
                vacationStatus = '(결재중)'
            listVacation.append({
                'empName': vacation.empName,
                'serviceBeginDatetime': Date,
                'vacationType': vacation.vacationType[:2],
                'vacationStatus': vacationStatus,
                'sortKey': vacation.empId.empRank,
            })

            if vacation.vacationType != '일차' and vacation.empId.empId not in serviceDept.values_list('empId', flat=True):
                if vacation.empId.dispatchCompany == '내근':
                    flag = ''
                else:
                    flag = '상주'

                if vacation.vacationType == '오전반차':
                    startDateTime = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 14, 0)
                    endDateTime = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 18, 0)
                elif vacation.vacationType == '오후반차':
                    startDateTime = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 9, 0)
                    endDateTime = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 14, 0)

                listService.append({
                    'serviceId': '',
                    'flag': flag,
                    'empName': vacation.empName,
                    'serviceBeginDatetime': startDateTime,
                    'serviceFinishDatetime': endDateTime,
                    'serviceStatus': '',
                    'companyName': vacation.empId.dispatchCompany,
                    'serviceType': '',
                    'serviceTitle': vacation.empId.message,
                    'sortKey': vacation.empId.empRank,
                })

    listService.sort(key=lambda x: x['sortKey'])
    listEducation.sort(key=lambda x: x['sortKey'])
    listVacation.sort(key=lambda x: x['sortKey'])

    queryService = []
    queryEducation = []
    queryVacation = []

    for l in listService:
        temp = QueryDict('', mutable=True)
        temp.update(l)
        queryService.append(temp)
    for l in listEducation:
        temp = QueryDict('', mutable=True)
        temp.update(l)
        queryEducation.append(temp)
    for l in listVacation:
        temp = QueryDict('', mutable=True)
        temp.update(l)
        queryVacation.append(temp)

    return queryService, queryEducation, queryVacation


def dayreport_query(empDeptName, day):
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    Date_min = datetime.datetime.combine(Date, datetime.datetime.min.time())
    Date_max = datetime.datetime.combine(Date, datetime.datetime.max.time())

    # 일정
    serviceDept = Servicereport.objects.filter(
        Q(empId__empDeptName__in=empDeptName) &
        (Q(serviceBeginDatetime__lte=Date_max) & Q(serviceFinishDatetime__gte=Date_min))
    ).order_by('serviceBeginDatetime')

    # 휴가
    vacationDept = Vacation.objects.filter(
        Q(empId__empDeptName__in=empDeptName) &
        Q(vacationDate=Date) &
        (Q(vacationStatus='Y') | Q(vacationStatus='N'))
    )

    listService = []
    listEducation = []
    listVacation = []

    for service in serviceDept:
        if service.serviceType.typeName == '상주' or service.serviceType.typeName == '프로젝트상주':
            flag = '상주'
        elif service.directgo == 'Y':
            flag = '직출'
        else:
            flag = ''

        if service.serviceType.typeName == '교육':
            listEducation.append({
                'serviceId': service.serviceId,
                'flag': flag,
                'empName': service.empName,
                'serviceBeginDatetime': service.serviceBeginDatetime,
                'serviceFinishDatetime': service.serviceFinishDatetime,
                'serviceStatus': service.serviceStatus,
                'serviceTitle': service.serviceTitle,
                'sortKey': service.empId.empRank,
            })
        else:
            listService.append({
                'serviceId': service.serviceId,
                'flag': flag,
                'empName': service.empName,
                'serviceBeginDatetime': service.serviceBeginDatetime,
                'serviceFinishDatetime': service.serviceFinishDatetime,
                'serviceStatus': service.serviceStatus,
                'companyName': service.companyName,
                'serviceType': service.serviceType.typeName,
                'serviceTitle': service.serviceTitle,
                'sortKey': service.empId.empRank,
            })

    # # 내근 추가 전
    # for vacation in vacationDept:
    #     vacationStatus = ''
    #     if vacation.vacationStatus == 'N':
    #         vacationStatus = '(결재중)'
    #     listVacation.append({
    #         'empName': vacation.empName,
    #         'serviceBeginDatetime': Date,
    #         'vacationType': vacation.vacationType[:2],
    #         'vacationStatus': vacationStatus,
    #         'sortKey': vacation.empId.empRank,
    #     })

    # 내근 추가
    if datetime.datetime.weekday(Date) >= 5 or Eventday.objects.filter(Q(eventDate=Date) & Q(eventType='휴일')):
        holiday = True
    else:
        holiday = False

    inDept = User.objects.filter(
        Q(employee__empDeptName__in=empDeptName) &
        Q(employee__empStatus='Y')
    ).exclude(
        Q(employee__empId__in=serviceDept.values('empId')) |
        Q(employee__empId__in=vacationDept.values('empId'))
    )

    if not holiday:
        for emp in inDept:
            listService.append({
                'serviceId': '',
                'flag': '',
                'empName': emp.employee.empName,
                'serviceBeginDatetime': datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 9, 0),
                'serviceFinishDatetime': datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 18, 0),
                'serviceStatus': '',
                'companyName': emp.employee.dispatchCompany,
                'serviceType': '',
                'serviceTitle': emp.employee.message,
                'sortKey': emp.employee.empRank,
            })

        for vacation in vacationDept:
            if vacation.vacationStatus == 'Y':
                vacationStatus = ''
            elif vacation.vacationStatus == 'N':
                vacationStatus = '(결재중)'
            listVacation.append({
                'empName': vacation.empName,
                'serviceBeginDatetime': Date,
                'vacationType': vacation.vacationType[:2],
                'vacationStatus': vacationStatus,
                'sortKey': vacation.empId.empRank,
            })

            if vacation.vacationType != '일차' and vacation.empId.empId not in serviceDept.values_list('empId', flat=True):
                if vacation.empId.dispatchCompany == '내근':
                    flag = ''
                else:
                    flag = '상주'

                if vacation.vacationType == '오전반차':
                    startDateTime = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 14, 0)
                    endDateTime = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 18, 0)
                elif vacation.vacationType == '오후반차':
                    startDateTime = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 9, 0)
                    endDateTime = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 14, 0)

                listService.append({
                    'serviceId': '',
                    'flag': flag,
                    'empName': vacation.empName,
                    'serviceBeginDatetime': startDateTime,
                    'serviceFinishDatetime': endDateTime,
                    'serviceStatus': '',
                    'companyName': vacation.empId.dispatchCompany,
                    'serviceType': '',
                    'serviceTitle': vacation.empId.message,
                    'sortKey': vacation.empId.empRank,
                })

    listService.sort(key=lambda x: x['sortKey'])
    listEducation.sort(key=lambda x: x['sortKey'])
    listVacation.sort(key=lambda x: x['sortKey'])

    queryService = []
    queryEducation = []
    queryVacation = []

    for l in listService:
        temp = QueryDict('', mutable=True)
        temp.update(l)
        queryService.append(temp)
    for l in listEducation:
        temp = QueryDict('', mutable=True)
        temp.update(l)
        queryEducation.append(temp)
    for l in listVacation:
        temp = QueryDict('', mutable=True)
        temp.update(l)
        queryVacation.append(temp)

    return queryService, queryEducation, queryVacation


def link_callback(uri, rel):
    sUrl = settings.STATIC_URL
    sRoot = settings.STATIC_ROOT
    mUrl = settings.MEDIA_URL
    mRoot = settings.MEDIA_ROOT

    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri

    if not os.path.isfile(path):
        raise Exception(
            'media URI must start with %s or %s' % (sUrl, mUrl)
        )
    return path


def num_to_str_position(num):
    if num == 0 or num == '0':
        return '임원'
    elif num == 1 or num == '1':
        return '이사'
    elif num == 2 or num == '2':
        return '부장'
    elif num == 3 or num == '3':
        return '차장'
    elif num == 4 or num == '4':
        return '과장'
    elif num == 5 or num == '5':
        return '대리'
    elif num == 6 or num == '6':
        return '사원'


def latlng_distance(lat1, lng1, lat2, lng2, unit='km'):
    deg2rad = lambda deg: deg * math.pi / 180.0
    rad2deg = lambda rad: rad * 180 / math.pi

    theta = lng1 - lng2
    dist1 = math.sin(deg2rad(lat1)) * math.sin(deg2rad(lat2))
    dist2 = math.cos(deg2rad(lat1)) * math.cos(deg2rad(lat2)) * math.cos(deg2rad(theta))
    dist = math.acos(dist1 + dist2)
    dist = rad2deg(dist) * 60 * 1.1515

    if unit == "km":
        dist *= 1.609344
        dist = round(dist, 1)
    elif unit == 'm':
        dist *= 1609.344
        dist = round(dist)

    return dist


def cal_foodcost(str_start_datetime, str_end_datetime):
    foodcosts=0
    is_holiday_startdate = is_holiday(datetime.datetime.strptime(str_start_datetime[:10], "%Y-%m-%d").date())
    startDate = datetime.datetime(year=int(str_start_datetime[:4]), month=int(str_start_datetime[5:7]), day=int(str_start_datetime[8:10]))
    endDate = datetime.datetime(year=int(str_end_datetime[:4]), month=int(str_end_datetime[5:7]), day=int(str_end_datetime[8:10]))
    dateRange = []
    o_start = pd.Timestamp(str_start_datetime)
    o_finish = pd.Timestamp(str_end_datetime)
    for x in range(0, (o_finish.date() - o_start.date()).days + 1):

        date_dict = {}
        year = int(str((startDate + datetime.timedelta(days=x)).date())[:4])
        month = int(str((startDate + datetime.timedelta(days=x)).date())[5:7])
        day = int(str((startDate + datetime.timedelta(days=x)).date())[8:10])
        next_year = int(str((startDate + datetime.timedelta(days=x+1)).date())[:4])
        next_month = int(str((startDate + datetime.timedelta(days=x+1)).date())[5:7])
        next_day = int(str((startDate + datetime.timedelta(days=x+1)).date())[8:10])

        if (startDate + datetime.timedelta(days=x)).date() == startDate.date():
            date_dict['start'] = o_start
            if (startDate + datetime.timedelta(days=x)).date() == endDate.date():
                date_dict['end'] = o_finish
                dateRange.append(date_dict)
            else:
                date_dict['end'] = datetime.datetime(next_year, next_month, next_day, 0, 0, 0)
                dateRange.append(date_dict)
        else:
            date_dict['start'] = datetime.datetime(year, month, day, 0, 0, 0)
            if (startDate + datetime.timedelta(days=x)).date() == endDate.date():
                date_dict['end'] = o_finish
                dateRange.append(date_dict)
            else:
                date_dict['end'] = datetime.datetime(next_year, next_month, next_day, 0, 0, 0)
                dateRange.append(date_dict)

    for date in dateRange:
        s_week = date['start'].weekday()
        start_date = date['start'].date()
        end_date = date['end'].date()
        start_hour = date['start'].hour
        start_min = date['start'].minute
        end_hour = date['end'].hour
        end_min = date['end'].minute
    
        if start_date != end_date and end_hour == 0:
            end_hour = 24

        # 주말이거나 공휴일일 때
        if s_week in [5, 6] or is_holiday_startdate != 0:
            # 조식대
            # 7:00시 이전 출근
            # 7:00시 이후 퇴근
            if start_hour <= 7 and end_hour >= 7:
                if start_hour == 7 and start_min != 0:
                    foodcosts += 0
                else:
                    foodcosts += 8000

            if start_hour <= 12 and end_hour >= 13:
                foodcosts += 8000

            if start_hour <= 18 and end_hour >= 19:
                foodcosts += 8000
        else:
            # 평일 석식 오후 6시 이후 모두 지급 (단, 8시 이전 근무 종료자 제외)
            # 18:00시 이전 출근시엔 20:00시 초과 퇴근
            # 20:00시 초과 퇴근
            if start_hour >= 18 and end_hour >= 20: #시작시간이 6시를 넘기고 & 종료시간은 8시보다 커야함
                if end_hour == 20 and end_min == 0:
                    foodcosts += 0
                else:
                    foodcosts += 8000
            elif end_hour >= 20:
                if end_hour == 20 and end_min == 0:
                    foodcosts += 0
                else:
                    foodcosts += 8000
    return foodcosts


def naver_distance(latlngs):
    start_lat = str(latlngs[0][0])
    start_lng = str(latlngs[0][1])
    goal_lat = str(latlngs[-1][0])
    goal_lng = str(latlngs[-1][1])
    waypoints = ""
    for i in range(1, len(latlngs)-1):
        waypoints += str(latlngs[i][1]) + ',' + str(latlngs[i][0]) + '|'
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
          "&option=" + option[0] + ":" + option[1] + ":" + option[2]
    header = [
        "X-NCP-APIGW-API-KEY-ID: " + naverMapId,
        "X-NCP-APIGW-API-KEY: " + naverMapKey,
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
    distanceCode = body['code']
    if distanceCode > 0:
        path = ''
        distance = 0
        tollMoney = 0
    else:
        distanceList = [
            body['route'][option[0]][0]['summary']['distance'],
            body['route'][option[1]][0]['summary']['distance'],
            body['route'][option[2]][0]['summary']['distance'],
        ]
        distance = max(distanceList)
        distanceOption = distanceList.index(distance)
        distance = round((distance / 1000), 1)
        path = body['route'][option[distanceOption]][0]['path']
        tollMoney = max([
            body['route'][option[0]][0]['summary']['tollFare'],
            body['route'][option[1]][0]['summary']['tollFare'],
            body['route'][option[2]][0]['summary']['tollFare'],
        ])
    buffer.close()

    return distance, path, distanceCode, tollMoney


def reverse_geo(lat, lng):
    lat = str(lat)
    lng = str(lng)
    url = "https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc?" + \
          "request=coordsToaddr&coords=" + lng + "," + lat + \
          "&output=json" + \
          "&orders=addr"
    header = [
        "X-NCP-APIGW-API-KEY-ID: " + naverMapId,
        "X-NCP-APIGW-API-KEY: " + naverMapKey,
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
    buffer.close()

    alias = body['results'][0]['region']['area1']['alias']
    region = body['results'][0]['region']['area1']['name'] + ' ' \
        + body['results'][0]['region']['area2']['name'] + ' ' \
        + body['results'][0]['region']['area3']['name'] + ' ' \
        + body['results'][0]['region']['area4']['name']
    region = region.strip()

    return alias, region


def weekly_report(startDate, endDate):
    reportForm = '''
    <h4 style="text-align: center;">주 요 내 용</h4>
    <table style="border: #333; width: 100%; border-collapse: collapse; font-size: 14px;">
      <tbody>
      <tr>
        <td colspan="15" style="text-align: center; background: #e6e6e6; padding: 5px 10px; border: 1pt solid; width: 15%;"><b>일 자</b></td>
        <td colspan="85" style="text-align: center; background: #e6e6e6; padding: 5px 10px; border: 1pt solid; width: 85%;"><b>내 용</b></td>
      </tr>
      주요내용 자동작성
      <tr>
        <td colspan="15" style="text-align: center; background: #e6e6e6; padding: 5px 10px; border: 1pt solid; width: 15%;">기타</td>
        <td colspan="85" style="text-align: left; padding: 5px 10px; border: 1pt solid; width: 85%;"></td>
      </tr>
      </tbody>
    </table>
    <br>
    <h4 style="text-align: center">실 천 의 제</h4>
    <table style="border: #333; width: 100%; border-collapse: collapse; font-size: 14px;">
      <tbody>
      <tr>
        <td colspan="45" style="text-align: center; background: #e6e6e6; padding: 5px 10px; border: 1pt solid; width: 45%;"><b>지 시 사 항</b></td>
        <td colspan="20" style="text-align: center; background: #e6e6e6; padding: 5px 10px; border: 1pt solid; width: 20%;"><b>담 당 자</b></td>
        <td colspan="20" style="text-align: center; background: #e6e6e6; padding: 5px 10px; border: 1pt solid; width: 20%;"><b>기 한</b></td>
        <td colspan="15" style="text-align: center; background: #e6e6e6; padding: 5px 10px; border: 1pt solid; width: 15%;"><b>완 료 여 부</b></td>
      </tr>
      <tr>
        <td colspan="45" style="text-align: left; padding: 5px 10px; border: 1pt solid; width: 45%;"></td>
        <td colspan="20" style="text-align: center; padding: 5px 10px; border: 1pt solid; width: 20%;"></td>
        <td colspan="20" style="text-align: center; padding: 5px 10px; border: 1pt solid; width: 20%;"></td>
        <td colspan="15" style="text-align: center; padding: 5px 10px; border: 1pt solid; width: 15%;"></td>
      </tr>
      </tbody>
    </table>
    '''
    tempStr = ''
    days = date_list(startDate, endDate)
    weekday = ['월', '화', '수', '목', '금', '토', '일']
    for day in days:
        tempStr += '''
        <tr>
          <td colspan="15" style="text-align: center; font-size:14px; background: #e6e6e6; padding: 2px 5px; border: 1pt solid; width: 15%;">
        ''' + str(day)[2:] + ' (' + str(weekday[day.weekday()]) + ')' + '''
          </td>
          <td colspan="85" style="text-align: left; font-size:14px; padding: 2px 5px; border: 1pt solid; width: 85%;">
        '''
        # 일정 작성
        service = Servicereport.objects.filter(serviceDate__gte=startDate, serviceDate__lte=endDate)
        tempService = service.filter(serviceDate=day)
        if tempService:
            for s in tempService:
                tempStr += '''
            * ''' + str(s.empName) + ' : ' + '<a href="/service/viewservice/' + str(s.serviceId) + '/">' + s.serviceTitle + '</a>' + '''<br>    
                '''
        # 휴가 작성
        vacation = Vacation.objects.filter(vacationDate__gte=startDate, vacationDate__lte=endDate)
        vacation = vacation.exclude(vacationStatus='R')
        tempVacation = vacation.filter(vacationDate=day)
        if tempVacation:
            tempStr += '<br><span style="color: #e74a3b"><b>휴무자</b></span><br>'
            for v in tempVacation:
                tempStr += '''
                    * ''' + str(v.empName) + ' (' + str(v.vacationCategory.categoryName) + ', ' + v.vacationType + ') : ' + v.comment + '''<br>    
                        '''
        tempStr += '''
          </td>
        </tr>
        '''
    reportForm = reportForm.replace('주요내용 자동작성', tempStr)
    reportForm = reportForm.replace('\'', '"')
    reportForm = reportForm.replace('\r', '')
    reportForm = reportForm.replace('\n', '')
    return reportForm
