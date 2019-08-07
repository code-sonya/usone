# -*- coding: utf-8 -*-
import datetime
import json

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from service.models import Servicereport, Vacation
from .models import Eventday


@login_required
@csrf_exempt
def scheduler(request, day=None):
    #
    if day is None:
        day = str(datetime.datetime.today())[:10]
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), 1)
    beforeMonth = Date - relativedelta(months=1)
    afterMonth = Date + relativedelta(months=1)
    print(Date, beforeMonth, afterMonth)
    #

    template = loader.get_template('scheduler/scheduler.html')
    empId = request.user.employee.empId
    empName = request.user.employee.empName
    empDeptName = request.user.employee.empDeptName
    DeptList = ['경영지원본부', '영업1팀', '영업2팀', '인프라서비스사업팀', '솔루션지원팀', 'DB지원팀']

    # event
    holiday = Eventday.objects.filter(eventType="휴일")
    event = Eventday.objects.filter(eventType="사내일정")

    services = Servicereport.objects.filter(Q(serviceDate__gte=Date - datetime.timedelta(days=7)) & Q(serviceDate__lt=afterMonth + datetime.timedelta(days=7)))
    vacations = Vacation.objects.filter(Q(vacationDate__gte=Date - datetime.timedelta(days=7)) & Q(vacationDate__lt=afterMonth + datetime.timedelta(days=7)))

    # 1.선택한 부서만
    if request.method == "POST":
        print('post')
        postDeptList = request.POST.getlist('ckdept')
        print(postDeptList)

        # 일정(한달치)
        teamCalendar = services.filter(Q(empDeptName__in=postDeptList)).exclude(empId=empId)
        myCalendar = services.filter(Q(empDeptName__in=postDeptList) & Q(empId=empId))

        # 휴가(전체)
        teamVacation = vacations.filter(Q(empDeptName__in=postDeptList)).exclude(empId=empId)
        myVacation = vacations.filter(Q(empDeptName__in=postDeptList) & Q(empId=empId))

        context = {
            'today': str(datetime.date.today()),
            'empName': empName,
            'empDeptName': empDeptName,
            'teamCalendar': teamCalendar,
            'myCalendar': myCalendar,
            'teamVacation': teamVacation,
            'myVacation': myVacation,
            'DeptList': DeptList,
            'holiday': holiday,
            'event': event,
            'beforeMonth': beforeMonth,
            'afterMonth': afterMonth,
            'Date': Date,
            'postDeptList': postDeptList,
        }
        return HttpResponse(template.render(context, request))

    # 2.소속된 부서만
    else:

        # 일정
        teamCalendar = services.filter(Q(empDeptName=empDeptName)).exclude(empId=empId)
        myCalendar = services.filter(Q(empId=empId))

        # 휴가(전체)
        teamVacation = vacations.filter(Q(empDeptName=empDeptName)).exclude(empId=empId)
        myVacation = vacations.filter(Q(empId=empId))

        context = {
            'today': str(datetime.date.today()),
            'empName': empName,
            'empDeptName': empDeptName,
            'teamCalendar': teamCalendar,
            'myCalendar': myCalendar,
            'teamVacation': teamVacation,
            'myVacation': myVacation,
            'DeptList': DeptList,
            'holiday': holiday,
            'event': event,
            'beforeMonth': beforeMonth,
            'afterMonth': afterMonth,
            'Date': Date,
        }
        return HttpResponse(template.render(context, request))


@login_required
@require_POST
@csrf_exempt
def changeDate(request):
    # POST : service id, type, start/enddate
    serviceId = request.POST.get('serviceId', None)
    serviceType = request.POST.get('serviceType', None)
    startDate = request.POST.get('start', None)
    endDate = request.POST.get('end', None)

    # 일정인 경우
    if serviceType == "N":
        post = get_object_or_404(Servicereport, serviceId=serviceId)
        post.serviceDate = str(startDate)[:10]
        post.serviceStartDatetime = str(startDate)[:10] + ' ' + str(post.serviceStartDatetime)[11:]
        post.serviceEndDatetime = str(endDate)[:10] + ' ' + str(post.serviceEndDatetime)[11:]
        post.save()

    # 휴가인 경우
    else:
        vacation = get_object_or_404(Vacation, vacationId=serviceId)
        vacation.vacationDate = str(startDate)[:10]
        vacation.save()

    context = {'service_id': serviceId}
    return HttpResponse(json.dumps(context), content_type="application/json")
