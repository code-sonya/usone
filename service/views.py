from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, QueryDict
from django.db.models import Q, Sum
from django.contrib.auth.models import User

from .models import Servicereport, Serviceform, Vacation
from client.models import Company, Customer
from hr.models import Employee
from scheduler.models import Eventday
from .forms import ServicereportForm, ServiceformForm

from .functions import date_list, month_list, overtime, str_to_timedelta_hour, dayreport_query, dayreport_query2
import datetime
import json


def post_service(request, postdate):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        # 로그인 사용자 정보
        empId = Employee(empId=request.user.employee.empId)
        empName = request.user.employee.empName
        empDeptName = request.user.employee.empDeptName

        if request.method == "POST":
            form = ServicereportForm(request.POST)

            if form.is_valid():
                post = form.save(commit=False)
                post.empId = empId
                post.empName = empName
                post.empDeptName = empDeptName
                post.serviceFinishDatetime = datetime.datetime.now()
                for_status = request.POST['for']

                # 기본등록
                if for_status == 'for_n':
                    post.serviceStartDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
                    post.serviceEndDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
                    post.serviceDate = str(post.serviceStartDatetime)[:10]
                    post.serviceHour = str_to_timedelta_hour(post.serviceEndDatetime, post.serviceStartDatetime)
                    post.serviceOverHour = overtime(post.serviceStartDatetime, post.serviceEndDatetime)
                    post.serviceRegHour = post.serviceHour - post.serviceOverHour
                    post.save()
                    return redirect('scheduler')

                # 매월반복
                elif for_status == 'for_my':
                    dateRange = month_list(form.clean()['startdate'], form.clean()['enddate'])
                    timeCalculateFlag = True
                    for date in dateRange:
                        post.serviceStartDatetime = str(date) + ' ' + form.clean()['starttime']
                        post.serviceEndDatetime = str(date) + ' ' + form.clean()['endtime']
                        post.serviceDate = str(post.serviceStartDatetime)[:10]
                        if timeCalculateFlag:
                            post.serviceHour = str_to_timedelta_hour(post.serviceEndDatetime, post.serviceStartDatetime)
                            post.serviceOverHour = overtime(post.serviceStartDatetime, post.serviceEndDatetime)
                            post.serviceRegHour = post.serviceHour - post.serviceOverHour
                            timeCalculateFlag = False
                        Servicereport.objects.create(
                            serviceDate=post.serviceDate,
                            empId=post.empId,
                            empName=post.empName,
                            empDeptName=post.empDeptName,
                            companyName=post.companyName,
                            serviceType=post.serviceType,
                            serviceStartDatetime=post.serviceStartDatetime,
                            serviceEndDatetime=post.serviceEndDatetime,
                            serviceFinishDatetime=post.serviceFinishDatetime,
                            serviceHour=post.serviceHour,
                            serviceOverHour=post.serviceOverHour,
                            serviceRegHour=post.serviceRegHour,
                            serviceLocation=post.serviceLocation,
                            directgo=post.directgo,
                            serviceTitle=post.serviceTitle,
                            serviceDetails=post.serviceDetails,
                            serviceStatus=post.serviceStatus,
                        )
                    return redirect('scheduler')

                # 기간(휴일제외)
                elif for_status == 'for_hn':
                    dateRange = date_list(form.clean()['startdate'], form.clean()['enddate'])
                    timeCalculateFlag = True
                    for date in dateRange:
                        if not Eventday.objects.filter(eventDate=date) and date.weekday() != 5 and date.weekday() != 6:
                            post.serviceStartDatetime = str(date) + ' ' + form.clean()['starttime']
                            post.serviceEndDatetime = str(date) + ' ' + form.clean()['endtime']
                            post.serviceDate = str(post.serviceStartDatetime)[:10]
                            if timeCalculateFlag:
                                post.serviceHour = str_to_timedelta_hour(post.serviceEndDatetime, post.serviceStartDatetime)
                                post.serviceOverHour = overtime(post.serviceStartDatetime, post.serviceEndDatetime)
                                post.serviceRegHour = post.serviceHour - post.serviceOverHour
                                timeCalculateFlag = False
                            Servicereport.objects.create(
                                serviceDate=post.serviceDate,
                                empId=post.empId,
                                empName=post.empName,
                                empDeptName=post.empDeptName,
                                companyName=post.companyName,
                                serviceType=post.serviceType,
                                serviceStartDatetime=post.serviceStartDatetime,
                                serviceEndDatetime=post.serviceEndDatetime,
                                serviceFinishDatetime=post.serviceFinishDatetime,
                                serviceHour=post.serviceHour,
                                serviceOverHour=post.serviceOverHour,
                                serviceRegHour=post.serviceRegHour,
                                serviceLocation=post.serviceLocation,
                                directgo=post.directgo,
                                serviceTitle=post.serviceTitle,
                                serviceDetails=post.serviceDetails,
                                serviceStatus=post.serviceStatus,
                            )
                    return redirect('scheduler')

                # 기간(휴일포함)
                elif for_status == 'for_hy':
                    dateRange = date_list(form.clean()['startdate'], form.clean()['enddate'])
                    timeCalculateFlag = True
                    for date in dateRange:
                        post.serviceStartDatetime = str(date) + ' ' + form.clean()['starttime']
                        post.serviceEndDatetime = str(date) + ' ' + form.clean()['endtime']
                        post.serviceDate = str(post.serviceStartDatetime)[:10]
                        if timeCalculateFlag:
                            post.serviceHour = str_to_timedelta_hour(post.serviceEndDatetime, post.serviceStartDatetime)
                            post.serviceOverHour = overtime(post.serviceStartDatetime, post.serviceEndDatetime)
                            post.serviceRegHour = post.serviceHour - post.serviceOverHour
                            timeCalculateFlag = False
                        Servicereport.objects.create(
                            serviceDate=post.serviceDate,
                            empId=post.empId,
                            empName=post.empName,
                            empDeptName=post.empDeptName,
                            companyName=post.companyName,
                            serviceType=post.serviceType,
                            serviceStartDatetime=post.serviceStartDatetime,
                            serviceEndDatetime=post.serviceEndDatetime,
                            serviceFinishDatetime=post.serviceFinishDatetime,
                            serviceHour=post.serviceHour,
                            serviceOverHour=post.serviceOverHour,
                            serviceRegHour=post.serviceRegHour,
                            serviceLocation=post.serviceLocation,
                            directgo=post.directgo,
                            serviceTitle=post.serviceTitle,
                            serviceDetails=post.serviceDetails,
                            serviceStatus=post.serviceStatus,
                        )
                    return redirect('scheduler')

        else:
            form = ServicereportForm()
            form.fields['startdate'].initial = postdate
            form.fields['starttime'].initial = "09:00"
            form.fields['enddate'].initial = postdate
            form.fields['endtime'].initial = "18:00"
            serviceforms = Serviceform.objects.filter(empId=empId)
            context = {
                'form': form,
                'postdate': postdate,
                'serviceforms': serviceforms,
            }
            return render(request, 'service/postservice.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def post_vacation(request):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        # 로그인 사용자 정보
        empId = Employee(empId=request.user.employee.empId)
        empName = request.user.employee.empName
        empDeptName = request.user.employee.empDeptName

        if request.method == "POST":
            vacationTypeDict = request.POST
            dateArray = list(request.POST.keys())[1:]

            for vacationDate in dateArray:
                if vacationTypeDict[vacationDate] == 'all':
                    vacationType = "일차"
                elif vacationTypeDict[vacationDate] == 'am':
                    vacationType = "오전반차"
                elif vacationTypeDict[vacationDate] == 'pm':
                    vacationType = "오후반차"
                else:
                    vacationType = ""

                Vacation.objects.create(
                    empId=empId,
                    empName=empName,
                    empDeptName=empDeptName,
                    vacationDate=vacationDate,
                    vacationType=vacationType
                )
            return redirect('scheduler')

        else:
            context = {}
            return render(request, 'service/postvacation.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def post_serviceform(request):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        empId = Employee(empId=request.user.employee.empId)

        if request.method == "POST":
            form = ServiceformForm(request.POST)

            if form.is_valid():
                post = form.save(commit=False)
                post.empId = empId
                post.save()
                return redirect('service:postservice', str(datetime.date.today()))

        else:
            form = ServiceformForm()
            form.fields['serviceStartTime'].initial = "09:00"
            form.fields['serviceEndTime'].initial = "18:00"
            context = {
                'form': form,
            }
            return render(request, 'service/postserviceform.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def show_services(request):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:

        if request.method == "POST":
            startdate = request.POST['startdate']
            enddate = request.POST['enddate']
            empDeptName = request.POST['empDeptName']
            empName = request.POST['empName']
            companyName = request.POST['companyName']
            serviceType = request.POST['serviceType']
            serviceTitle = request.POST['serviceTitle']

            services = Servicereport.objects.all()
            if startdate:
                services = services.filter(serviceDate__gte=startdate)
            if enddate:
                services = services.filter(serviceDate__lte=enddate)
            if empDeptName:
                services = services.filter(empDeptName__icontains=empDeptName)
            if empName:
                services = services.filter(empName__icontains=empName)
            if companyName:
                services = services.filter(companyName__companyName__icontains=companyName)
            if serviceType:
                services = services.filter(serviceType__icontains=serviceType)
            if serviceTitle:
                services = services.filter(Q(serviceTitle__icontains=serviceTitle) | Q(serviceDetails__icontains=serviceTitle))

            context = {
                'services': services,
                'today': datetime.datetime.today(),
                'sumHour': services.aggregate(Sum('serviceHour'))['serviceHour__sum'],
                'sumOverHour': services.aggregate(Sum('serviceOverHour'))['serviceOverHour__sum'] or 0
            }
            return render(request, 'service/showservices.html', context)

        else:
            empId = Employee(empId=request.user.employee.empId)
            services = Servicereport.objects.filter(empId=empId)

            context = {
                'services': services,
                'today': datetime.datetime.today(),
                'sumHour': services.aggregate(Sum('serviceHour'))['serviceHour__sum'] or 0,
                'sumOverHour': services.aggregate(Sum('serviceOverHour'))['serviceOverHour__sum'] or 0
            }
            return render(request, 'service/showservices.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def view_service(request, serviceId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        service = Servicereport.objects.get(serviceId=serviceId)

        context = {
            'service': service,
        }

        return render(request, 'service/viewservice.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def save_service(request, serviceId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        service = Servicereport.objects.get(serviceId=serviceId)
        service.serviceStatus = 'Y'
        service.serviceFinishDatetime = datetime.datetime.now()
        service.save()
        
        return HttpResponse("일정 완료. 메일 연결")

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def delete_service(request, serviceId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        Servicereport.objects.filter(serviceId=serviceId).delete()

        return redirect('scheduler')

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def modify_service(request, serviceId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        # 로그인 사용자 정보
        instance = Servicereport.objects.get(serviceId=serviceId)
        empId = Employee(empId=request.user.employee.empId)
        empName = request.user.employee.empName
        empDeptName = request.user.employee.empDeptName

        if request.method == "POST":
            form = ServicereportForm(request.POST, instance=instance)

            if form.is_valid():
                post = form.save(commit=False)
                post.empId = empId
                post.empName = empName
                post.empDeptName = empDeptName
                post.serviceFinishDatetime = datetime.datetime.now()
                post.serviceStartDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
                post.serviceEndDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
                post.serviceDate = str(post.serviceStartDatetime)[:10]
                post.serviceHour = str_to_timedelta_hour(post.serviceEndDatetime, post.serviceStartDatetime)
                post.serviceOverHour = overtime(post.serviceStartDatetime, post.serviceEndDatetime)
                post.serviceRegHour = post.serviceHour - post.serviceOverHour
                post.save()
                return redirect('scheduler')
        else:
            form = ServicereportForm(instance=instance)
            form.fields['startdate'].initial = str(instance.serviceStartDatetime)[:10]
            form.fields['starttime'].initial = str(instance.serviceStartDatetime)[11:16]
            form.fields['enddate'].initial = str(instance.serviceEndDatetime)[:10]
            form.fields['endtime'].initial = str(instance.serviceEndDatetime)[11:16]

            context = {
                'form': form,
            }
            return render(request, 'service/postservice.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def copy_service(request, serviceId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        # 로그인 사용자 정보
        instance = Servicereport.objects.get(serviceId=serviceId)
        empId = Employee(empId=request.user.employee.empId)
        empName = request.user.employee.empName
        empDeptName = request.user.employee.empDeptName
        Servicereport.objects.create(
            serviceDate=instance.serviceDate,
            empId=empId,
            empName=empName,
            empDeptName=empDeptName,
            companyName=instance.companyName,
            serviceType=instance.serviceType,
            serviceStartDatetime=instance.serviceStartDatetime,
            serviceEndDatetime=instance.serviceEndDatetime,
            serviceFinishDatetime=instance.serviceFinishDatetime,
            serviceHour=instance.serviceHour,
            serviceOverHour=instance.serviceOverHour,
            serviceRegHour=instance.serviceRegHour,
            serviceLocation=instance.serviceLocation,
            directgo=instance.directgo,
            serviceTitle=instance.serviceTitle,
            serviceDetails=instance.serviceDetails,
            serviceStatus=instance.serviceStatus,
        )
        return redirect('scheduler')

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def show_serviceforms(request):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        empId = Employee(empId=request.user.employee.empId)
        serviceforms = Serviceform.objects.filter(empId=empId)

        context = {
            'serviceforms': serviceforms,
        }
        return render(request, 'service/showserviceforms.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def modify_serviceform(request, serviceFormId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        instance = Serviceform.objects.get(serviceFormId=serviceFormId)
        empId = Employee(empId=request.user.employee.empId)

        if request.method == "POST":
            form = ServiceformForm(request.POST, instance=instance)

            if form.is_valid():
                post = form.save(commit=False)
                post.empId = empId
                post.save()
                return redirect('service:postservice', str(datetime.date.today()))

        else:
            form = ServiceformForm(instance=instance)
            context = {
                'form': form,
                'serviceFormId': serviceFormId,
            }
            return render(request, 'service/postserviceform.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def delete_serviceform(request, serviceFormId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        Serviceform.objects.filter(serviceFormId=serviceFormId).delete()

        return redirect('service:showserviceforms')

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def show_vacations(request):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        empId = Employee(empId=request.user.employee.empId)
        vacations = Vacation.objects.filter(empId=empId)

        context = {
            'vacations': vacations,
        }
        return render(request, 'service/showvacations.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def delete_vacation(request, vacationId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        Vacation.objects.filter(vacationId=vacationId).delete()

        return redirect('service:showvacations')

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def day_report(request, day):
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    beforeDate = Date - datetime.timedelta(days=1)
    afterDate = Date + datetime.timedelta(days=1)

    solution = dayreport_query(empDeptName="솔루션지원팀", day=day)
    db = dayreport_query(empDeptName="DB지원팀", day=day)

    context = {
        'day': day,
        'Date': Date,
        'beforeDate': beforeDate,
        'afterDate': afterDate,
        'solution': solution,
        'db': db,
    }

    return render(request, 'service/dayreport.html', context)


def day_report2(request, day):
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    beforeDate = Date - datetime.timedelta(days=1)
    afterDate = Date + datetime.timedelta(days=1)

    solution = dayreport_query2(empDeptName="솔루션지원팀", day=day)
    db = dayreport_query2(empDeptName="DB지원팀", day=day)

    context = {
        'day': day,
        'Date': Date,
        'beforeDate': beforeDate,
        'afterDate': afterDate,
        'serviceSolution': solution[0],
        'educationSolution': solution[1],
        'vacationSolution': solution[2],
        'serviceDb': db[0],
        'educationDb': db[1],
        'vacationDb': db[2],
    }

    return render(request, 'service/dayreport2.html', context)