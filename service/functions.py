import datetime
import os
import math

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import QueryDict

from scheduler.models import Eventday
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


def overtime_extrapay(str_start_datetime, str_end_datetime):
    is_holiday_startdate = is_holiday(datetime.datetime.strptime(str_start_datetime[:10], "%Y-%m-%d").date())
    is_holiday_enddate = is_holiday(datetime.datetime.strptime(str_end_datetime[:10], "%Y-%m-%d").date())

    o_start = pd.Timestamp(str_start_datetime)
    o_finish = pd.Timestamp(str_end_datetime)
    d_start = pd.Timestamp(str_start_datetime)
    d_finish = pd.Timestamp(str_end_datetime)


    minute_sum = 0

    s_week = d_start.weekday()
    f_week = d_finish.weekday()

    if s_week in [5, 6] or is_holiday_startdate != 0:  # 주말이거나 공휴일 일때
        if d_start.minute != 0:
            print('1')
            minute_sum += (60 - d_start.minute)
            print(minute_sum)
            d_start = d_start + datetime.timedelta(minutes=(60 - d_start.minute))
            print(d_start)

    else:  # 평일 일때
        if d_start.minute != 0:  # 정각 시작하지 않은 경우
            if d_start.hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # 시작 시각이 초과 근무에 해당 할 경우
                print('2')
                minute_sum += (60 - d_start.minute)
                print(minute_sum)
                d_start = d_start + datetime.timedelta(minutes=(60 - d_start.minute))
                print(d_start)
            else:  # 초과 근무에 해당 하지 않는 경우
                print('3')
                d_start = d_start + datetime.timedelta(minutes=(60 - d_start.minute))
                print(d_start)

    if f_week in [5, 6] or is_holiday_enddate != 0:  # 주말이거나 공휴일 일때
        if d_finish.minute != 0:
            print('4')
            minute_sum += d_finish.minute
            print('minute_sum:', minute_sum)
            d_finish = d_finish - datetime.timedelta(minutes=d_finish.minute)
            print(d_finish)

    else:  # 평일 일때
        if d_finish.minute != 0:  # 정각에 끝나지 않은 경우
            if d_finish.hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # 종료 시각이 초과 근무에 해당 할 경우
                print('5')
                minute_sum += d_finish.minute
                print(minute_sum)
                d_finish = d_finish - datetime.timedelta(minutes=d_finish.minute)
                print(d_finish)
            else:
                print('6')
                d_finish = d_finish - datetime.timedelta(minutes=d_finish.minute)
                print(d_finish)

    min_date = datetime.datetime(3000, 1, 31, 1, 0, 0)
    max_date = datetime.datetime(1999, 1, 31, 1, 0, 0)
    for i in range(0, work_hours(d_start, d_finish), 1):
        a = (d_start + datetime.timedelta(hours=i))
        event_a = is_holiday(a.date())
        a_week = a.weekday()

        if d_start <= a <= d_finish:
            if a_week in [5, 6] or event_a != 0:  # 주말이나 공휴일
                if d_start.date() == d_finish.date():
                    minute_sum += int((d_finish - d_start).seconds / 60)
                    min_date = d_start
                    max_date = d_finish
                    break
                elif d_finish == a:
                    pass
                else:
                    minute_sum += 60
                    if a < min_date:
                        min_date = a

                    if a > max_date:
                        max_date = a

            else:  # 평일
                if int(a.hour) in [0, 1, 2, 3, 4, 5, 22, 23]:
                    if d_finish == a:
                        pass
                    else:
                        minute_sum += 60
                        if a < min_date:
                            min_date = a

                        if a > max_date:
                            max_date = a

    if max_date != datetime.datetime(1999, 1, 31, 1, 0, 0):
        max_date = max_date + datetime.timedelta(minutes=60)
    else:
        max_date = None
    if min_date == datetime.datetime(3000, 1, 31, 1, 0, 0):
        min_date = None
    if max_date.hour == 5 and o_finish.hour == 5 and o_finish.minute != 0:
        max_date = o_finish
    if min_date.hour == 23:
        if o_start.hour == 22 and o_start.minute != 0:
            min_date = o_start

    return round((math.trunc(minute_sum * 0.1)*10)/60, 2), round((math.trunc(minute_sum * 0.1)*10)/60, 2), min_date, max_date


def dayreport_query2(empDeptName, day):
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    Date_min = datetime.datetime.combine(Date, datetime.datetime.min.time())
    Date_max = datetime.datetime.combine(Date, datetime.datetime.max.time())
    if datetime.datetime.weekday(Date) >= 5 or Eventday.objects.filter(Q(eventDate=Date) & Q(eventType='휴일')):
        holiday = True
    else:
        holiday = False

    serviceDept = Servicereport.objects.filter(
        Q(empDeptName=empDeptName) & (Q(serviceBeginDatetime__lte=Date_max) & Q(serviceFinishDatetime__gte=Date_min))
    ).order_by('serviceBeginDatetime')

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
        if service.serviceType == '상주':
            flag = '상주'
        elif service.directgo == 'Y':
            flag = '직출'
        else:
            flag = ''

        if service.serviceType == '교육':
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
                'serviceType': service.serviceType,
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
            listVacation.append({
                'empName': vacation.empName,
                'serviceBeginDatetime': Date,
                'vacationType': vacation.vacationType[:2],
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
        start_hour = date['start'].hour
        end_hour = date['end'].hour
        if end_hour == 0:
            end_hour = 24

        # 주말이거나 공휴일일 때
        if s_week in [5, 6] or is_holiday_startdate != 0:
            if start_hour <= 7 and 7 <= end_hour:
                foodcosts += 8000

            if start_hour <= 12 and end_hour >= 13:
                foodcosts += 8000

            if start_hour <= 18 and end_hour >= 19:
                foodcosts += 8000
        else:
            # 평일 석식 오후 6시 이후 모두 지급 (단, 오후6~8시 근무자 제외)
            if end_hour <=18:
                if start_hour >= 18 and end_hour < 21:
                    pass
                else:
                    foodcosts += 8000

    return foodcosts









