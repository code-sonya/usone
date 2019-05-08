# -*- coding: utf-8 -*-
import json

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
from django.core.serializers.json import DjangoJSONEncoder

from hr.models import Employee
from .forms import OpportunityForm
from .models import Contract
from service.models import Company ,Customer
from django.db.models import Q


@login_required
def post_opportunity(request):

    if request.method == "POST":
        form = OpportunityForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.empName = form.clean()['empId'].empName
            post.empDeptName = form.clean()['empId'].empDeptName
            post.saleCustomerName = form.clean()['saleCustomerId'].customerName
            post.endCustomerName = form.clean()['endCustomerId'].customerName
            post.save()
            return redirect('service:showservices')

    else:
        form = OpportunityForm()
        context = {
            'form': form,
        }
        return render(request, 'sales/postopportunity.html', context)


@login_required
def show_contracts(request):
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))
    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        contractStep = request.POST["contractStep"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        endCompanyName = request.POST['endCompanyName']
        contractName = request.POST['contractName']

        context = {
            'employees': employees,
            'startdate' : startdate,
            'enddate': enddate,
            'contractStep':contractStep,
            'empDeptName':empDeptName,
            'empName' :empName,
            'saleCompanyName':saleCompanyName,
            'endCompanyName':endCompanyName,
            'contractName':contractName,
            'filter':'Y'
        }


    else:
        context = {
            'employees': employees,
            'filter': 'N'
        }

    return render(request, 'sales/showcontracts.html', context)


@login_required
def contract_asjson(request):
    Ocontracts = Contract.objects.filter(contractStep='Opportunity')\
        .values('contractStep', 'predictContractDate', 'contractName', 'saleCompanyName', 'endCompanyName', 'empName', 'contractId')
    Fcontracts = Contract.objects.filter(contractStep='Firm') \
        .values('contractStep', 'contractDate', 'contractName', 'saleCompanyName', 'endCompanyName', 'empName', 'contractId')
    contracts = []
    contracts.extend(list(Ocontracts))
    contracts.extend(list(Fcontracts))
    structure = json.dumps(contracts, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def salemanager_asjson(request):
    companyName = request.POST['saleCompanyName']
    customer = Customer.objects.filter(companyName=companyName)
    json = serializers.serialize('json', customer)
    return HttpResponse(json, content_type='application/json')


@login_required
@csrf_exempt
def empdept_asjson(request):
    empDeptName = request.POST['empDeptName']
    if empDeptName =='전체':
        employees = Employee.objects.filter(Q(empDeptName='영업1팀')|Q(empDeptName='영업2팀')|Q(empDeptName='영업3팀')&Q(empStatus='Y'))
    else:
        employees = Employee.objects.filter(Q(empDeptName=empDeptName)&Q(empStatus='Y'))
    json = serializers.serialize('json', employees)
    return HttpResponse(json, content_type='application/json')


@login_required
@csrf_exempt
def filter_asjson(request):
    startdate = request.POST["startdate"]
    enddate = request.POST["enddate"]
    contractStep = request.POST["contractStep"]
    empDeptName = request.POST['empDeptName']
    empName = request.POST['empName']
    saleCompanyName = request.POST['saleCompanyName']
    endCompanyName = request.POST['endCompanyName']
    contractName = request.POST['contractName']

    print(startdate,enddate,contractStep,empDeptName,empName,saleCompanyName,endCompanyName,contractName)


    Ocontracts = Contract.objects.filter(contractStep='Opportunity')
    Fcontracts = Contract.objects.filter(contractStep='Firm')

    if startdate:
        Ocontracts.filter(predictContractDate__gte=startdate)
        Fcontracts.filter(contractDate__gte=startdate)
    if enddate:
        Ocontracts.filter(predictContractDate__lte=enddate)
        Fcontracts.filter(contractDate__lte=enddate)
    if contractStep != '전체':
        Ocontracts.filter(contractStep=contractStep)
        Fcontracts.filter(contractStep=contractStep)
    if empDeptName != '전체':
        Ocontracts.filter(empDeptName=empDeptName)
        Fcontracts.filter(empDeptName=empDeptName)
    if empName != '전체':
        Ocontracts.filter(empName=empName)
        Fcontracts.filter(empName=empName)
    if saleCompanyName:
        Ocontracts.filter(saleCompanyName__in=saleCompanyName)
        Fcontracts.filter(saleCompanyName__in=saleCompanyName)
    if endCompanyName:
        Ocontracts.filter(endCompanyName__in=endCompanyName)
        Fcontracts.filter(endCompanyName__in=endCompanyName)
    if contractName:
        Ocontracts.filter(contractName__in=contractName)
        Fcontracts.filter(contractName__in=contractName)


    Ocontracts.values('contractStep', 'predictContractDate', 'contractName', 'saleCompanyName', 'endCompanyName', 'empName', 'contractId')
    Fcontracts.values('contractStep', 'contractDate', 'contractName', 'saleCompanyName', 'endCompanyName', 'empName', 'contractId')


    contracts = []
    contracts.extend(list(Ocontracts))
    contracts.extend(list(Fcontracts))
    print(contracts)
    structure = json.dumps(contracts, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')
