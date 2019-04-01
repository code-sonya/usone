import pandas as pd
from datetime import datetime, timedelta
import requests
from django.db.models import Q
from dateutil.relativedelta import relativedelta
from scheduler.models import Eventday


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
