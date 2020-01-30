# -*- coding: utf-8 -*-

import datetime
import json

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F
from django.db.models import Max
from django.db.models import Q, Sum, Case, When, FloatField, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from extrapay.models import Car
from .forms import EmployeeForm, DepartmentForm, UserForm
from .functions import save_punctuality, check_absence, year_absence, adminemail_test, siteMap
from .models import Attendance, Employee, Punctuality, Department, AdminEmail, AdminVacation, ReturnVacation
from service.models import Vacation
from approval.models import Document
from extrapay.models import ExtraPay


@login_required
@csrf_exempt
def profile(request):
    template = loader.get_template('hr/profile.html')
    userId = request.user.id
    user = User.objects.get(id=userId)
    if request.method == "POST":
        empPhone = request.POST['empPhone'] or user.employee.empPhone
        empEmail = request.POST['empEmail'] or user.employee.empEmail
        carId = request.POST['carId'] or None
        if carId:
            carId = Car.objects.get(carId=carId)
        message = request.POST['message'] or user.employee.message

        user.employee.empPhone = empPhone
        user.employee.empEmail = empEmail
        user.employee.carId = carId
        user.employee.message = message
        user.employee.save()

    cars = Car.objects.all()
    context = {
        'user': user,
        'cars': cars,
    }
    return HttpResponse(template.render(context, request))


@login_required
def show_profiles(request):
    context = {}
    return render(request, 'hr/showprofiles.html', context)


