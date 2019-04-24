import os
from django.conf import settings
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Q
from dateutil.relativedelta import relativedelta

from scheduler.models import Eventday
from .models import Servicereport, Vacation
from django.contrib.auth.models import User
from django.http import QueryDict


def date_list(startDatetime, endDatetime):
    startDate = datetime(year=int(startDatetime[:4]), month=int(startDatetime[5:7]), day=int(startDatetime[8:10]))
    endDate = datetime(year=int(endDatetime[:4]), month=int(endDatetime[5:7]), day=int(endDatetime[8:10]))
    dateRange = [(startDate + timedelta(days=x)).date() for x in range(0, (endDate - startDate).days + 1)]
    return dateRange


def month_list(startDatetime, endDatetime):
    startDatetime = datetime(year=int(startDatetime[:4]), month=int(startDatetime[5:7]), day=int(startDatetime[8:10]))
    endDatetime = datetime(year=int(endDatetime[:4]), month=int(endDatetime[5:7]), day=int(endDatetime[8:10]))

    monthRange = []
    insertDate = startDatetime
    while insertDate <= endDatetime:
        monthRange.append(insertDate.date())
        insertDate = insertDate + relativedelta(months=1)
    return monthRange


def str_to_timedelta_hour(str_endDatetime, str_startDatetime):
    e = datetime(year=int(str(str_endDatetime)[:4]), month=int(str(str_endDatetime)[5:7]), day=int(str(str_endDatetime)[8:10]),
                 hour=int(str(str_endDatetime)[11:13]), minute=int(str(str_endDatetime)[14:16]), second=0)
    s = datetime(year=int(str(str_startDatetime)[:4]), month=int(str(str_startDatetime)[5:7]), day=int(str(str_startDatetime)[8:10]),
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
    is_holiday_startdate = is_holiday(datetime.strptime(str_start_datetime[:10], "%Y-%m-%d").date())
    is_holiday_enddate = is_holiday(datetime.strptime(str_end_datetime[:10], "%Y-%m-%d").date())
    d_start = pd.Timestamp(str_start_datetime)
    d_finish = pd.Timestamp(str_end_datetime)

    minute_sum = 0

    s_week = d_start.weekday()
    f_week = d_finish.weekday()

    if s_week in [5, 6] or is_holiday_startdate != 0:  # 주말이거나 공휴일 일때
        if d_start.minute != 0:
            minute_sum += (60 - d_start.minute)
            d_start = d_start + timedelta(minutes=(60 - d_start.minute))

    else:  # 평일 일때
        if d_start.minute != 0:  # 정각 시작하지 않은 경우
            if d_start.hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # 시작 시각이 초과 근무에 해당 할 경우
                minute_sum += (60 - d_start.minute)
                d_start = d_start + timedelta(minutes=(60 - d_start.minute))
            else:  # 초과 근무에 해당 하지 않는 경우
                d_start = d_start + timedelta(minutes=(60 - d_start.minute))

    if f_week in [5, 6] or is_holiday_enddate != 0:  # 주말이거나 공휴일 일때
        if d_finish.minute != 0:
            minute_sum += d_finish.minute
            d_finish = d_finish - timedelta(minutes=d_finish.minute)

    else:  # 평일 일때
        if d_finish.minute != 0:  # 정각에 끝나지 않은 경우
            if d_finish.hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # 종료 시각이 초과 근무에 해당 할 경우
                minute_sum += d_finish.minute
                d_finish = d_finish - timedelta(minutes=d_finish.minute)
            else:
                d_finish = d_finish - timedelta(minutes=d_finish.minute)

    for i in range(0, work_hours(d_start, d_finish), 1):
        a = (d_start + timedelta(hours=i))
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


def dayreport_sort(x):
    if x['empName'] == '최영준' or x['empName'] == '박정일':
        return 1, x['serviceStartDatetime']
    if x['empName'] == '최순석' or x['empName'] == '임성민':
        return 2, x['serviceStartDatetime']
    if x['empName'] == '박경진' or x['empName'] == '유병길':
        return 3, x['serviceStartDatetime']
    if x['empName'] == '유명수' or x['empName'] == '임중정':
        return 4, x['serviceStartDatetime']
    if x['empName'] == '권성진' or x['empName'] == '구본석':
        return 5, x['serviceStartDatetime']
    if x['empName'] == '김동혁' or x['empName'] == '정남구':
        return 6, x['serviceStartDatetime']
    if x['empName'] == '박준형' or x['empName'] == '이현수':
        return 7, x['serviceStartDatetime']
    if x['empName'] == '김소령' or x['empName'] == '어경진':
        return 8, x['serviceStartDatetime']
    if x['empName'] == '임형균' or x['empName'] == '':
        return 9, x['serviceStartDatetime']
    if x['empName'] == '' or x['empName'] == '':
        return 10, x['serviceStartDatetime']


def dayreport_query(empDeptName, day):
    Date = datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    Date_min = datetime.combine(Date, datetime.min.time())
    Date_max = datetime.combine(Date, datetime.max.time())

    serviceDept = Servicereport.objects.filter(
        Q(empDeptName=empDeptName) & (Q(serviceStartDatetime__lte=Date_max) & Q(serviceEndDatetime__gte=Date_min))
    )

    vacationDept = Vacation.objects.filter(
        Q(empDeptName=empDeptName) & Q(vacationDate=Date)
    )

    inDept = User.objects.filter(
        Q(employee__empDeptName=empDeptName) & Q(employee__empStatus='Y')
    ).exclude(
        Q(employee__empId__in=serviceDept.values('empId')) | Q(employee__empId__in=vacationDept.values('empId'))
    )

    listDept = []

    for service in serviceDept:
        if service.serviceType == '교육' and service.directgo == 'Y':
            flag = '직출'
            companyName = '교육'
            serviceType = ''
        elif service.serviceType == '교육' and service.directgo == 'N':
            flag = ''
            companyName = '교육'
            serviceType = ''
        elif service.directgo == 'Y':
            flag = '직출'
            companyName = service.companyName
            serviceType = service.serviceType
        else:
            flag = ''
            companyName = service.companyName
            serviceType = service.serviceType
        listDept.append({
            'serviceId': service.serviceId,
            'flag': flag,
            'empName': service.empName,
            'serviceStartDatetime': service.serviceStartDatetime,
            'serviceEndDatetime': service.serviceEndDatetime,
            'serviceStatus': service.serviceStatus,
            'companyName': companyName,
            'serviceType': serviceType,
            'serviceTitle': service.serviceTitle,
        })

    for vacation in vacationDept:
        listDept.append({
            'serviceId': '',
            'flag': '휴가',
            'empName': vacation.empName,
            'serviceStartDatetime': datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 9, 0),
            'serviceEndDatetime': '',
            'serviceStatus': '',
            'companyName': '',
            'serviceType': '',
            'serviceTitle': vacation.vacationType,
        })

    for emp in inDept:
        if emp.employee.dispatchCompany == '내근':
            flag = ''
            serviceType = ''
        else:
            flag = '상주'
            serviceType = ''
        listDept.append({
            'serviceId': '',
            'flag': flag,
            'empName': emp.employee.empName,
            'serviceStartDatetime': datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 9, 0),
            'serviceEndDatetime': datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 18, 0),
            'serviceStatus': '',
            'companyName': emp.employee.dispatchCompany,
            'serviceType': serviceType,
            'serviceTitle': emp.employee.message,
        })

    listDept.sort(key=dayreport_sort)

    query = []
    for l in listDept:
        temp = QueryDict('', mutable=True)
        temp.update(l)
        query.append(temp)

    return query


