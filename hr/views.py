# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse
from sales.models import Contract, Category, Revenue, Contractitem, Goal, Purchase
from service.models import Company, Customer
import pandas as pd
from .models import Attendance, Employee
from django.db.models import Q
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

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
def show_punctuality(request):
    template = loader.get_template('hr/showpunctuality.html')
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
def upload_caps(request):
    template = loader.get_template('hr/uploadcaps.html')
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
def save_caps(request):

    if "GET" == request.method:
        pass

    csv_file = request.FILES["csv_file"]
    xl_file = pd.ExcelFile(csv_file)
    data = pd.read_excel(xl_file)
    data = data[['발생일자', '발생시각', '사용자ID', '이름', '모드']]
    data = data.dropna()
    datalen = len(data)
    errorList = []
    successCount = 0

    for index, rows in data.iterrows():
        print('발생일자:', rows[0], '발생시각:', rows[1], '사용자ID:', rows[2], '이름:', rows[3], '모드:', rows[4])
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