@login_required
def showprofiles_asjson(request):
    empStatus = ''
    if 'empStatus' in request.GET.keys():
        if request.GET['empStatus']:
            empStatus = request.GET['empStatus']

    employees = Employee.objects.all()
    if empStatus:
        employees = employees.filter(empStatus=empStatus)

    employees = employees.annotate(
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

        if employee.empStatus == 'Y':
            emp = User.objects.get(id=employee.empId)
            emp.is_active = 1
            emp.save()

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
def delete_department(request, deptId):
    Department.objects.get(deptId=deptId).delete()
    return redirect('hr:showdepartments')


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

    if day <= '2020-01-31':
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
    else:
        punctualityList.append(
            punctuality.filter(empId__empDeptName='경영지원본부').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
            )
        )
        punctualityList.append(
            punctuality.filter(empId__empDeptName='경영지원실').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
            )
        )
        punctualityList.append(
            punctuality.filter(empId__empDeptName='인프라솔루션사업부').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
            )
        )
        punctualityList.append(
            punctuality.filter(empId__empDeptName='영업팀').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
            )
        )
        punctualityList.append(
            punctuality.filter(empId__empDeptName='R&D 전략사업부').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
            )
        )
        punctualityList.append(
            punctuality.filter(empId__empDeptName='AI Platform Labs').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
            )
        )
        punctualityList.append(
            punctuality.filter(empId__empDeptName='Technical Architecture팀').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
            )
        )
        punctualityList.append(
            punctuality.filter(empId__empDeptName='Platform Biz').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
            )
        )
        punctualityList.append(
            punctuality.filter(empId__empDeptName='DB Expert팀').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
            )
        )
        punctualityList.append(
            punctuality.filter(empId__empDeptName='솔루션팀').values(
                'empId_id', 'empId__empDeptName', 'empId__empName', 'empId__empPosition__positionName', 'punctualityType', 'comment', 'punctualityId'
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
    if request.method == 'POST':
        year = request.POST['year']
    else:
        year = str(datetime.datetime.today().year)
    employees = Employee.objects.filter(Q(empStatus='Y'))
    context = {
        'employees': employees,
        'year': year,
    }
    return render(request, 'hr/showvacations.html', context)


@csrf_exempt
@login_required
def showvacations_asjson(request):
    year = request.POST['year']
    if year:
        vacations = AdminVacation.objects.filter(Q(creationDateTime__year=year)).values(
            'vacationId', 'empId__empDeptName', 'empId__empName', 'vacationType', 'vacationDays', 'creationDateTime', 'expirationDate', 'comment',
        )
    else:
        vacations = AdminVacation.objects.all().values(
            'vacationId', 'empId__empDeptName', 'empId__empName', 'vacationType', 'vacationDays', 'creationDateTime', 'expirationDate', 'comment',
        )
    structure = json.dumps(list(vacations), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def delete_vacation(request):
    if request.method == 'POST' and request.is_ajax():
        vacationId = request.POST.get('vacationId', None)
        adminVacation = AdminVacation.objects.get(vacationId=vacationId)
        employee = Employee.objects.get(empId=adminVacation.empId.empId)
        employee.empAnnualLeave = employee.empAnnualLeave - adminVacation.vacationDays
        employee.save()
        adminVacation.delete()
        return HttpResponse(json.dumps({'vacationId': vacationId}), content_type="application/json")

@login_required
@csrf_exempt
def save_vacation(request):
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
    return redirect('hr:showvacations')


@login_required
@csrf_exempt
def vacations_excel(request):
    if request.method == 'POST':
        year = request.POST['year']
    else:
        year = str(datetime.datetime.today().year)
    context = {
        'year': year,
    }
    return render(request, 'hr/vacationsexcel.html', context)


@csrf_exempt
@login_required
def vacationsexcel_asjson(request):
    year = request.POST['year']
    # 직원별 연차, 특별 휴가 생성 일 수
    if year:
        adminvacation = AdminVacation.objects.filter(Q(creationDateTime__year=year)).values('empId', 'vacationType').annotate(sumvacationDays=Sum('vacationDays'))
        empvacation = AdminVacation.objects.filter(Q(creationDateTime__year=year)).values('empId').annotate(empcount=Count('empId'))

    else:
        adminvacation = AdminVacation.objects.all().values('empId',  'vacationType').annotate(sumvacationDays=Sum('vacationDays'))
        empvacation = AdminVacation.objects.filter(Q(creationDateTime__year=year)).values('empId').annotate(empcount=Count('empId'))

    # 직원별 휴가 타입별 휴가 사용 일 수
    # vacationType => 일차, 오전반차, 오후반차
    # vacationCategory => 일차, 오전반차, 오후반차
    vacations = Vacation.objects.filter(Q(vacationDate__year=year)&(Q(vacationStatus='Y')|Q(vacationStatus='N'))).annotate(
        vacationDay=Case(
            When(vacationType='일차', then=1.0),
            default=0.5,
            output_field=FloatField()
        ),
        categoryName=F('vacationCategory__categoryName'),
    ).values('empId', 'categoryName').annotate(
        vacationDays=Sum('vacationDay')
    )

    vacationList = []
    for emp in empvacation:
        vacationDict = {'createAnnualLeave': 0, 'createSpecialLeave': 0, 'remainingAnnualLeave': 0, 'remainingSpecialLeave': 0,
                        'useAnnualLeave': 0, 'useSpecialLeave': 0, 'useTraining': 0, 'useInvestigation': 0, 'useSickleave': 0, 'useMaternityleave': 0, 'useCompensation': 0}
        employee = Employee.objects.get(empId=emp['empId'])
        vacationDict['empId'] = employee.empId
        vacationDict['empName'] = employee.empName
        vacationDict['empStartDate'] = employee.empStartDate
        vacationDict['empDeptName'] = employee.empDeptName
        for create in adminvacation.filter(Q(empId=emp['empId'])):
            if create['vacationType'] == '연차':
                vacationDict['createAnnualLeave'] = create['sumvacationDays']
            elif create['vacationType'] == '특별휴가':
                vacationDict['createSpecialLeave'] = create['sumvacationDays']
            for useVacation in vacations.filter(empId=create['empId']):
                if useVacation['categoryName'] == '연차':
                    vacationDict['useAnnualLeave'] = useVacation['vacationDays']
                elif useVacation['categoryName'] == '특별휴가':
                    vacationDict['useSpecialLeave'] = useVacation['vacationDays']
                elif useVacation['categoryName'] == '훈련':
                    vacationDict['useTraining'] = useVacation['vacationDays']
                elif useVacation['categoryName'] == '경조사':
                    vacationDict['useInvestigation'] = useVacation['vacationDays']
                elif useVacation['categoryName'] == '병가':
                    vacationDict['useSickleave'] = useVacation['vacationDays']
                elif useVacation['categoryName'] == '출산':
                    vacationDict['useMaternityleave'] = useVacation['vacationDays']
                elif useVacation['categoryName'] == '보상휴가':
                    vacationDict['useCompensation'] = useVacation['vacationDays']

        vacationDict['remainingAnnualLeave'] = vacationDict['createAnnualLeave'] - vacationDict['useAnnualLeave']
        vacationDict['remainingSpecialLeave'] = vacationDict['createSpecialLeave'] - vacationDict['useSpecialLeave']
        vacationList.append(vacationDict)
    structure = json.dumps(vacationList, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def return_vacation(request):
    if request.method == 'POST':
        year = request.POST['year']
    else:
        year = str(datetime.datetime.today().year)

    employees = Employee.objects.filter(Q(empStatus='Y'))
    context = {
        'year': year,
        'employees': employees,
    }
    return render(request, 'hr/returnvacation.html', context)


@login_required
@csrf_exempt
def returnvacation_asjson(request):
    year = request.POST['year']

    # 휴가 취소 내역
    if year:
        returnVacations = ReturnVacation.objects.filter(Q(returnDateTime__year=year))\
            .values('returnDateTime', 'empId__empDeptName', 'empId__empName', 'vacationId__documentId__documentId', 'vacationId__documentId__title', 'vacationId__vacationDate',  'vacationId__vacationType', 'vacationId__vacationCategory__categoryName', 'comment')

    else:
        returnVacations = ReturnVacation.objects.all()\
            .values('returnDateTime', 'empId__empDeptName', 'empId__empName', 'vacationId__documentId__documentId', 'vacationId__documentId__title', 'vacationId__vacationType', 'vacationId__vacationCategory__categoryName', 'comment')


    structure = json.dumps(list(returnVacations), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def vacationdocument_asjson(request):
    empId = request.POST['empId']
    vacationdocument = Document.objects.filter(Q(writeEmp=empId) & Q(documentStatus='완료') & Q(formId__formTitle='휴가신청서')).values('documentId','writeEmp', 'draftDatetime', 'title')

    structure = json.dumps(list(vacationdocument), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def cancel_vacation(request):
    empId = request.POST['empId']
    documentId = request.POST['document']
    comment = request.POST['comment']
    document = Document.objects.get(documentId=documentId)
    document.documentStatus = '결재완료후취소'
    document.save()
    empId = Employee.objects.get(empId=empId)
    returnvacations = Vacation.objects.filter(Q(documentId=documentId))
    for returnvacation in returnvacations:
        # vacation = Vacation.objects.get(vacationId=returnvacation.vacationId)
        ReturnVacation.objects.create(
            empId=empId,
            returnDateTime=datetime.datetime.now(),
            vacationId=returnvacation,
            comment=comment,
        )
        returnvacation.vacationStatus='X'
        returnvacation.comment='결재완료후취소'
        returnvacation.save()
        vacationDay = 0
        if returnvacation.vacationType == '일차':
            vacationDay += 1
        else:
            vacationDay += 0.5
        categoryName = returnvacation.vacationCategory.categoryName
        if categoryName == '연차':
            empId.empAnnualLeave += vacationDay
            empId.save()
        elif categoryName == '특별휴가':
            empId.empSpecialLeave += vacationDay
            empId.save()
        elif categoryName == '보상휴가':
            rewardVacationType = returnvacation.rewardVacationType
            now = document.draftDatetime
            yyyy = str(now)[:4]
            mm = str(now)[5:7]
            if mm == '01':
                yyyyBefore = str(int(yyyy) - 1)
                mmBefore = '12'
            else:
                yyyyBefore = yyyy
                mmBefore = str(int(mm) - 1).zfill(2)
            if rewardVacationType == '당월보상휴가':
                # 보상휴가일수
                extraWork = ExtraPay.objects.filter(empId=empId, overHourDate__year=yyyy, overHourDate__month=mm)
                extraWorkObj = extraWork.first()
                extraWorkObj.compensatedHour -= vacationDay * 8
                extraWorkObj.save()
            elif rewardVacationType == '전월보상휴가':
                # 보상휴가일수
                extraWorkBefore = ExtraPay.objects.filter(empId=empId, overHourDate__year=yyyyBefore, overHourDate__month=mmBefore)
                extraWorkBeforeObj = extraWorkBefore.first()
                extraWorkBeforeObj.compensatedHour -= vacationDay * 8
                extraWorkBeforeObj.save()

    return redirect('hr:returnvacation')


@login_required
@csrf_exempt
def detailvacation_asjson(request):
    empId = request.POST['empId']
    year = request.POST['year']

    vacations = Vacation.objects.filter(Q(empId=empId) & Q(vacationDate__year=year) & Q(vacationStatus='Y')).values('vacationDate', 'vacationType', 'vacationCategory__categoryName')

    structure = json.dumps(list(vacations), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


