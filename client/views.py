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
from .models import Company, Customer
from .forms import CompanyForm, CustomerForm
from hr.models import Employee
from django.core import serializers


@login_required
@csrf_exempt
def client_asjson(request):
    companyName = request.POST['companyName']
    services = Servicereport.objects.filter(companyName=companyName)
    json = serializers.serialize('json', services)
    return HttpResponse(json, content_type='application/json')


@login_required
@csrf_exempt
def list_asjson(request):
    companylist = Company.objects.filter(companyStatus='Y')
    companylist = companylist.values('companyName', 'saleEmpId__empName', 'dbMainEmpId__empName', 'dbSubEmpId__empName', 'solutionMainEmpId__empName',
                                     'solutionSubEmpId__empName', 'dbContractEndDate', 'solutionContractEndDate')
    structure = json.dumps(list(companylist), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def filter_asjson(request):
    companyName = request.POST["companyName"]
    empName = request.POST["empName"]
    chkbox = request.POST["chkbox"]

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

    companylist = companylist.values('companyName', 'saleEmpId__empName', 'dbMainEmpId__empName', 'dbSubEmpId__empName', 'solutionMainEmpId__empName',
                                     'solutionSubEmpId__empName', 'dbContractEndDate', 'solutionContractEndDate')
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


@login_required
def view_client(request, companyName):
    template = loader.get_template('client/viewclient.html')
    company = Company.objects.get(companyName=companyName)
    customers = Customer.objects.filter(companyName=companyName)
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
            'companyName':companyName
        }
        return render(request, 'client/postcustomer.html', context)

