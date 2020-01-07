# -*- coding: utf-8 -*-
import datetime
import json

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Max
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from hr.models import Employee, Department
from service.models import Servicereport, Vacation
from .forms import EventdayForm
from .models import Eventday


@login_required
@csrf_exempt
def scheduler(request, day=None):
    if day is None:
        day = str(datetime.datetime.today())[:10]

    # 날짜
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), 1)
    beforeMonth = Date - relativedelta(months=1)
    afterMonth = Date + relativedelta(months=1)
    startDate = Date - datetime.timedelta(days=7)
    endDate = afterMonth + datetime.timedelta(days=7)

    # 로그인 유저, 부서 정보
    empId = request.user.employee.empId
    empName = request.user.employee.empName
    empDeptName = request.user.employee.empDeptName
    DeptList = Department.objects.filter(
        deptName__in=Employee.objects.filter(empStatus='Y').values_list('departmentName__deptName', flat=True).distinct(),
        deptLevel=Department.objects.all().aggregate(maxLevel=Max('deptLevel'))['maxLevel'],
    ).values_list('deptName', flat=True)

    # 선택한 부서의 일정, 휴가 (기본값은 로그인 사용자의 부서)
    if request.method == "POST":
        postDeptList = request.POST.getlist('ckdept')
    else:
        postDeptList = [empDeptName]

    # 일정, 휴가, 휴일, 사내일정 (한달)
    services = Servicereport.objects.filter(
        Q(serviceDate__gte=startDate) &
        Q(serviceDate__lte=endDate) &
        Q(empDeptName__in=postDeptList)
    )
    vacations = Vacation.objects.filter(
        Q(vacationDate__gte=startDate) &
        Q(vacationDate__lte=endDate) &
        Q(empDeptName__in=postDeptList) &
        (Q(vacationStatus='Y') | Q(vacationStatus='N'))
    )
    holiday = Eventday.objects.filter(
        Q(eventType="휴일") &
        Q(eventDate__gte=startDate) &
        Q(eventDate__lte=endDate)
    )
    event = Eventday.objects.filter(
        Q(eventType="사내일정") &
        Q(eventDate__gte=startDate) &
        Q(eventDate__lte=endDate)
    )

    # 내 일정, 팀 일정
    myServices = services.filter(empId=empId)
    teamServices = services.exclude(empId=empId)

    # 내 휴가, 팀 휴가
    myVacations = vacations.filter(empId=empId)
    teamVacations = vacations.exclude(empId=empId)

    context = {
        'today': str(datetime.date.today()),
        'empName': empName,
        'empDeptName': empDeptName,
        'myServices': myServices,
        'teamServices': teamServices,
        'myVacations': myVacations,
        'teamVacations': teamVacations,
        'DeptList': DeptList,
        'holiday': holiday,
        'event': event,
        'beforeMonth': beforeMonth,
        'afterMonth': afterMonth,
        'Date': Date,
        'postDeptList': postDeptList,
    }
    template = loader.get_template('scheduler/scheduler.html')
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
        post.serviceBeginDatetime = str(startDate)[:10] + ' ' + str(post.serviceBeginDatetime)[11:]
        post.serviceStartDatetime = str(startDate)[:10] + ' ' + str(post.serviceStartDatetime)[11:]
        post.serviceEndDatetime = str(endDate)[:10] + ' ' + str(post.serviceEndDatetime)[11:]
        post.serviceFinishDatetime = str(endDate)[:10] + ' ' + str(post.serviceFinishDatetime)[11:]
        post.save()

    # 휴가인 경우
    else:
        vacation = get_object_or_404(Vacation, vacationId=serviceId)
        vacation.vacationDate = str(startDate)[:10]
        vacation.save()

    context = {'service_id': serviceId}
    return HttpResponse(json.dumps(context), content_type="application/json")


@login_required
def show_eventday(request):
    today = str(datetime.datetime.today())[:10]
    startdate = today[:4] + '-01-01'
    enddate = ''

    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']

    context = {
        'startdate': startdate,
        'enddate': enddate,
    }
    return render(request, 'scheduler/showeventday.html', context)


@login_required
def showeventday_asjson(request):
    startdate = request.GET['startdate']
    enddate = request.GET['enddate']

    eventDay = Eventday.objects.all()
    if startdate:
        eventDay = eventDay.filter(eventDate__gte=startdate)
    if enddate:
        eventDay = eventDay.filter(eventDate__lte=enddate)
    eventDay = eventDay.values('eventDate', 'eventName', 'eventType')

    structure = json.dumps(list(eventDay), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def view_eventday(request, eventDate):
    eventDay = Eventday.objects.get(eventDate=eventDate)

    if request.method == 'POST':
        form = EventdayForm(request.POST, instance=eventDay)
        form.save()
        return redirect('scheduler:showeventday')

    else:
        form = EventdayForm(instance=eventDay)

        context = {
            'eventDay': eventDay,
            'form': form,
        }

        return render(request, 'scheduler/vieweventday.html', context)


@login_required
def post_eventday(request):
    if request.method == 'POST':
        form = EventdayForm(request.POST)
        form.save()

        return redirect('scheduler:showeventday')

    else:
        form = EventdayForm()

        context = {
            'form': form,
        }

        return render(request, 'scheduler/posteventday.html', context)


@login_required
def delete_eventday(request, eventDate):
    Eventday.objects.get(eventDate=eventDate).delete()
    return redirect('scheduler:showeventday')


@login_required
def check_eventday(request):
    result = 'Y'
    if Eventday.objects.filter(eventDate=request.GET['eventDate']):
        result = 'N'

    print(result)

    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')