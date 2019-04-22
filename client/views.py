# -*- coding: utf-8 -*-
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
import json
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
from .models import Company, Customer
from .forms import CompanyForm
from hr.models import Employee


def show_clientlist(request):
    if request.user.id:  # 로그인 유무
        template = loader.get_template('client/showclientlist.html')

        if request.method == "POST":
            companyName = request.POST["companyName"]
            empName = request.POST["empName"]
            chkbox = request.POST.getlist('chkbox')

            companylist = Company.objects.all()

            if 'present' in chkbox:
                companylist_present = companylist.filter(companyStatus='Y')
            else:
                companylist_present = companylist.filter(companyStatus='O')
            if 'past' in chkbox:
                companylist_past = companylist.filter(companyStatus='N')
            else:
                companylist_past = companylist.filter(companyStatus='O')
            if 'wait' in chkbox:
                companylist_wait = companylist.filter(companyStatus='X')
            else:
                companylist_wait = companylist.filter(companyStatus='O')

            companylist = companylist_present | companylist_past | companylist_wait

            if companyName:
                companylist = companylist.filter(companyName__icontains=companyName)

            if empName:
                empId = Employee.objects.get(empName=empName).empId
                companylist = companylist.filter(
                    Q(dbMainEmpId=empId) |
                    Q(dbSubEmpId=empId) |
                    Q(solutionMainEmpId=empId) |
                    Q(solutionSubEmpId=empId) |
                    Q(saleEmpId=empId)
                )

            context = {
                'companylist': companylist,
            }

        else:
            companylist = Company.objects.filter(companyStatus='Y')

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
            return redirect('client:show_clientlist')

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
        customers = Customer.objects.filter(companyName=companyName)
        try:
            dbms = json.loads(company.companyDbms)
        except:
            dbms = "{}"
        services = Servicereport.objects.filter(companyName=companyName)
        if request.method == 'POST':
            print(request.POST)
            try:
                company.dbComment = request.POST["dbtextArea"]
                company.save()
            except:
                company.solutionComment = request.POST["soltextArea"]
                company.save()

        context = {
            'company': company,
            'customers':customers,
            'dbms' : dbms,
            'services' : services,
        }
        return HttpResponse(template.render(context, request))

    else:
        return redirect('login')

def view_customer(request, customerId):
    userId = request.user.id  # 로그인 유무 판단 변수
    template = loader.get_template('client/viewcustomer.html')
    if userId:
        customer = Customer.objects.get(customerId=customerId)
        if request.method == 'POST':
            customer.customerName = request.POST["customerName"]
            customer.customerDeptName = request.POST["customerDept"]
            customer.customerEmail = request.POST["customerEmail"]
            customer.customerPhone = request.POST["customerPhone"]
            customer.save()

        context = {
            'customer': customer,
        }
        return HttpResponse(template.render(context, request))

    else:
        return redirect('login')
