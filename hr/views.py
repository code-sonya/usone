# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse
from sales.models import Contract, Category, Revenue, Contractitem, Goal, Purchase
from service.models import Company, Customer, Servicereport, Vacation
import pandas as pd
from .models import Attendance, Employee
from django.db.models import Q
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
import datetime
from .functions import employee_empPosition

@login_required
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
def show_punctuality(request, day=None):
    template = loader.get_template('hr/showpunctuality.html')
    if day is None:
        day = str(datetime.datetime.today())[:10]
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    beforeDate = Date - datetime.timedelta(days=1)
    afterDate = Date + datetime.timedelta(days=1)
    users = User.objects.filter(Q(employee__empStatus='Y')).exclude(Q(employee__empDeptName='임원')|Q(employee__empDeptName='미정'))\
                        .values('employee__empId','employee__empName','employee__empDeptName','employee__empPosition','employee__empRank','employee__dispatchCompany')
    attendances = Attendance.objects.filter(attendanceDate=day).order_by('attendanceTime')


    for user in users:
        # 기본
        user['status'] = '지각'

        # 직급
        positionName = employee_empPosition(user['employee__empPosition'])
        user['positionName'] = positionName

        # 상주
        if user['employee__dispatchCompany'] != '내근':
            user['status'] = '상주'

        # 휴가
        elif Vacation.objects.filter(Q(vacationDate=day)&Q(empId_id=user['employee__empId'])):
            user['status'] = '휴가'

        else:
            service = Servicereport.objects.filter(Q(serviceDate=day) & Q(empId=user['employee__empId'])).order_by('serviceStartDatetime').first()
            if service:
                if service.directgo == 'Y':
                    user['status'] = '직출'
                else:
                    for attendance in attendances:
                        if user['employee__empId'] == attendance.empId_id:
                            if attendance.attendanceTime >= datetime.time(9,1,0):
                                user['status'] = '지각'
                                break
                            else:
                                user['status'] = '출근'
                                break
            else:
                for attendance in attendances:
                    if user['employee__empId'] == attendance.empId_id:
                        if attendance.attendanceTime >= datetime.time(9, 1, 0):
                            user['status'] = '지각'
                            break
                        else:
                            user['status'] = '출근'
                            break

    print(users)

    context = {
        'day': day,
        'Date': Date,
        'beforeDate': beforeDate,
        'afterDate': afterDate,
        'users':users,
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
            if Attendance.objects.filter(Q(empId=empId) & Q(attendanceDate=rows[0]) & Q(attendanceTime=rows[1])).first() == None :
                Attendance.objects.create(empId=empId, attendanceDate=rows[0], attendanceTime=rows[1], attendanceType=rows[4])
                successCount += 1

    print('successCount:',successCount)
    print(errorList)

    context = {
        "datalen": datalen - 1,
        "errorList":errorList,
        "successCount":successCount,
    }

    return render(request, 'hr/uploadcaps.html', context)