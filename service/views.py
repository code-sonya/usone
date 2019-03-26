from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, QueryDict
from django.db.models import Q, Sum

from .models import Servicereport, Serviceform, Vacation
from client.models import Company, Customer
from hr.models import Employee
from scheduler.models import Eventday
from .forms import ServicereportForm

from .functions import date_list, overtime, str_timedelta_hour
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
            for_status = request.POST['for']

            # 기간(휴일제외)
            if for_status == 'for_hn':
                dateRange = date_list(form.clean()['startdate'], form.clean()['enddate'])
                count = 0

                for date in dateRange:
                    if not Eventday.objects.filter(eventDate=date) and date.weekday() != 5 and date.weekday() != 6:
                        post = form.save(commit=False)
                        post.empId = empId
                        post.empName = empName
                        post.empDeptName = empDeptName
                        post.serviceFinishDatetime = datetime.datetime.now()
                        post.serviceStartDatetime = str(date) + ' ' + form.clean()['starttime']
                        post.serviceEndDatetime = str(date) + ' ' + form.clean()['endtime']
                        post.serviceDate = str(post.serviceStartDatetime)[:10]
                        if count == 0:
                            post.serviceHour = str_timedelta_hour(post.serviceEndDatetime, post.serviceStartDatetime)
                            post.serviceOverHour = overtime(post.serviceStartDatetime, post.serviceEndDatetime)
                            post.serviceRegHour = post.serviceHour - post.serviceOverHour
                            count += 1
                        post.serviceStatus = 'N'
                        post.save()
            # 기본등록
            if for_status == 'for_n':
                post = form.save(commit=False)
                post.empId = empId
                post.empName = empName
                post.empDeptName = empDeptName
                post.serviceFinishDatetime = datetime.datetime.now()
                post.serviceStartDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
                post.serviceEndDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
                post.serviceDate = str(post.serviceStartDatetime)[:10]
                post.serviceHour = str_timedelta_hour(post.serviceEndDatetime, post.serviceStartDatetime)
                post.serviceOverHour = overtime(post.serviceStartDatetime, post.serviceEndDatetime)
                post.serviceRegHour = post.serviceHour - post.serviceOverHour
                post.serviceStatus = 'N'
                post.save()
            # return redirect('scheduler:scheduler_month') # redirect URL 설정
            return HttpResponse("일정등록 완료!")

        else:
            form = ServicereportForm(request.POST)
            context = {'form': form,
                       'empName': empName,
                       'postdate': postdate,
                       }
            return render(request, 'service/post.html', context)

    else:
        return HttpResponse("로그아웃")





