# -*- coding: utf-8 -*-

import datetime
import json

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F
from django.db.models import Max
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from extrapay.models import Car
from .forms import EmployeeForm, DepartmentForm, UserForm
from .functions import save_punctuality, check_absence, year_absence, adminemail_test, siteMap
from .models import AdminEmail, AdminVacation
from .models import Attendance, Employee, Punctuality, Department


@login_required
@csrf_exempt
def profile(request):
    template = loader.get_template('hr/profile.html')
    userId = request.user.id
    user = User.objects.get(id=userId)
    if request.method == "POST":
        empPhone = request.POST['empPhone'] or user.employee.empPhone
        empEmail = request.POST['empEmail'] or user.employee.empEmail
        # carId = request.POST['carId'] or None
        # if carId:
        #     carId = Car.objects.get(carId=carId)
        # message = request.POST['message'] or user.employee.message

        user.employee.empPhone = empPhone
        user.employee.empEmail = empEmail
        # user.employee.carId = carId
        # user.employee.message = message
        user.employee.save()

    # cars = Car.objects.all()
    context = {
        'user': user,
        # 'cars': cars,
    }
    return HttpResponse(template.render(context, request))


@login_required
def show_profiles(request):
    context = {}
    return render(request, 'hr/showprofiles.html', context)


@login_required
def showprofiles_asjson(request):
    employees = Employee.objects.all().annotate(
        userName=F('user__username'),
        positionName=F('empPosition__positionName'),
        lastLogin=F('user__last_login'),
    ).values(
        'empId', 'userName', 'empName', 'empDeptName', 'positionName',
        'empPhone', 'empEmail', 'lastLogin', 'empStatus',
    )

    structure = json.dumps(list(employees), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def view_profile(request, empId):
    employee = Employee.objects.get(empId=empId)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        post = form.save(commit=False)
        post.empDeptName = post.departmentName.deptName
        post.save()

        if employee.empStatus == 'N':
            emp = User.objects.get(id=employee.empId)
            emp.is_active = 0
            emp.save()
        return redirect('hr:showprofiles')

    else:
        form = EmployeeForm(instance=employee)

        context = {
            'employee': employee,
            'form': form,
        }
        return render(request, 'hr/viewprofile.html', context)


@login_required
def post_profile(request):
    if request.method == 'POST':
        userForm = UserForm(request.POST)
        if userForm.is_valid():
            new_user = User.objects.create_user(**userForm.cleaned_data)

            empForm = EmployeeForm(request.POST)
            post = empForm.save(commit=False)
            post.user = new_user
            post.empDeptName = post.departmentName.deptName
            post.save()

            if post.empStatus == 'N':
                new_user.is_active = 0
                new_user.save()

            return redirect('hr:showprofiles')

    else:
        userForm = UserForm()
        empForm = EmployeeForm()

        context = {
            'userForm': userForm,
            'empForm': empForm,
        }
        return render(request, 'hr/postprofile.html', context)


@login_required
def check_profile(request):
    result = 'Y'
    if Employee.objects.filter(user__username=request.GET['username']):
        result = 'usernameN'
    elif Employee.objects.filter(empCode=request.GET['empCode']):
        result = 'empCodeN'

    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def show_departments(request):
    deptLevelList = siteMap()
    context = {
        "deptLevelList": deptLevelList,
    }
    return render(request, 'hr/showdepartments.html', context)


@login_required
def showdepartments_asjson(request):
    departments = Department.objects.all().annotate(
        deptManagerName=F('deptManager__empName'),
        parentDeptName=F('parentDept__deptName'),
    ).values(
        'deptId', 'deptName', 'deptManagerName', 'deptLevel', 'parentDeptName',
    )

    structure = json.dumps(list(departments), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def view_department(request, deptId):
    dept = Department.objects.get(deptId=deptId)

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        post = form.save(commit=False)
        post.save()
        Employee.objects.filter(departmentName=dept).update(empDeptName=post.deptName)
        return redirect('hr:showdepartments')

    else:
        form = DepartmentForm(instance=dept)
        context = {
            'dept': dept,
            'form': form,
        }
        return render(request, 'hr/viewdepartment.html', context)


@login_required
def post_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        form.save()
        return redirect('hr:showdepartments')

    else:
        form = DepartmentForm()
        context = {
            'form': form,
        }
        return render(request, 'hr/postdepartment.html', context)


@login_required
def check_department(request):
    dept = Department.objects.filter(deptName=request.GET['deptName'])
    if dept:
        result = 'N'
    else:
        result = 'Y'
    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def show_punctuality(request, day=None):
    template = loader.get_template('hr/showpunctuality.html')
    if day is None:
        day = str(datetime.datetime.today())[:10]
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))

    if datetime.datetime.weekday(Date) == 0:
        beforeDate = Date - datetime.timedelta(days=3)
        afterDate = Date + datetime.timedelta(days=1)
    elif datetime.datetime.weekday(Date) == 4:
        beforeDate = Date - datetime.timedelta(days=1)
        afterDate = Date + datetime.timedelta(days=3)
    else:
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
    punctualityList.append(
        punctuality.filter(empId__empDeptName='경영지원본부').values(
            'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment', 'punctualityId'
        )
    )
    punctualityList.append(
        punctuality.filter(empId__empDeptName='영업1팀').values(
            'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment', 'punctualityId'
        )
    )
    punctualityList.append(
        punctuality.filter(empId__empDeptName='영업2팀').values(
            'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment', 'punctualityId'
        )
    )
    punctualityList.append(
        punctuality.filter(empId__empDeptName='인프라서비스사업팀').values(
            'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment', 'punctualityId'
        )
    )
    punctualityList.append(
        punctuality.filter(empId__empDeptName='솔루션지원팀').values(
            'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment', 'punctualityId'
        )
    )
    punctualityList.append(
        punctuality.filter(empId__empDeptName='DB지원팀').values(
            'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition', 'punctualityType', 'comment', 'punctualityId'
        )
    )

    for pun in punctualityList:
        for user in pun:
            absence = check_absence(user['empId_id'], startdate, day, False)
            if absence:
                user['absenceDate'] = []
                for a in absence:
                    user['absenceDate'].append(a.punctualityDate)
                user['absenceCount'] = len(absence)

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

    # context = {
    #     "datalen": datalen - 1,
    #     "errorList": errorList,
    #     "successCount": successCount,
    # }

    return redirect('hr:uploadcaps')


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

    punctualitys = Punctuality.objects.all()

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
        'punctuality': punctuality
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
        return redirect('hr:viewabsence', punctualityId)

    else:
        punctuality = Punctuality.objects.filter(Q(punctualityId=punctualityId))
        punctuality = punctuality.values('punctualityDate', 'empId__empDeptName', 'empId__empName', 'punctualityType', 'comment',
                                         'punctualityId').first()

        context = {
            'punctuality': punctuality
        }
        return render(request, 'hr/modifyabsence.html', context)


