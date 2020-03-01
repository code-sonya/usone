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
        'serviceId', 'serviceDate', 'empName', 'empDeptName',
        'serviceType__typeName', 'serviceHour', 'serviceOverHour', 'serviceTitle'
    )
    structure = json.dumps(list(services), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def filter_asjson(request):
    companylist = Company.objects.all()

    companylist = companylist.values(
        'companyName', 'ceo', 'companyNumber', 'companyAddress', 'companyPhone', 'companyType',
    )
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
        form = CompanyForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.companyNameKo = form.clean()['companyName']
            post.save()
        return redirect('client:show_clientlist')

    else:
        form = CompanyForm()
        context = {
            'form': form,
        }
        return HttpResponse(template.render(context, request))


@login_required
def modify_client(request, companyName):
    template = loader.get_template('client/postclient.html')
    company = Company.objects.get(companyName=companyName)

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            post = form.save(commit=False)
            post.companyNameKo = form.clean()['companyName']
            post.save()
        return redirect('client:view_client', companyName)

    else:
        form = CompanyForm(instance=company)
        context = {
            'form': form,
        }
        return HttpResponse(template.render(context, request))


@login_required
def view_client(request, companyName):
    template = loader.get_template('client/viewclient.html')
    company = Company.objects.get(companyName=companyName)
    customers = Customer.objects.filter(companyName=companyName)
    contracts = Contract.objects.filter(saleCompanyName=companyName)

    context = {
        'company': company,
        'customers': customers,
        'contracts': contracts,
    }
    return HttpResponse(template.render(context, request))


@login_required
def delete_client(request, companyName):
    company = Company.objects.get(companyName=companyName)
    company.delete()
    return redirect('client:show_clientlist')


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
def check_company(request):
    companyName = request.POST['companyName']
    if Company.objects.filter(companyName=companyName):
        result = 'N'
    else:
        result = 'Y'
    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')