#
# if request.method == "POST":
#     form = PostForm(request.POST)
#
#     if form.is_valid():
#         post = form.save(commit=False)
#
#         post.EMP_NAME = name
#         post.DEPT_NAME = EMPLOYEES.objects.filter(emp_name__icontains=post.EMP_NAME)[0].dept_name
#         post.END_DATETIME = datetime.datetime.now()
#
#         for_status = request.POST['for']
#
#         # 기간(휴일제외)
#         if for_status == 'for_hn':
#             date = date_list(form.clean()['startdate'], form.clean()['finishdate'])
#             count = 0
#             for i in date:
#                 if not EVENT.objects.filter(EVENT_DATE=i) and i.weekday() != 5 and i.weekday() != 6:
#                     post.START_DATETIME = str(i) + ' ' + form.clean()['starttime']
#                     post.FINISH_DATETIME = str(i) + ' ' + form.clean()['finishtime']
#                     post.SERVICE_DATE = str(post.START_DATETIME)[:10]
#                     if count == 0:
#                         st = datetime.datetime(year=int(str(post.FINISH_DATETIME)[:4]),
#                                                month=int(str(post.FINISH_DATETIME)[5:7]),
#                                                day=int(str(post.FINISH_DATETIME)[8:10]),
#                                                hour=int(str(post.FINISH_DATETIME)[11:13]),
#                                                minute=int(str(post.FINISH_DATETIME)[14:16]), second=00) - \
#                              datetime.datetime(year=int(str(post.START_DATETIME)[:4]),
#                                                month=int(str(post.START_DATETIME)[5:7]),
#                                                day=int(str(post.START_DATETIME)[8:10]),
#                                                hour=int(str(post.START_DATETIME)[11:13]),
#                                                minute=int(str(post.START_DATETIME)[14:16]), second=00)
#                         post.HOUR = round(st.total_seconds() / 60 / 60, 1)
#                         post.HOUR_EXCEPT_DISPATCH = post.HOUR
#                         post.MINUTE = int(st.total_seconds() / 60)
#                         post.OVER_MINUTE = int(overtime_sum(post.START_DATETIME, post.FINISH_DATETIME))
#                         post.OVER_HOUR = round((post.OVER_MINUTE / 60), 1)
#                         post.REG_HOUR = post.HOUR - post.OVER_HOUR
#                         post.REG_MINUTE = post.MINUTE - post.OVER_MINUTE
#                         count += 1
#                     SERVICES.objects.create(SERVICE_DATE=post.SERVICE_DATE, DEPT_NAME=post.DEPT_NAME, EMP_NAME=post.EMP_NAME,
#                                             COMPANY_NAME=post.COMPANY_NAME, SERVICE_TYPE=post.SERVICE_TYPE, START_DATETIME=post.START_DATETIME,
#                                             FINISH_DATETIME=post.FINISH_DATETIME, END_DATETIME=post.END_DATETIME,
#                                             HOUR=post.HOUR, HOUR_EXCEPT_DISPATCH=post.HOUR_EXCEPT_DISPATCH, MINUTE=post.MINUTE,
#                                             OVER_HOUR=post.OVER_HOUR, OVER_MINUTE=post.OVER_MINUTE, REG_HOUR=post.REG_HOUR, REG_MINUTE=post.REG_MINUTE,
#                                             LOCATION=post.LOCATION, JIGCHUL_YN=post.JIGCHUL_YN, DETAILS=post.DETAILS, SERVICE_STATUS='N')
#             return redirect('scheduler:scheduler_month')
#
#         # 기간(휴일포함)
#         if for_status == 'for_hy':
#             date = date_list(form.clean()['startdate'], form.clean()['finishdate'])
#             for i in date:
#
#                 post.START_DATETIME = str(i) + ' ' + form.clean()['starttime']
#                 post.FINISH_DATETIME = str(i) + ' ' + form.clean()['finishtime']
#                 post.SERVICE_DATE = str(post.START_DATETIME)[:10]
#                 st = datetime.datetime(year=int(str(post.FINISH_DATETIME)[:4]),
#                                        month=int(str(post.FINISH_DATETIME)[5:7]),
#                                        day=int(str(post.FINISH_DATETIME)[8:10]),
#                                        hour=int(str(post.FINISH_DATETIME)[11:13]),
#                                        minute=int(str(post.FINISH_DATETIME)[14:16]), second=00) - \
#                      datetime.datetime(year=int(str(post.START_DATETIME)[:4]),
#                                        month=int(str(post.START_DATETIME)[5:7]),
#                                        day=int(str(post.START_DATETIME)[8:10]),
#                                        hour=int(str(post.START_DATETIME)[11:13]),
#                                        minute=int(str(post.START_DATETIME)[14:16]), second=00)
#                 post.HOUR = round(st.total_seconds() / 60 / 60, 1)
#                 post.HOUR_EXCEPT_DISPATCH = post.HOUR
#                 post.MINUTE = int(st.total_seconds() / 60)
#                 post.OVER_MINUTE = int(overtime_sum(post.START_DATETIME, post.FINISH_DATETIME))
#                 post.OVER_HOUR = round((post.OVER_MINUTE / 60), 1)
#                 post.REG_HOUR = post.HOUR - post.OVER_HOUR
#                 post.REG_MINUTE = post.MINUTE - post.OVER_MINUTE
#                 SERVICES.objects.create(SERVICE_DATE=post.SERVICE_DATE, DEPT_NAME=post.DEPT_NAME, EMP_NAME=post.EMP_NAME,
#                                         COMPANY_NAME=post.COMPANY_NAME, SERVICE_TYPE=post.SERVICE_TYPE, START_DATETIME=post.START_DATETIME,
#                                         FINISH_DATETIME=post.FINISH_DATETIME, END_DATETIME=post.END_DATETIME,
#                                         HOUR=post.HOUR, HOUR_EXCEPT_DISPATCH=post.HOUR_EXCEPT_DISPATCH, MINUTE=post.MINUTE,
#                                         OVER_HOUR=post.OVER_HOUR, OVER_MINUTE=post.OVER_MINUTE, REG_HOUR=post.REG_HOUR, REG_MINUTE=post.REG_MINUTE,
#                                         LOCATION=post.LOCATION, JIGCHUL_YN=post.JIGCHUL_YN, DETAILS=post.DETAILS, SERVICE_STATUS='N')
#             return redirect('scheduler:scheduler_month')
#
#         # 매월반복
#         if for_status == 'for_my':
#             date = month_list(form.clean()['startdate'], form.clean()['finishdate'])
#             for i in date:
#                 post.START_DATETIME = str(i) + ' ' + form.clean()['starttime']
#                 post.FINISH_DATETIME = str(i) + ' ' + form.clean()['finishtime']
#                 post.SERVICE_DATE = str(post.START_DATETIME)[:10]
#                 st = datetime.datetime(year=int(str(post.FINISH_DATETIME)[:4]),
#                                        month=int(str(post.FINISH_DATETIME)[5:7]),
#                                        day=int(str(post.FINISH_DATETIME)[8:10]),
#                                        hour=int(str(post.FINISH_DATETIME)[11:13]),
#                                        minute=int(str(post.FINISH_DATETIME)[14:16]), second=00) - \
#                      datetime.datetime(year=int(str(post.START_DATETIME)[:4]),
#                                        month=int(str(post.START_DATETIME)[5:7]),
#                                        day=int(str(post.START_DATETIME)[8:10]),
#                                        hour=int(str(post.START_DATETIME)[11:13]),
#                                        minute=int(str(post.START_DATETIME)[14:16]), second=00)
#                 post.HOUR = round(st.total_seconds() / 60 / 60, 1)
#                 post.HOUR_EXCEPT_DISPATCH = post.HOUR
#                 post.MINUTE = int(st.total_seconds() / 60)
#                 post.OVER_MINUTE = int(overtime_sum(post.START_DATETIME, post.FINISH_DATETIME))
#                 post.OVER_HOUR = round((post.OVER_MINUTE / 60), 1)
#                 post.REG_HOUR = post.HOUR - post.OVER_HOUR
#                 post.REG_MINUTE = post.MINUTE - post.OVER_MINUTE
#                 SERVICES.objects.create(SERVICE_DATE=post.SERVICE_DATE, DEPT_NAME=post.DEPT_NAME, EMP_NAME=post.EMP_NAME,
#                                         COMPANY_NAME=post.COMPANY_NAME, SERVICE_TYPE=post.SERVICE_TYPE, START_DATETIME=post.START_DATETIME,
#                                         FINISH_DATETIME=post.FINISH_DATETIME, END_DATETIME=post.END_DATETIME,
#                                         HOUR=post.HOUR, HOUR_EXCEPT_DISPATCH=post.HOUR_EXCEPT_DISPATCH, MINUTE=post.MINUTE,
#                                         OVER_HOUR=post.OVER_HOUR, OVER_MINUTE=post.OVER_MINUTE, REG_HOUR=post.REG_HOUR, REG_MINUTE=post.REG_MINUTE,
#                                         LOCATION=post.LOCATION, JIGCHUL_YN=post.JIGCHUL_YN, DETAILS=post.DETAILS, SERVICE_STATUS='N')
#             return redirect('scheduler:scheduler_month')
#
#         post.START_DATETIME = form.clean()['startdate'] + ' ' + form.clean()['starttime']
#         post.FINISH_DATETIME = form.clean()['finishdate'] + ' ' + form.clean()['finishtime']
#         post.SERVICE_DATE = str(post.START_DATETIME)[:10]
#
#         # 휴가등록
#         if post.SERVICE_TYPE == "휴가" and request.POST['status'] != 'form':
#             date = (date_list(post.START_DATETIME, post.FINISH_DATETIME))
#             for i in date:
#                 SERVICES.objects.create(SERVICE_DATE=i, DEPT_NAME=post.DEPT_NAME, EMP_NAME=name,
#                                         COMPANY_NAME=post.COMPANY_NAME, SERVICE_TYPE="휴가", START_DATETIME=i,
#                                         FINISH_DATETIME=i,HOUR=0, HOUR_EXCEPT_DISPATCH=0, MINUTE=0, OVER_HOUR=0,
#                                         OVER_MINUTE=0,REG_HOUR=0, REG_MINUTE=0, DETAILS=post.DETAILS,
#                                         SERVICE_STATUS="X", END_DATETIME=post.END_DATETIME)
#             return redirect('scheduler:scheduler_month')
#
#         # 기본
#         st = datetime.datetime(year=int(str(post.FINISH_DATETIME)[:4]),
#                                month=int(str(post.FINISH_DATETIME)[5:7]),
#                                day=int(str(post.FINISH_DATETIME)[8:10]),
#                                hour=int(str(post.FINISH_DATETIME)[11:13]),
#                                minute=int(str(post.FINISH_DATETIME)[14:16]), second=00) - \
#              datetime.datetime(year=int(str(post.START_DATETIME)[:4]), month=int(str(post.START_DATETIME)[5:7]),
#                                day=int(str(post.START_DATETIME)[8:10]),
#                                hour=int(str(post.START_DATETIME)[11:13]),
#                                minute=int(str(post.START_DATETIME)[14:16]), second=00)
#         post.HOUR = round(st.total_seconds() / 60 / 60, 1)
#         post.HOUR_EXCEPT_DISPATCH = post.HOUR
#         post.MINUTE = int(st.total_seconds() / 60)
#         post.OVER_MINUTE = int(overtime_sum(post.START_DATETIME, post.FINISH_DATETIME))
#         post.OVER_HOUR = round((post.OVER_MINUTE / 60), 1)
#         post.REG_HOUR = post.HOUR - post.OVER_HOUR
#         post.REG_MINUTE = post.MINUTE - post.OVER_MINUTE
#
#         # 기본등록(저장)
#         if request.POST['status'] == "save":
#             post.SERVICE_STATUS = 'N'
#             post.save()
#             return redirect('scheduler:scheduler_month')
#
#         # 기본등록(지원완료)
#         elif request.POST['status'] == "sign":
#             post.SERVICE_STATUS = 'Y'
#             post.save()
#             return redirect('mail:select', post.id)
#
#         # 새로운 양식 저장
#         elif request.POST['status'] == "form":
#             post.SERVICE_STATUS = 'F'
#             post.save()
#
#             form = PostForm()
#             try:
#                 myform = SERVICES.objects.filter(Q(SERVICE_STATUS='F') & Q(EMP_NAME=name))
#             except Exception as ex:
#                 myform = {}
#             type = 1
#             context = {'form': form,
#                        'name': name,
#                        "myform": myform,
#                        "type": type}
#             return render(request, 'usone/post.html', context)
#
#     # 새로운 양식 저장 화면(POST했을때 is_valid가 False이면 넘어가는 로직이므로, 칸을 채우고 새로운 양식 등록 누르면 오류)
#     else:
#         form = PostForm()
#         try:
#             myform = SERVICES.objects.filter(Q(SERVICE_STATUS='F') & Q(EMP_NAME=name))
#         except Exception as ex:
#             myform = {}
#         type = 1
#         context = {'form': form,
#                    'name': name,
#                    "myform": myform,
#                    "type": type}
#         return render(request, 'usone/post.html', context)
#
# # 일정등록화면
# else:
#     form = PostForm()
#     try:
#         myform = SERVICES.objects.filter(Q(SERVICE_STATUS='F')& Q(EMP_NAME=name))
#     except Exception as ex:
#         myform = {}
#     type = 0
#     context = {'form': form,
#                'name': name,
#                "myform":myform,
#                "type": type,
#                "postdate":postdate}
#     return render(request, 'usone/post.html', context)