@login_required
@csrf_exempt
def email_registration(request):
    adminEmail = AdminEmail.objects.aggregate(Max('adminId'))
    if adminEmail['adminId__max']:
        adminEmail = AdminEmail.objects.get(adminId=adminEmail['adminId__max'])
        email = adminEmail.smtpEmail.split('@')
        id = email[0]
        address = email[1]
    else:
        adminEmail = ''
        id = ''
        address = ''

    context = {
        'adminEmail': adminEmail,
        'id': id,
        'address': address,
    }
    return render(request, 'hr/emailregistration.html', context)


@login_required
@csrf_exempt
def adminemail_asjson(request):
    smtpEmail = '{}@{}'.format(request.POST['smtpEmail'], request.POST['address'])
    smtpPassword = request.POST['smtpPassword']
    smtpServer = request.POST['smtpServer']
    smtpPort = request.POST['smtpPort']
    smtpSecure = request.POST['smtpSecure']
    smtpDatetime = datetime.datetime.now()
    result = adminemail_test(smtpEmail, smtpPassword, smtpServer, smtpPort, smtpSecure)
    if result == 'Y':
        AdminEmail.objects.create(
            smtpEmail=smtpEmail,
            smtpPassword=smtpPassword,
            smtpServer=smtpServer,
            smtpPort=smtpPort,
            smtpSecure=smtpSecure,
            smtpDatetime=smtpDatetime,
        )
    else:
        AdminEmail.objects.create(
            smtpEmail=smtpEmail,
            smtpPassword=smtpPassword,
            smtpServer=smtpServer,
            smtpPort=smtpPort,
            smtpSecure=smtpSecure,
            smtpDatetime=smtpDatetime,
            smtpStatus=result,
        )
        result = '입력하신정보가 올바르지 않습니다.\n다시 확인해 주세요.'
    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


def upload_emp_stamp(request, empId):
    emp = Employee.objects.get(empId=empId)
    for f in request.FILES.getlist('empStamp'):
        emp.empStamp = f
        emp.save()
    return redirect('hr:profile')


def redo_default_stamp(request, empId):
    emp = Employee.objects.get(empId=empId)
    emp.empStamp = 'stamp/accepted.png'
    emp.save()
    return redirect('hr:profile')


@login_required
@csrf_exempt
def show_vacations(request):
    if request.POST:
        empId = request.POST['empId']
        vacationType = request.POST['vacationType']
        vacationDays = request.POST['vacationDays']
        comment = request.POST['comment']
        employee = Employee.objects.get(empId=empId)
        now = datetime.datetime.now()
        expirationDate = datetime.date(now.year, 12, 31)
        AdminVacation.objects.create(
            empId=employee,
            vacationType=vacationType,
            vacationDays=vacationDays,
            creationDateTime=now,
            expirationDate=expirationDate,
            comment=comment,
        )
        if vacationType == '연차':
            employee.empAnnualLeave += float(vacationDays)
            employee.save()
        elif vacationType == '특별휴가':
            employee.empSpecialLeave += float(vacationDays)
            employee.save()
        return  redirect('hr:showvacations')

    employees = Employee.objects.filter(Q(empStatus='Y'))
    context = {
        'employees': employees,
    }
    return render(request, 'hr/showvacations.html', context)


@login_required
def showvacations_asjson(request):
    vacations = AdminVacation.objects.all().values(
        'vacationId', 'empId__empDeptName',  'empId__empName', 'vacationType', 'vacationDays', 'creationDateTime', 'expirationDate', 'comment',
    )

    structure = json.dumps(list(vacations), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def delete_vacation(request):
    if request.method == 'POST' and request.is_ajax():
        vacationId = request.POST.get('vacationId', None)
        AdminVacation.objects.filter(vacationId=vacationId).delete()
        return HttpResponse(json.dumps({'vacationId': vacationId}), content_type="application/json")