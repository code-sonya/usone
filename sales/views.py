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
from .forms import ContractForm, GoalForm
from .models import Contract, Category, Revenue, Contractitem
from service.models import Company, Customer
from django.db.models import Q
from datetime import datetime, timedelta

@login_required
def post_contract(request):
    if request.method == "POST":
        form = ContractForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.empName = form.clean()['empId'].empName
            post.empDeptName = form.clean()['empId'].empDeptName
            if form.clean()['saleCustomerId']:
                post.saleCustomerName = form.clean()['saleCustomerId'].customerName
            else:
                post.saleCustomerName = ''
            post.save()

            jsonItem = json.loads(request.POST['jsonItem'])
            for item in jsonItem:
                Contractitem.objects.create(
                    contractId=post,
                    mainCategory=item["mainCategory"],
                    subCategory=item["subCategory"],
                    itemName=item["itemName"],
                    itemPrice=int(item["itemPrice"])
                )

            jsonRevenue = json.loads(request.POST['jsonRevenue'])
            for revenue in jsonRevenue:
                Revenue.objects.create(
                    contractId=post,
                    billingDate=revenue["billingDate"],
                    revenuePrice=int(revenue["revenuePrice"]),
                    revenueProfitPrice=int(revenue["revenueProfitPrice"]),
                    comment=revenue["revenueComment"],
                )
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

    else:
        startdate = ''
        enddate = ''
        contractStep = ''
        empDeptName = ''
        empName = ''
        saleCompanyName = ''
        endCompanyName = ''
        contractName = ''

    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'contractStep': contractStep,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'endCompanyName': endCompanyName,
        'contractName': contractName,
    }

    return render(request, 'sales/showcontracts.html', context)


@login_required
@csrf_exempt
def view_contract(request, contractId):
    contract = Contract.objects.get(contractId=contractId)
    items = Contractitem.objects.filter(contractId=contractId)
    revenues = Revenue.objects.filter(contractId=contractId)
    context = {
        'contract': contract,
        'items': items,
        'revenues': revenues,
    }
    return render(request, 'sales/viewcontract.html', context)


@login_required
def modify_contract(request, contractId):
    contractInstance = Contract.objects.get(contractId=contractId)

    if request.method == "POST":
        form = ContractForm(request.POST, instance=contractInstance)

        if form.is_valid():
            post = form.save(commit=False)
            post.empName = form.clean()['empId'].empName
            post.empDeptName = form.clean()['empId'].empDeptName
            if form.clean()['saleCustomerId']:
                post.saleCustomerName = form.clean()['saleCustomerId'].customerName
            else:
                post.saleCustomerName = ''
            post.save()

            jsonItem = json.loads(request.POST['jsonItem'])
            itemId = list(i[0] for i in Contractitem.objects.filter(contractId=contractId).values_list('contractItemId'))
            jsonItemId = []
            for item in jsonItem:
                if item['itemId'] == '추가':
                    Contractitem.objects.create(
                        contractId=post,
                        mainCategory=item["mainCategory"],
                        subCategory=item["subCategory"],
                        itemName=item["itemName"],
                        itemPrice=int(item["itemPrice"])
                    )
                else:
                    itemInstance = Contractitem.objects.get(contractItemId=int(item["itemId"]))
                    itemInstance.contractId = post
                    itemInstance.mainCategory = item["mainCategory"]
                    itemInstance.subCategory = item["subCategory"]
                    itemInstance.itemName = item["itemName"]
                    itemInstance.itemPrice = int(item["itemPrice"])
                    itemInstance.save()
                    jsonItemId.append(int(item['itemId']))

            delItemId = list(set(itemId) - set(jsonItemId))

            if delItemId:
                for Id in delItemId:
                    Contractitem.objects.filter(contractItemId=Id).delete()

            jsonRevenue = json.loads(request.POST['jsonRevenue'])
            print('jsonRevenue :', jsonRevenue)
            revenueId = list(i[0] for i in Revenue.objects.filter(contractId=contractId).values_list('revenueId'))
            jsonRevenueId = []
            for revenue in jsonRevenue:
                if revenue['revenueId'] == '추가':
                    Revenue.objects.create(
                        contractId=post,
                        billingDate=revenue["billingDate"],
                        revenuePrice=int(revenue["revenuePrice"]),
                        revenueProfitPrice=int(revenue["revenueProfitPrice"]),
                        comment=revenue["revenueComment"],
                    )
                else:
                    revenueInstance = Revenue.objects.get(revenueId=int(revenue["revenueId"]))
                    revenueInstance.contractId = post
                    revenueInstance.billingDate = revenue["billingDate"]
                    revenueInstance.salePrice = int(revenue["revenuePrice"])
                    revenueInstance.revenueProfitPrice = int(revenue["revenueProfitPrice"])
                    revenueInstance.comment = revenue["revenueComment"]
                    revenueInstance.save()
                    jsonRevenueId.append(int(revenue["revenueId"]))

            delRevenueId = list(set(revenueId) - set(jsonRevenueId))

            if delRevenueId:
                for Id in delRevenueId:
                    Revenue.objects.filter(revenueId=Id).delete()

            return redirect('sales:showcontracts')

    else:
        form = ContractForm(instance=contractInstance)
        items = Contractitem.objects.filter(contractId=contractId)
        revenues = Revenue.objects.filter(contractId=contractId)

        context = {
            'form': form,
            'items': items,
            'revenues': revenues,
        }
        return render(request, 'sales/postcontract.html', context)


