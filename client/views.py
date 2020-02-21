# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, redirect
import json
from django.http import HttpResponse
from django.template import loader
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from service.models import Servicereport
from sales.models import Contract
from .models import Company, Customer
from .forms import CompanyForm, CustomerForm
from hr.models import Employee

import datetime


@login_required
@csrf_exempt
def service_asjson(request):
    companyName = request.POST['companyName']
    services = Servicereport.objects.filter(companyName=companyName).values(
        'serviceId', 'serviceDate', 'empName', 'empDeptName', 'serviceType__typeName', 'serviceHour', 'serviceOverHour', 'serviceTitle'
    )
    structure = json.dumps(list(services), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def filter_asjson(request):
    companyName = request.POST["companyName"]
    empName = request.POST["empName"]

    companylist = Company.objects.filter(companyStatus='Y')

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

    companylist = companylist.values('companyName', 'companyNameKo', 'saleEmpId__empName', 'ceo', 'companyNumber', 'companyAddress',)
    structure = json.dumps(list(companylist), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def show_clientlist(request):
    template = loader.get_template('client/showclientlist.html')

    if request.method == "POST":
        companyName = request.POST["companyName"]
        empName = request.POST["empName"]
        chkbox = request.POST.getlist('chkbox')

        context = {
            'filter': "Y",
            'companyName': companyName,
            'empName': empName,
            'chkbox': chkbox
        }

    else:
        context = {
            'filter': 'N',
        }

    return HttpResponse(template.render(context, request))


@login_required
def post_client(request):
    template = loader.get_template('client/postclient.html')
    if request.method == "POST":
        try:
            form = CompanyForm(request.POST)
            post = form.save(commit=False)
            post.companyStatus = 'Y'
            post.save()
            return redirect('client:show_clientlist')
        except:
            return HttpResponse("이미 등록된 고객사입니다. 고객사 영문명은 중복될 수 없습니다.")


    else:
        form = CompanyForm()
        context = {
            'form': form,
        }
        return HttpResponse(template.render(context, request))


@login_required
def modify_client(request, companyName):
    template = loader.get_template('client/postclient.html')
    companyInstance = Company.objects.get(companyName=companyName)
    if request.method == "POST":
        form = CompanyForm(request.POST, instance=companyInstance)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()

            return redirect('client:view_client', companyName)

    else:
        form = CompanyForm(instance=companyInstance)
        context = {
            'form': form,
            'modify': 'N'
        }
        return HttpResponse(template.render(context, request))




@login_required
def view_client(request, companyName):
    template = loader.get_template('client/viewclient.html')
    company = Company.objects.get(companyName=companyName)
    customers = Customer.objects.filter(companyName=companyName)
    contracts = Contract.objects.filter(
        Q(endCompanyName=companyName) & Q(contractStartDate__lte=datetime.datetime.today()) & Q(contractEndDate__gte=datetime.datetime.today())
    )

    try:
        dbms = json.loads(company.companyDbms)
    except:
        dbms = "{}"

    if request.method == 'POST':
        try:
            company.dbComment = request.POST["dbtextArea"]
            company.save()
        except:
            company.solutionComment = request.POST["soltextArea"]
            company.save()

    context = {
        'company': company,
        'customers': customers,
        'contracts': contracts,
        'dbms': dbms,
    }
    return HttpResponse(template.render(context, request))


@login_required
def view_customer(request, customerId):
    template = loader.get_template('client/viewcustomer.html')
    customer = Customer.objects.get(customerId=customerId)
    if request.method == 'POST':
        customer.customerName = request.POST["customerName"]
        customer.customerDeptName = request.POST["customerDept"]
        customer.customerEmail = request.POST["customerEmail"]
        customer.customerPhone = request.POST["customerPhone"]
        customer.save()
        return redirect('client:view_client', customer.companyName)

    context = {
        'customer': customer,
    }
    return HttpResponse(template.render(context, request))


@login_required
def delete_customer(request, customerId):
    customer = Customer.objects.filter(customerId=customerId).first()
    companyName = customer.companyName
    customer.delete()
    return redirect('client:view_client', companyName)


@login_required
def post_customer(request, companyName):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('client:view_client', companyName)

    else:
        form = CustomerForm()
        context = {
            'form': form,
            'companyName': companyName
        }
        return render(request, 'client/postcustomer.html', context)


@login_required
def delete_client(request, companyName):
    company = Company.objects.filter(companyName=companyName).first()
    company.delete()
    return redirect('client:show_clientlist')