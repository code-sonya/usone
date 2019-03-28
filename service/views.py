from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, QueryDict
from django.db.models import Q, Sum

from .models import Servicereport, Serviceform, Vacation
from client.models import Company, Customer
from hr.models import Employee
from scheduler.models import Eventday
from .forms import ServicereportForm

from .functions import date_list, month_list, overtime, str_to_timedelta_hour
import datetime
import json


def post(request, postdate):
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
            form = ServicereportForm(request.POST)
            context = {'form': form,
                       'empName': empName,
                       'postdate': postdate,
                       }
            return render(request, 'service/post.html', context)

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")

