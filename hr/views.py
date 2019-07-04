# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse
from sales.models import Contract, Category, Revenue, Contractitem, Goal, Purchase
from service.models import Company, Customer, Servicereport, Vacation
import pandas as pd
from .models import Attendance, Employee, Punctuality
from django.db.models import Q
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
import datetime
from .functions import employee_empPosition, save_punctuality, check_absence, year_absence
import json
from django.core.serializers.json import DjangoJSONEncoder


@login_required
@csrf_exempt
def profile(request):
    template = loader.get_template('hr/profile.html')
    userId = request.user.id
    user = User.objects.get(id=userId)
    if request.method == "POST":
        postMessage = request.POST['message']
        user.employee.message = postMessage
        user.employee.save()
        context = {
            'user': user,
        }
        return HttpResponse(template.render(context, request))
    else:
        context = {
            'user': user,
        }
        return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def show_punctuality(request, day=None):
    template = loader.get_template('hr/showpunctuality.html')
    if day is None:
        day = str(datetime.datetime.today())[:10]
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    beforeDate = Date - datetime.timedelta(days=1)
    afterDate = Date + datetime.timedelta(days=1)
    year = day[:4]
    month = day[5:7]

    # 분기
    if month in ['01', '02', '03']:
        startdate = '{}-01-01'.format(year)
    elif month in ['04', '05', '06']:
        startdate = '{}-04-01'.format(year)
    elif month in ['07', '08', '09']:
        startdate = '{}-07-01'.format(year)
    else:
        startdate = '{}-10-01'.format(year)

    punctuality = Punctuality.objects.filter(punctualityDate=day).order_by('empId__empPosition')
    punctualityList = []
    punctualityList.append(punctuality.filter(empId__empDeptName='경영지원본부').values('empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment'))
    punctualityList.append(punctuality.filter(empId__empDeptName='영업1팀').values('empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment'))
    punctualityList.append(punctuality.filter(empId__empDeptName='영업2팀').values('empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment'))
    punctualityList.append(punctuality.filter(empId__empDeptName='인프라서비스사업팀').values('empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment'))
    punctualityList.append(punctuality.filter(empId__empDeptName='솔루션지원팀').values('empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment'))
    punctualityList.append(punctuality.filter(empId__empDeptName='DB지원팀').values('empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment'))

    for pun in punctualityList:
        for user in pun:
            absence = check_absence(user['empId_id'], startdate, day, False)
            if absence:
                user['absenceDate'] = []
                for a in absence:
                    user['absenceDate'].append(a.punctualityDate)
                user['absenceCount'] = len(absence)

    print(punctualityList)
    context = {
        'day': day,
        'Date': Date,
        'beforeDate': beforeDate,
        'afterDate': afterDate,
        'punctualityList': punctualityList,
        'sumpunctuality': len(punctuality)
    }
    return HttpResponse(template.render(context, request))


@login_required
def upload_caps(request):
    template = loader.get_template('hr/uploadcaps.html')
    userId = request.user.id
    user = User.objects.get(id=userId)
    context = {
        'user': user,
    }
    return HttpResponse(template.render(context, request))


@login_required
def save_caps(request):
    csv_file = request.FILES["csv_file"]
    xl_file = pd.ExcelFile(csv_file)
    data = pd.read_excel(xl_file)
    data = data[['발생일자', '발생시각', '사용자ID', '이름', '모드']]
    data = data.dropna()
    datalen = len(data)
    errorList = []
    successCount = 0

    for index, rows in data.iterrows():
        # print('발생일자:', rows[0], '발생시각:', rows[1], '사용자ID:', rows[2], '이름:', rows[3], '모드:', rows[4])
        try:
            empId = Employee.objects.get(empCode=rows[2])
        except:
            errorList.append({rows[2]: '미등록된 사원 번호'})
            empId = ''

        if empId:
            if Attendance.objects.filter(Q(empId=empId) & Q(attendanceDate=rows[0]) & Q(attendanceTime=rows[1])).first() == None:
                Attendance.objects.create(empId=empId, attendanceDate=rows[0], attendanceTime=rows[1], attendanceType=rows[4])
                successCount += 1

    # 근태 정보 저장
    save_punctuality(list(data['발생일자'].unique()))

    context = {
        "datalen": datalen - 1,
        "errorList": errorList,
        "successCount": successCount,
    }

    return render(request, 'hr/uploadcaps.html', context)


@login_required
@csrf_exempt
def show_yearpunctuality(request, year=None):
    if request.method == "POST":
        year = request.POST['year']
        userList = year_absence(str(year))
    else:
        if year is None:
            year = datetime.datetime.today().year

        userList = year_absence(str(year))
    context = {
        'year': year,
        'userList': userList
    }

    return render(request, 'hr/showyearpunctuality.html', context)


@login_required
@csrf_exempt
def show_absence(request):
    if request.method == "POST":
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        empName = request.POST['empName']
        empDeptName = request.POST['empDeptName']

    else:
        startdate = ''
        enddate = ''
        empName = ''
        empDeptName = ''

    context = {
        'startdate': startdate,
        'enddate': enddate,
        'empName': empName,
        'empDeptName': empDeptName
    }
    return render(request, 'hr/showabsence.html', context)


@login_required
@csrf_exempt
def absences_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    empName = request.POST['empName']
    empDeptName = request.POST['empDeptName']

    punctualitys = Punctuality.objects.filter(Q(punctualityType='지각'))

    if startdate:
        punctualitys = punctualitys.filter(punctualityDate__gte=startdate)
    if enddate:
        punctualitys = punctualitys.filter(punctualityDate__lte=enddate)
    if empName:
        punctualitys = punctualitys.filter(empId__empName__icontains=empName)
    if empDeptName:
        punctualitys = punctualitys.filter(empId__empDeptName__icontains=empDeptName)

    punctualitys = punctualitys.values('punctualityDate', 'empId__empDeptName', 'empId__empName', 'punctualityType', 'comment', 'punctualityId')
    structure = json.dumps(list(punctualitys), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')

@login_required
@csrf_exempt
def view_absence(request, punctualityId):
    punctuality = Punctuality.objects.filter(Q(punctualityId=punctualityId))
    punctuality = punctuality.values('punctualityDate', 'empId__empDeptName', 'empId__empName', 'punctualityType', 'comment', 'punctualityId').first()
    context = {
        'punctuality':punctuality
    }
    return render(request, 'hr/viewabsence.html', context)

@login_required
@csrf_exempt
def modify_absence(request, punctualityId):

    if request.method == "POST":
        punctuality = Punctuality.objects.get(Q(punctualityId=punctualityId))
        punctualityType = request.POST["punctualityType"]
        comment = request.POST['comment']
        punctuality.punctualityType = punctualityType
        punctuality.comment = comment
        punctuality.save()
        print(punctuality)
        return redirect('hr:viewabsence',punctualityId)

    else:
        punctuality = Punctuality.objects.filter(Q(punctualityId=punctualityId))
        punctuality = punctuality.values('punctualityDate', 'empId__empDeptName', 'empId__empName', 'punctualityType', 'comment', 'punctualityId').first()

        context = {
            'punctuality':punctuality
        }
        return render(request, 'hr/modifyabsence.html', context)
