from django.shortcuts import render

# Create your views here.
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
from .models import Company ,Customer
from .forms import CompanyForm
from hr.models import Employee

def show_clientlist(request):
    if request.user.id:  # 로그인 유무
        template = loader.get_template('client/showclientlist.html')

        if request.method == "POST":
            print(request.POST)
            companyName = request.POST["companyName"]
            empName = request.POST["empName"]
            emp = Employee.objects.get(empName=empName)
            empId = emp.empId

            companylist = Company.objects.all()
            if companyName :
                companylist = companylist.filter(companyName__icontains=companyName)

            if empName :
                companylist = companylist.filter(Q(dbMainEmpId=empId)|
                                                 Q(dbSubEmpId=empId)|
                                                 Q(solutionMainEmpId=empId)|
                                                 Q(solutionSubEmpId=empId)|
                                                 Q(saleEmpId=empId))

            context = {
                'companylist' : companylist,
            }

        else:
            companylist = Company.objects.all()

            context = {
                'companylist': companylist,
            }

        return HttpResponse(template.render(context, request))

    else:
        return redirect('login')


def post_client(request):
    userId = request.user.id  # 로그인 유무 판단 변수
    template = loader.get_template('client/postclient.html')

    if userId:

        if request.method == "POST":
            form = CompanyForm(request.POST)
            post = form.save(commit=False)
            post.companyStatus = 'X'
            post.save()
            return redirect('show_clientlist')

        else:
            form = CompanyForm()
            context = {
                'form': form,
            }
            return HttpResponse(template.render(context, request))

    else:
        return redirect('login')

def view_client(request, companyName):
    userId = request.user.id  # 로그인 유무 판단 변수
    template = loader.get_template('client/viewclient.html')
    if userId:
        company = Company.objects.get(companyName=companyName)

        context = {
            'company': company,
        }
        return HttpResponse(template.render(context, request))

    else:
        return redirect('login')

