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
from .forms import ContractForm
from .models import Contract ,Category
from service.models import Company ,Customer
from django.db.models import Q


@login_required
def post_contract(request):

    if request.method == "POST":
        form = ContractForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.empName = form.clean()['empId'].empName
            post.empDeptName = form.clean()['empId'].empDeptName
            post.saleCustomerName = form.clean()['saleCustomerId'].customerName
            post.endCustomerName = form.clean()['endCustomerId'].customerName
            post.save()
            return redirect('sales:showcontracts')

    else:
        form = ContractForm()
        context = {
            'form': form,
        }
        return render(request, 'sales/postcontract.html', context)


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
    contracts = Contract.objects.all()
    contracts = contracts.values('contractStep', 'predictContractDate', 'contractDate', 'contractName', 'saleCompanyName', 'endCompanyName', 'empName', 'contractId')
    structure = json.dumps(list(contracts), cls=DjangoJSONEncoder)
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
def view_contract(request, contractId):
    contract = Contract.objects.get(contractId=contractId)
    context = {
        'contract': contract,
    }
    if contract.contractStep == "Opportunity":
        return render(request, 'sales/viewopportunity.html', context)
    elif contract.contractStep == "Firm":
        return render(request, 'sales/viewfirm.html', context)

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

    contracts = Contract.objects.all()

    if startdate:
        contracts = contracts.filter(Q(predictContractDate__gte = startdate)|Q(contractDate__gte=startdate))
    if enddate:
        contracts = contracts.filter(Q(predictContractDate__lte=enddate)|Q(contractDate__lte=enddate))
    if contractStep != '전체':
        contracts = contracts.filter(contractStep=contractStep)
    if empDeptName != '전체':
        contracts = contracts.filter(empDeptName=empDeptName)
    if empName != '전체':
        contracts = contracts.filter(empName=empName)
    if saleCompanyName:
        contracts = contracts.filter(saleCompanyName__in=saleCompanyName)
    if endCompanyName:
        contracts = contracts.filter(endCompanyName__in=endCompanyName)
    if contractName:
        contracts = contracts.filter(contractName__in=contractName)

    contracts = contracts.values('contractStep', 'predictContractDate', 'contractDate', 'contractName', 'saleCompanyName', 'endCompanyName', 'empName', 'contractId')
    structure = json.dumps(list(contracts), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')

@login_required
@csrf_exempt
def category_asjson(request):
    mainCategory = request.POST['mainCategory']
    subcategory = Category.objects.filter(mainCategory=mainCategory)
    json = serializers.serialize('json', subcategory)
    return HttpResponse(json, content_type='application/json')