@login_required
def show_revenues(request):
    context = {
    }

    return render(request, 'sales/showrevenues.html', context)


@login_required
@csrf_exempt
def view_revenue(request, revenueId):
    revenue = Revenue.objects.get(revenueId=revenueId)
    contract = Contract.objects.get(contractId=revenue.contractId.contractId)
    items = Contractitem.objects.filter(contractId=revenue.contractId.contractId)
    revenues = Revenue.objects.filter(contractId=revenue.contractId.contractId)

    context = {
        'revenue': revenue,
        'contract': contract,
        'items': items,
        'revenues': revenues,
    }
    return render(request, 'sales/viewrevenue.html', context)


@login_required
def delete_contract(request, contractId):
    Contract.objects.filter(contractId=contractId).delete()
    return redirect('sales:showcontracts')


@login_required
def delete_revenue(request, revenueId):
    Revenue.objects.filter(revenueId=revenueId).delete()
    return redirect('sales:showrevenues')


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
    if empDeptName == '전체':
        employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))
    else:
        employees = Employee.objects.filter(Q(empDeptName=empDeptName) & Q(empStatus='Y'))
    json = serializers.serialize('json', employees)
    return HttpResponse(json, content_type='application/json')


@login_required
@csrf_exempt
def category_asjson(request):
    mainCategory = request.POST['mainCategory']
    subcategory = Category.objects.filter(mainCategory=mainCategory)
    json = serializers.serialize('json', subcategory)
    return HttpResponse(json, content_type='application/json')


@login_required
@csrf_exempt
def contracts_asjson(request):
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
        contracts = contracts.filter(contractDate__gte=startdate)
    if enddate:
        contracts = contracts.filter(contractDate__lte=enddate)
    if contractStep != '전체' and contractStep != '':
        contracts = contracts.filter(contractStep=contractStep)
    if empDeptName != '전체' and empDeptName != '':
        contracts = contracts.filter(empDeptName=empDeptName)
    if empName != '전체' and empName != '':
        contracts = contracts.filter(empName=empName)
    if saleCompanyName:
        contracts = contracts.filter(saleCompanyName__in=saleCompanyName)
    if endCompanyName:
        contracts = contracts.filter(endCompanyName__in=endCompanyName)
    if contractName:
        contracts = contracts.filter(contractName__in=contractName)

    contracts = contracts.values('contractStep', 'empDeptName', 'empName', 'contractCode', 'contractName', 'saleCompanyName', 'contractDate', 'contractId')
    structure = json.dumps(list(contracts), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def revenues_asjson(request):
    revenues = Revenue.objects.all()
    revenues = revenues.values('billingDate', 'contractId__contractCode', 'contractId__contractName', 'contractId__saleCompanyName__companyName',
                               'revenuePrice', 'revenueProfitPrice', 'contractId__empName', 'contractId__empDeptName', 'revenueId')
    structure = json.dumps(list(revenues), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_goal(request):
    salesteam_lst = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    salesteam_lst = [x['empDeptName'] for x in salesteam_lst if "영업" in x['empDeptName']]
    today_year = datetime.today().year

    if request.method == "POST":
        form = GoalForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            print(post)
            if request.POST['empName'] == "전체":
                post.name = request.POST['empDeptName']
            else:
                post.name = request.POST['empName']

            post.q1 = post.jan + post.feb + post.mar
            post.q2 = post.apr + post.may + post.jun
            post.q3 = post.jul + post.aug + post.sep
            post.q4 = post.oct + post.nov + post.dec
            post.yearSum = post.q1 + post.q2 + post.q3 + post.q4
            post.save()

            return redirect('sales:showcontracts')

    else:
        form = GoalForm()
        context = {
            'form': form,
            'salesteam_lst':salesteam_lst,
            'today_year':today_year,
        }
        return render(request, 'sales/postgoal.html', context)