def dayreport_query2(empDeptName, day):
    Date = datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    Date_min = datetime.combine(Date, datetime.min.time())
    Date_max = datetime.combine(Date, datetime.max.time())

    serviceDept = Servicereport.objects.filter(
        Q(empDeptName=empDeptName) & (Q(serviceStartDatetime__lte=Date_max) & Q(serviceEndDatetime__gte=Date_min))
    )

    vacationDept = Vacation.objects.filter(
        Q(empDeptName=empDeptName) & Q(vacationDate=Date)
    )

    inDept = User.objects.filter(
        Q(employee__empDeptName=empDeptName) & Q(employee__empStatus='Y')
    ).exclude(
        Q(employee__empId__in=serviceDept.values('empId')) | Q(employee__empId__in=vacationDept.values('empId'))
    )

    listService = []
    listEducation = []
    listVacation = []

    for service in serviceDept:
        if service.directgo == 'Y':
            flag = '직출'
        else:
            flag = ''

        if service.serviceType == '교육':
            listEducation.append({
                'serviceId': service.serviceId,
                'flag': flag,
                'empName': service.empName,
                'serviceStartDatetime': service.serviceStartDatetime,
                'serviceEndDatetime': service.serviceEndDatetime,
                'serviceStatus': service.serviceStatus,
                'serviceTitle': service.serviceTitle,
            })
        else:
            listService.append({
                'serviceId': service.serviceId,
                'flag': flag,
                'empName': service.empName,
                'serviceStartDatetime': service.serviceStartDatetime,
                'serviceEndDatetime': service.serviceEndDatetime,
                'serviceStatus': service.serviceStatus,
                'companyName': service.companyName,
                'serviceType': service.serviceType,
                'serviceTitle': service.serviceTitle,
            })

    for emp in inDept:
        if emp.employee.dispatchCompany == '내근':
            flag = ''
        else:
            flag = '상주'
        listService.append({
            'serviceId': '',
            'flag': flag,
            'empName': emp.employee.empName,
            'serviceStartDatetime': datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 9, 0),
            'serviceEndDatetime': datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), 18, 0),
            'serviceStatus': '',
            'companyName': emp.employee.dispatchCompany,
            'serviceType': '',
            'serviceTitle': emp.employee.message,
        })

    for vacation in vacationDept:
        listVacation.append({
            'empName': vacation.empName,
            'serviceStartDatetime': Date,
            'vacationType': vacation.vacationType[:2],
        })

    listService.sort(key=dayreport_sort)
    listEducation.sort(key=dayreport_sort)
    listVacation.sort(key=dayreport_sort)

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