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
from django.db.models import Sum



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

        customer_support_time= Servicereport.objects.values('companyName')\
                                                    .filter(Q(serviceDate__gte=startdate)&
                                                            Q(serviceDate__lte=enddate)&
                                                            Q(empDeptName=request.user.employee.empDeptName))\
                                                    .annotate(sum_supportTime=Sum('serviceHour'))

        context = {
            'customer_support_time': customer_support_time,
        }
        return HttpResponse(template.render(context, request))
    else:
        return redirect('login')
