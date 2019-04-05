from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.http import HttpResponse
from django.template import loader
import pandas as pd
from datetime import datetime, timedelta
import requests
from django.db.models import Q
from dateutil.relativedelta import relativedelta

from scheduler.models import Eventday
from service.models import Servicereport, Vacation
from django.contrib.auth.models import User
from django.http import QueryDict
from django.db.models import FloatField
from django.db.models import F, Sum, Count, Case, When

def dashboard(request):
    if request.user.id: #로그인 유무
        template = loader.get_template('dashboard/dashboard.html')

        #기간 설정 했을 경우
        if request.method=="POST":

            startdate=request.POST['startdate']
            enddate = request.POST['startdate']

        #default : 주 단위 (월~일)
        else:
            today = datetime.today()
            startdate = today - timedelta(days=today.weekday())
            enddate = startdate + timedelta(days=6)
            print(startdate.date(),enddate.date())

        ###고객사별 지원통계
        customer_support_time= Servicereport.objects.values('companyName')\
                                                    .filter(Q(serviceDate__gte=startdate)&
                                                            Q(serviceDate__lte=enddate)&
                                                            Q(empDeptName=request.user.employee.empDeptName))\
                                                    .annotate(sum_supportTime=Sum('serviceHour'))

        all_support_time = Servicereport.objects.filter(Q(serviceDate__gte=startdate) &
                                                        Q(serviceDate__lte=enddate) &
                                                        Q(empDeptName=request.user.employee.empDeptName))\
                                                .aggregate(Sum('serviceHour'),Count('serviceHour'))

        all_support_Overtime = Servicereport.objects.filter(Q(serviceDate__gte=startdate) &
                                                        Q(serviceDate__lte=enddate) &
                                                        Q(empDeptName=request.user.employee.empDeptName)) \
                                                    .aggregate(Sum('serviceOverHour'))

        ###엔지니어별 지원통계
        emp_support_time = Servicereport.objects.values('empName') \
            .filter(Q(serviceDate__gte=startdate) &
                    Q(serviceDate__lte=enddate) &
                    Q(empDeptName=request.user.employee.empDeptName)) \
            .annotate(sum_supportTime=Sum('serviceHour')).annotate(sum_supportCount=Count('empName')).annotate(sum_overTime=Sum('serviceOverHour'))

        ###타입별 지원통계
        type_support_time = Servicereport.objects.values('serviceType')\
            .filter(Q(serviceDate__gte=startdate) &
                    Q(serviceDate__lte=enddate) &
                    Q(empDeptName=request.user.employee.empDeptName)) \
            .annotate(sum_supportTime=Sum('serviceHour')).order_by('serviceType')

        type_count = [i for i in range(len(type_support_time))]
        multi_type = zip(type_support_time, type_count)

        context = {
            'customer_support_time': customer_support_time,
            'emp_support_time' : emp_support_time,
            'type_support_time' : type_support_time,
            'multi_type' : multi_type,
            'all_support_time' : all_support_time,
            'all_support_Overtime': all_support_Overtime
        }
        return HttpResponse(template.render(context, request))
    else:
        return redirect('login')
