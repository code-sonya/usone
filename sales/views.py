# -*- coding: utf-8 -*-
import json

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Sum, FloatField, F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import Coalesce
from hr.models import Employee
from .forms import ContractForm, GoalForm, PurchaseForm
from .models import Contract, Category, Revenue, Contractitem, Goal, Purchase
from .functions import viewContract
from service.models import Company, Customer
from django.db.models import Q
from datetime import datetime, timedelta
import pandas as pd
from xhtml2pdf import pisa
from service.functions import link_callback


@login_required
def post_contract(request):
    if request.method == "POST":
        form = ContractForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.empName = form.clean()['empId'].empName
            post.empDeptName = form.clean()['empId'].empDeptName
            post.saleCompanyName = Company.objects.filter(companyName=form.clean()['saleCompanyNames']).first()
            post.endCompanyName = Company.objects.filter(companyName=form.clean()['endCompanyNames']).first()
            if form.clean()['saleCustomerId']:
                post.saleCustomerName = form.clean()['saleCustomerId'].customerName
            else:
                post.saleCustomerName = ''
            post.mainCategory = json.loads(request.POST['jsonItem'])[0]['mainCategory']
            post.subCategory = json.loads(request.POST['jsonItem'])[0]['subCategory']
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
            jsonRevenue = sorted(jsonRevenue, key=lambda x: x['predictBillingDate'])
            idx = 0
            for revenue in jsonRevenue:
                idx += 1
                Revenue.objects.create(
                    contractId=post,
                    billingTime=str(idx) + '/' + str(len(jsonRevenue)),
                    predictBillingDate=revenue["billingDate"] or revenue["predictBillingDate"] + '-01' or None,
                    billingDate=revenue["billingDate"] or None,
                    predictDepositDate=revenue["predictDepositDate"] or None,
                    depositDate=revenue["depositDate"] or None,
                    revenueCompany=Company.objects.filter(companyName=revenue["revenueCompany"]).first(),
                    revenuePrice=int(revenue["revenuePrice"]),
                    revenueProfitPrice=int(revenue["revenueProfitPrice"]),
                    revenueProfitRatio=round((int(revenue["revenueProfitPrice"]) / int(revenue["revenuePrice"]) * 100)),
                    comment=revenue["revenueComment"],
                )

            jsonPurchase = json.loads(request.POST['jsonPurchase'])
            for purchase in jsonPurchase:
                Purchase.objects.create(
                    contractId=post,
                    billingTime=None,
                    predictBillingDate=purchase["purchaseDate"] or purchase["predictPurchaseDate"] + '-01' or None,
                    billingDate=purchase["purchaseDate"] or None,
                    predictWithdrawDate=purchase["predictWithdrawDate"] or None,
                    withdrawDate=purchase["withdrawDate"] or None,
                    purchaseCompany=Company.objects.filter(companyName=purchase["purchaseCompany"]).first(),
                    purchasePrice=int(purchase["purchasePrice"]),
                    comment=purchase["purchaseComment"],
                )
            return redirect('sales:showcontracts')

    else:
        form = ContractForm()
        companyList = Company.objects.filter(Q(companyStatus='Y'))
        companyNames = []
        for company in companyList:
            temp = {'id': company.pk, 'value': company.companyName}
            companyNames.append(temp)
        context = {
            'form': form,
            'companyNames': companyNames,
        }
        return render(request, 'sales/postcontract.html', context)


@login_required
def show_contracts(request):
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))
    salesteam_lst = Employee.objects.values('empDeptName').distinct()
    salesteam_lst = [x['empDeptName'] for x in salesteam_lst if "영업" in x['empDeptName']]

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
        'salesteam_lst': salesteam_lst,
    }

    return render(request, 'sales/showcontracts.html', context)


@login_required
@csrf_exempt
def view_contract(request, contractId):
    context = viewContract(contractId)
    return render(request, 'sales/viewcontract.html', context)


@login_required
def modify_contract(request, contractId):
    contractInstance = Contract.objects.get(contractId=contractId)

    if request.method == "POST":
        form = ContractForm(request.POST, request.FILES, instance=contractInstance)

        if form.is_valid():
            post = form.save(commit=False)
            post.empName = form.clean()['empId'].empName
            post.empDeptName = form.clean()['empId'].empDeptName
            post.saleCompanyName = Company.objects.filter(companyName=form.clean()['saleCompanyNames']).first()
            post.endCompanyName = Company.objects.filter(companyName=form.clean()['endCompanyNames']).first()
            if form.clean()['saleCustomerId']:
                post.saleCustomerName = form.clean()['saleCustomerId'].customerName
            else:
                post.saleCustomerName = ''
            post.mainCategory = json.loads(request.POST['jsonItem'])[0]['mainCategory']
            post.subCategory = json.loads(request.POST['jsonItem'])[0]['subCategory']
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
            jsonRevenue = sorted(jsonRevenue, key=lambda x: x['predictBillingDate'])
            idx = 0
            revenueId = list(i[0] for i in Revenue.objects.filter(contractId=contractId).values_list('revenueId'))
            jsonRevenueId = []
            for revenue in jsonRevenue:
                idx += 1
                if revenue['revenueId'] == '추가':
                    Revenue.objects.create(
                        contractId=post,
                        billingTime=str(idx) + '/' + str(len(jsonRevenue)),
                        predictBillingDate=revenue["billingDate"] or revenue["predictBillingDate"] + '-01' or None,
                        billingDate=revenue["billingDate"] or None,
                        predictDepositDate=revenue["predictDepositDate"] or None,
                        depositDate=revenue["depositDate"] or None,
                        revenueCompany=Company.objects.filter(companyName=revenue["revenueCompany"]).first(),
                        revenuePrice=int(revenue["revenuePrice"]),
                        revenueProfitPrice=int(revenue["revenueProfitPrice"]),
                        revenueProfitRatio=round((int(revenue["revenueProfitPrice"]) / int(revenue["revenuePrice"]) * 100)),
                        comment=revenue["revenueComment"],
                    )
                else:
                    revenueInstance = Revenue.objects.get(revenueId=int(revenue["revenueId"]))
                    revenueInstance.contractId = post
                    revenueInstance.billingTime = str(idx) + '/' + str(len(jsonRevenue))
                    revenueInstance.predictBillingDate = revenue["billingDate"] or revenue["predictBillingDate"] + '-01' or None
                    revenueInstance.billingDate = revenue["billingDate"] or None
                    revenueInstance.predictDepositDate = revenue["predictDepositDate"] or None
                    revenueInstance.depositDate = revenue["depositDate"] or None
                    revenueInstance.revenueCompany = Company.objects.filter(companyName=revenue["revenueCompany"]).first()
                    revenueInstance.revenuePrice = int(revenue["revenuePrice"])
                    revenueInstance.revenueProfitPrice = int(revenue["revenueProfitPrice"])
                    revenueInstance.revenueProfitRatio = round((int(revenue["revenueProfitPrice"]) / int(revenue["revenuePrice"]) * 100))
                    revenueInstance.comment = revenue["revenueComment"]
                    revenueInstance.save()
                    jsonRevenueId.append(int(revenue["revenueId"]))

            delRevenueId = list(set(revenueId) - set(jsonRevenueId))

            if delRevenueId:
                for Id in delRevenueId:
                    Revenue.objects.filter(revenueId=Id).delete()

            jsonPurchase = json.loads(request.POST['jsonPurchase'])
            purchaseId = list(i[0] for i in Purchase.objects.filter(contractId=contractId).values_list('purchaseId'))
            jsonPurchaseId = []
            for purchase in jsonPurchase:
                if purchase['purchaseId'] == '추가':
                    Purchase.objects.create(
                        contractId=post,
                        billingTime=None,
                        predictBillingDate=purchase["purchaseDate"] or purchase["predictPurchaseDate"] + '-01' or None,
                        billingDate=purchase["purchaseDate"] or None,
                        predictWithdrawDate=purchase["predictWithdrawDate"] or None,
                        withdrawDate=purchase["withdrawDate"] or None,
                        purchaseCompany=Company.objects.filter(companyName=purchase["purchaseCompany"]).first(),
                        purchasePrice=int(purchase["purchasePrice"]),
                        comment=purchase["purchaseComment"],
                    )
                else:
                    purchaseInstance = Purchase.objects.get(purchaseId=int(purchase["purchaseId"]))
                    purchaseInstance.contractId = post
                    purchaseInstance.billingTime = None
                    purchaseInstance.predictBillingDate = purchase["purchaseDate"] or purchase["predictPurchaseDate"] + '-01' or None
                    purchaseInstance.billingDate = purchase["purchaseDate"] or None
                    purchaseInstance.predictWithdrawDate = purchase["predictWithdrawDate"] or None
                    purchaseInstance.withdrawDate = purchase["withdrawDate"] or None
                    purchaseInstance.purchaseCompany = Company.objects.filter(companyName=purchase["purchaseCompany"]).first()
                    purchaseInstance.purchasePrice = int(purchase["purchasePrice"])
                    purchaseInstance.comment = purchase["purchaseComment"]
                    purchaseInstance.save()
                    jsonPurchaseId.append(int(purchase["purchaseId"]))

            delPurchaseId = list(set(purchaseId) - set(jsonPurchaseId))

            if delPurchaseId:
                for Id in delPurchaseId:
                    Purchase.objects.filter(purchaseId=Id).delete()

            return redirect('sales:viewcontract', str(contractId))

    else:
        form = ContractForm(instance=contractInstance)
        items = Contractitem.objects.filter(contractId=contractId)
        revenues = Revenue.objects.filter(contractId=contractId)
        purchases = Purchase.objects.filter(contractId=contractId)
        saleCompanyNames = Contract.objects.get(contractId=contractId).saleCompanyName
        endCompanyNames = Contract.objects.get(contractId=contractId).endCompanyName
        contractPaper = str(form.save(commit=False).contractPaper).split('/')[-1]
        orderPaper = str(form.save(commit=False).orderPaper).split('/')[-1]

        companyList = Company.objects.filter(Q(companyStatus='Y'))
        companyNames = []
        for company in companyList:
            temp = {'id': company.pk, 'value': company.companyName}
            companyNames.append(temp)

        context = {
            'form': form,
            'items': items,
            'revenues': revenues.order_by('predictBillingDate'),
            'purchases': purchases.order_by('predictBillingDate'),
            'saleCompanyNames': saleCompanyNames,
            'endCompanyNames': endCompanyNames,
            'contractPaper': contractPaper,
            'orderPaper': orderPaper,
            'companyNames': companyNames
        }
        return render(request, 'sales/postcontract.html', context)


@login_required
def show_revenues(request):
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        contractName = request.POST['contractName']
        contractStep = request.POST['contractStep']
        modifyMode = request.POST['modifyMode']

    else:
        startdate = ''
        enddate = ''
        empDeptName = ''
        empName = ''
        saleCompanyName = ''
        contractName = ''
        contractStep = ''
        modifyMode = 'N'

    outstandingcollection = 'N'
    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'outstandingcollection': outstandingcollection,
        'modifyMode': modifyMode,
    }

    return render(request, 'sales/showrevenues.html', context)


@login_required
@csrf_exempt
def view_revenue(request, revenueId):
    revenue = Revenue.objects.get(revenueId=revenueId)
    contractId = revenue.contractId.contractId

    context = viewContract(contractId)
    context['revenueId'] = int(revenueId)
    return render(request, 'sales/viewcontract.html', context)


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
        # employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀'))
    else:
        employees = Employee.objects.filter(Q(empDeptName=empDeptName) & Q(empStatus='Y'))
        # employees = Employee.objects.filter(Q(empDeptName=empDeptName))
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
        contracts = contracts.filter(saleCompanyName__companyName__icontains=saleCompanyName)
    if endCompanyName:
        contracts = contracts.filter(endCompanyName__companyName__icontains=endCompanyName)
    if contractName:
        contracts = contracts.filter(contractName__contains=contractName)

    contracts = contracts.values('contractStep', 'empDeptName', 'empName', 'contractCode', 'contractName', 'saleCompanyName', 'endCompanyName', 'contractDate', 'contractId', 'salePrice',
                                 'profitPrice')
    structure = json.dumps(list(contracts), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def revenues_asjson(request):
    startdate = request.POST["startdate"]
    enddate = request.POST["enddate"]
    empDeptName = request.POST['empDeptName']
    empName = request.POST['empName']
    saleCompanyName = request.POST['saleCompanyName']
    contractName = request.POST['contractName']
    contractStep = request.POST['contractStep']
    outstandingcollection = request.POST['outstandingcollection']

    if outstandingcollection == 'Y':
        revenues = Revenue.objects.filter(Q(billingDate__isnull=False) & Q(depositDate__isnull=True))
    elif outstandingcollection == 'N':
        revenues = Revenue.objects.all()

    if startdate:
        revenues = revenues.filter(Q(predictBillingDate__gte=startdate) or Q(predictDepositDate__gte=startdate))
    if enddate:
        revenues = revenues.filter(Q(predictBillingDate__lte=enddate) or Q(predictDepositDate__lte=enddate))
    if empDeptName != '전체' and empDeptName != '':
        revenues = revenues.filter(contractId__empDeptName=empDeptName)
    if empName != '전체' and empName != '':
        revenues = revenues.filter(contractId__empName=empName)
    if saleCompanyName:
        revenues = revenues.filter(contractId__saleCompanyName__companyName__icontains=saleCompanyName)
    if contractName:
        revenues = revenues.filter(contractId__contractName__contains=contractName)
    if contractStep != '전체' and contractStep != '':
        revenues = revenues.filter(contractId__contractStep=contractStep)

    revenues = revenues.values('billingDate', 'contractId__contractCode', 'contractId__contractName', 'contractId__saleCompanyName__companyName', 'revenuePrice', 'revenueProfitPrice',
                               'contractId__empName', 'contractId__empDeptName', 'revenueId', 'predictBillingDate', 'predictDepositDate', 'depositDate', 'contractId__contractStep',
                               'contractId__depositCondition', 'contractId__depositConditionDay', 'comment')
    structure = json.dumps(list(revenues), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_goal(request):
    salesteam_lst = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    salesteam_lst = [x['empDeptName'] for x in salesteam_lst if "영업" or "경영" in x['empDeptName']]
    today_year = datetime.today().year

    if request.method == "POST":
        form = GoalForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            if request.POST["empName"] != '전체':
                post.empName = Employee.objects.filter(pk=request.POST["empName"]).first().empName

            post.salesq1 = post.sales1 + post.sales2 + post.sales3
            post.salesq2 = post.sales4 + post.sales5 + post.sales6
            post.salesq3 = post.sales7 + post.sales8 + post.sales9
            post.salesq4 = post.sales10 + post.sales11 + post.sales12
            post.yearSalesSum = post.salesq1 + post.salesq2 + post.salesq3 + post.salesq4
            post.profitq1 = post.profit1 + post.profit2 + post.profit3
            post.profitq2 = post.profit4 + post.profit5 + post.profit6
            post.profitq3 = post.profit7 + post.profit8 + post.profit9
            post.profitq4 = post.profit10 + post.profit11 + post.profit12
            post.yearProfitSum = post.profitq1 + post.profitq2 + post.profitq3 + post.profitq4
            post.save()

            return redirect('sales:showgoals')

    else:
        form = GoalForm()
        context = {
            'form': form,
            'salesteam_lst': salesteam_lst,
            'today_year': today_year,
        }
        return render(request, 'sales/postgoal.html', context)


@login_required
def show_goals(request):
    salesteam_lst = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    salesteam_lst = [x['empDeptName'] for x in salesteam_lst if "영업" in x['empDeptName']]
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))
    today_year = datetime.today().year

    if request.method == "POST":
        year = request.POST["year"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']

    else:
        year = ''
        empDeptName = ''
        empName = ''

    context = {
        'employees': employees,
        'year': year,
        'empDeptName': empDeptName,
        'empName': empName,
        'today_year': today_year,
        'salesteam_lst': salesteam_lst,
    }

    return render(request, 'sales/showgoals.html', context)


@login_required
@csrf_exempt
def goals_asjson(request):
    year = request.POST["year"]
    empDeptName = request.POST['empDeptName']
    empName = request.POST['empName']

    goal = Goal.objects.all()

    if year:
        goal = goal.filter(year=year)
    if empDeptName:
        goal = goal.filter(empDeptName=empDeptName)
    if empName:
        goal = goal.filter(empName=empName)

    goal = goal.values('year', 'empDeptName', 'empName', 'salesq1', 'salesq2', 'salesq3', 'salesq4', 'yearSalesSum', 'goalId')
    structure = json.dumps(list(goal), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_goal(request, goalId):
    goal = Goal.objects.get(goalId=goalId)

    context = {
        'goalId': int(goalId),
        'goal': goal,
    }
    return render(request, 'sales/viewgoal.html', context)


@login_required
def modify_goal(request, goalId):
    goalinstance = Goal.objects.get(goalId=goalId)
    salesteam_lst = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    salesteam_lst = [x['empDeptName'] for x in salesteam_lst if "영업" in x['empDeptName']]

    if request.method == "POST":
        form = GoalForm(request.POST, instance=goalinstance)

        if form.is_valid():
            post = form.save(commit=False)
            if request.POST["empName"] != '전체':
                post.empName = Employee.objects.filter(pk=request.POST["empName"]).first().empName
            post.salesq1 = post.sales1 + post.sales2 + post.sales3
            post.salesq2 = post.sales4 + post.sales5 + post.sales6
            post.salesq3 = post.sales7 + post.sales8 + post.sales9
            post.salesq4 = post.sales10 + post.sales11 + post.sales12
            post.yearSalesSum = post.salesq1 + post.salesq2 + post.salesq3 + post.salesq4
            post.profitq1 = post.profit1 + post.profit2 + post.profit3
            post.profitq2 = post.profit4 + post.profit5 + post.profit6
            post.profitq3 = post.profit7 + post.profit8 + post.profit9
            post.profitq4 = post.profit10 + post.profit11 + post.profit12
            post.yearProfitSum = post.profitq1 + post.profitq2 + post.profitq3 + post.profitq4
            post.save()
            return redirect('sales:showgoals')

    else:
        form = GoalForm(instance=goalinstance)

        context = {
            'form': form,
            'today_year': goalinstance.year,
            'salesteam_lst': salesteam_lst,
            'empDeptName': goalinstance.empDeptName,
            'empName': goalinstance.empName,
        }
        return render(request, 'sales/postgoal.html', context)


@login_required
def delete_goal(request, goalId):
    Goal.objects.filter(goalId=goalId).delete()
    return redirect('sales:showgoals')


@login_required
def upload_purchase(request):
    context = {
    }
    return render(request, 'sales/uploadpurchase.html', context)


@login_required
def upload_csv(request):
    if "GET" == request.method:
        pass
    try:
        csv_file = request.FILES["csv_file"]
        xl_file = pd.ExcelFile(csv_file)
        data = pd.read_excel(xl_file, skiprows=[0, 1, 2])
        datalen = len(data)
        col = data.columns
        col_lst = [col[1], col[5], col[7], col[8], col[9], col[10], col[11], col[12]]
        df = data[col_lst]
        dfhead = df[:1]
        df = df.rename(columns={'관리\n번호': 'col0', '회차': 'col1', '총매출액': 'col2', '수금일': 'col3', '매입일': 'col4', '업체명': 'col5', '매입금액': 'col6', '지급일': 'col7'})
        ### 전처리
        df = df.fillna('-')
        df = df[df.col1 != '-']
        df = df[df.col0 != '-']
        companylst = list(Company.objects.all().values('companyNameKo'))
        df['check'] = df.apply(lambda x: 'Y' if {'companyNameKo': x.col5} in companylst else 'N', axis=1)
        dfTrue = df[df.check == 'Y']
        dfFalse = df[df.check == 'N']

        dfbody = []
        for index, rows in dfTrue.iterrows():
            my_dict = {"col0": rows[0], "col1": rows[1], "col2": rows[2], "col3": rows[3], "col4": rows[4], "col5": rows[5], "col6": rows[6], "col7": rows[7]}
            dfbody.append(my_dict)

        dfbodyFalse = []
        for index, rows in dfFalse.iterrows():
            my_dict = {"col0": rows[0], "col1": rows[1], "col2": rows[2], "col3": rows[3], "col4": rows[4], "col5": rows[5], "col6": rows[6], "col7": rows[7]}
            dfbodyFalse.append(my_dict)

    except Exception as e:
        print(e)

    context = {
        "dfhead": dfhead,
        "dfbody": dfbody,
        "dfbodyFalse": dfbodyFalse,
        "datalen": datalen - 1
    }

    return render(request, 'sales/uploadpurchase.html', context)


@login_required
@csrf_exempt
def save_purchase(request):
    if "POST" == request.method:
        controlNumber = request.POST.getlist('controlNumber')
        batch = request.POST.getlist('batch')
        salesAmount = request.POST.getlist('salesAmount')
        collectionDate = request.POST.getlist('collectionDate')
        purchaseDate = request.POST.getlist('purchaseDate')
        companyName = request.POST.getlist('companyName')
        purchaseAmount = request.POST.getlist('purchaseAmount')
        paymentDate = request.POST.getlist('paymentDate')

        for a, b, c, d, e, f, g, h in zip(controlNumber, batch, salesAmount, collectionDate, purchaseDate, companyName, purchaseAmount, paymentDate):
            print(a, b, c, d, e, f, g, h)

    context = {
        "message": "등록이 완료 되었습니다."
    }
    return render(request, 'sales/uploadpurchase.html', context)


def show_purchases(request):
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        contractName = request.POST['contractName']
        contractStep = request.POST['contractStep']
        purchaseInAdvance = request.POST['purchaseInAdvance']
        modifyMode = request.POST['modifyMode']
    else:
        startdate = ''
        enddate = ''
        empDeptName = ''
        empName = ''
        saleCompanyName = ''
        contractName = ''
        contractStep = ''
        purchaseInAdvance = ''
        modifyMode = 'N'

    accountspayable = 'N'
    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'purchaseInAdvance': purchaseInAdvance,
        'accountspayable': accountspayable,
        'modifyMode': modifyMode,
    }

    return render(request, 'sales/showpurchases.html', context)


@login_required
@csrf_exempt
def save_purchasetable(request):
    # datatable Data
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))
    predictBillingDate = request.GET.getlist('predictBillingDate')
    billingDate = request.GET.getlist('billingDate')
    predictWithdrawDate = request.GET.getlist('predictWithdrawDate')
    withdrawDate = request.GET.getlist('withdrawDate')
    comment = request.GET.getlist('comment')
    purchaseId = request.GET.getlist('purchaseId')
    # filter Data
    startdate = request.GET["startdate"]
    enddate = request.GET["enddate"]
    empDeptName = request.GET['empDeptName']
    empName = request.GET['empName']
    saleCompanyName = request.GET['saleCompanyName']
    contractName = request.GET['contractName']
    contractStep = request.GET['contractStep']
    purchaseInAdvance = request.GET['purchaseInAdvance']
    accountspayable = request.GET['accountspayable']
    modifyMode = 'N'

    for a, b, c, d, e, f in zip(purchaseId, predictBillingDate, billingDate, predictWithdrawDate, withdrawDate, comment):
        purchase = Purchase.objects.get(purchaseId=a)
        purchase.predictBillingDate = c or b + '-01' or None
        purchase.billingDate = c or None
        purchase.predictWithdrawDate = d or None
        purchase.withdrawDate = e or None
        purchase.comment = f
        purchase.save()

    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'purchaseInAdvance': purchaseInAdvance,
        'accountspayable': accountspayable,
        'modifyMode': modifyMode,
    }
    if accountspayable == 'Y':
        return render(request, 'sales/showaccountspayables.html', context)
    elif accountspayable == 'N':
        return render(request, 'sales/showpurchases.html', context)


@login_required
@csrf_exempt
def purchases_asjson(request):
    startdate = request.POST["startdate"]
    enddate = request.POST["enddate"]
    empDeptName = request.POST['empDeptName']
    empName = request.POST['empName']
    saleCompanyName = request.POST['saleCompanyName']
    contractName = request.POST['contractName']
    contractStep = request.POST['contractStep']
    purchaseInAdvance = request.POST['purchaseInAdvance']
    accountspayable = request.POST['accountspayable']
    # print(startdate,enddate,empDeptName,empName,saleCompanyName,contractName,contractStep,contractStep)

    if accountspayable == 'Y':
        purchase = Purchase.objects.filter(Q(billingDate__isnull=False) & Q(withdrawDate__isnull=True))
    elif accountspayable == 'N':
        purchase = Purchase.objects.all()

    if startdate:
        purchase = purchase.filter(Q(predictBillingDate__gte=startdate) or Q(predictWithdrawDate__gte=startdate))
    if enddate:
        purchase = purchase.filter(Q(predictBillingDate__lte=enddate) or Q(predictWithdrawDate__lte=enddate))
    if empDeptName != '전체' and empDeptName != '':
        purchase = purchase.filter(contractId__empDeptName=empDeptName)
    if empName != '전체' and empName != '':
        purchase = purchase.filter(contractId__empName=empName)
    if saleCompanyName:
        purchase = purchase.filter(contractId__saleCompanyName__companyName__icontains=saleCompanyName)
    if contractName:
        purchase = purchase.filter(contractId__contractName__contains=contractName)
    if contractStep != '전체' and contractStep != '':
        purchase = purchase.filter(contractId__contractStep=contractStep)
    if purchaseInAdvance != 'N' and purchaseInAdvance != '':
        # 매입일이 있는 계약
        purchaseContract = Purchase.objects.values('contractId').filter(billingDate__isnull=False).distinct()
        # 매출일이 있는 계약
        revenueContract = Revenue.objects.values('contractId').filter(billingDate__isnull=False).distinct()
        purchaseContract = list(purchaseContract)
        revenueContract = list(revenueContract)
        for i in revenueContract:
            if i in purchaseContract:
                purchaseContract.remove(i)
        contractId = [i['contractId'] for i in purchaseContract]
        purchase = purchase.filter(Q(contractId__in=contractId) & Q(billingDate__isnull=False))

    purchase = purchase.values('contractId__contractName', 'purchaseCompany', 'contractId__contractCode', 'predictBillingDate', 'billingDate', 'purchasePrice',
                               'predictWithdrawDate', 'withdrawDate', 'purchaseId', 'contractId__empDeptName', 'contractId__empName', 'contractId__contractStep', 'comment')
    structure = json.dumps(list(purchase), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_purchase(request, purchaseId):
    purchase = Purchase.objects.get(purchaseId=purchaseId)
    contractId = purchase.contractId.contractId

    context = viewContract(contractId)
    context['purchaseId'] = int(purchaseId)
    return render(request, 'sales/viewcontract.html', context)


@login_required
@csrf_exempt
def save_revenuetable(request):
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))
    # dataTable Data
    predictBillingDate = request.GET.getlist('predictBillingDate')
    billingDate = request.GET.getlist('billingDate')
    predictDepositDate = request.GET.getlist('predictDepositDate')
    depositDate = request.GET.getlist('depositDate')
    comment = request.GET.getlist('comment')
    revenueId = request.GET.getlist('revenueId')
    # filter Data
    startdate = request.GET["startdate"]
    enddate = request.GET["enddate"]
    empDeptName = request.GET['empDeptName']
    empName = request.GET['empName']
    saleCompanyName = request.GET['saleCompanyName']
    contractName = request.GET['contractName']
    contractStep = request.GET['contractStep']
    outstandingcollection = request.GET['outstandingcollection']
    modifyMode = 'N'

    for a, b, c, d, e, f in zip(revenueId, predictBillingDate, billingDate, predictDepositDate, depositDate, comment):
        revenue = Revenue.objects.get(revenueId=a)
        revenue.predictBillingDate = c or b + '-01' or None
        revenue.billingDate = c or None
        revenue.predictDepositDate = d or None
        revenue.depositDate = e or None
        revenue.comment = f
        revenue.save()

    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'outstandingcollection': outstandingcollection,
        'modifyMode': modifyMode,
    }
    if outstandingcollection == 'Y':
        return render(request, 'sales/showoutstandingcollections.html', context)
    elif outstandingcollection == 'N':
        return render(request, 'sales/showrevenues.html', context)


@login_required
@csrf_exempt
def show_outstandingcollections(request):
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        contractName = request.POST['contractName']
        contractStep = request.POST['contractStep']
        modifyMode = request.POST['modifyMode']

    else:
        startdate = ''
        enddate = ''
        empDeptName = ''
        empName = ''
        saleCompanyName = ''
        contractName = ''
        contractStep = ''
        modifyMode = 'N'

    outstandingcollection = 'Y'
    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'outstandingcollection': outstandingcollection,
        'modifyMode': modifyMode,
    }

    return render(request, 'sales/showoutstandingcollections.html', context)


@login_required
@csrf_exempt
def view_contract_pdf(request, contractId):
    context = viewContract(contractId)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    template = get_template('sales/viewcontractpdf.html')
    html = template.render(context, request)

    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    # return render(request, 'sales/viewcontractpdf.html', context)
    return response


@login_required
@csrf_exempt
def show_accountspayables(request):
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        contractName = request.POST['contractName']
        contractStep = request.POST['contractStep']
        purchaseInAdvance = request.POST['purchaseInAdvance']
        modifyMode = request.POST['modifyMode']
    else:
        startdate = ''
        enddate = ''
        empDeptName = ''
        empName = ''
        saleCompanyName = ''
        contractName = ''
        contractStep = ''
        purchaseInAdvance = ''
        modifyMode = 'N'

    accountspayable = 'Y'
    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'purchaseInAdvance': purchaseInAdvance,
        'accountspayable': accountspayable,
        'modifyMode': modifyMode,
    }

    return render(request, 'sales/showaccountspayables.html', context)


@login_required
@csrf_exempt
def change_predictpurchase(request):
    lastMonth = datetime(datetime.today().year, datetime.today().month - 1, 1)
    purchases = Purchase.objects.filter(Q(billingDate__isnull=True) & Q(predictBillingDate__lte=lastMonth)).exclude(contractId__contractStep='Drop')
    purchases = purchases.values('purchaseId', 'contractId__contractStep', 'contractId__contractCode', 'contractId__contractName', 'predictBillingDate')
    for purchase in purchases:
        purchase['nextBillingDate'] = datetime(datetime.today().year, datetime.today().month, 1).date()
    structure = json.dumps(list(purchases), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def save_predictpurchase(request):
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))
    purchaseId = request.POST.getlist('purchaseId')
    nextBillingDate = request.POST.getlist('nextBillingDate')

    if purchaseId:
        for id, next in zip(purchaseId, nextBillingDate):
            purchase = Purchase.objects.get(purchaseId=id)
            purchase.predictBillingDate = next
            purchase.save()

    # 필터 바꾸면 수정
    startdate = ''
    enddate = ''
    empDeptName = ''
    empName = ''
    saleCompanyName = ''
    contractName = ''
    contractStep = ''
    purchaseInAdvance = ''
    modifyMode = 'N'
    accountspayable = 'N'

    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'purchaseInAdvance': purchaseInAdvance,
        'accountspayable': accountspayable,
        'modifyMode': modifyMode,
    }

    return render(request, 'sales/showpurchases.html', context)


@login_required
@csrf_exempt
def change_predictrevenue(request):
    lastMonth = datetime(datetime.today().year, datetime.today().month - 1, 1)
    revenues = Revenue.objects.filter(Q(billingDate__isnull=True) & Q(predictBillingDate__lte=lastMonth)).exclude(contractId__contractStep='Drop')
    revenues = revenues.values('revenueId', 'contractId__contractStep', 'contractId__contractCode', 'contractId__contractName', 'predictBillingDate')

    for revenue in revenues:
        revenue['nextBillingDate'] = datetime(datetime.today().year, datetime.today().month, 1).date()

    structure = json.dumps(list(revenues), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def save_predictrevenue(request):
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))
    revenueId = request.POST.getlist('revenueId')
    nextBillingDate = request.POST.getlist('nextBillingDate')

    if revenueId:
        for id, next in zip(revenueId, nextBillingDate):
            revenues = Revenue.objects.get(revenueId=id)
            revenues.predictBillingDate = next
            revenues.save()

    # 필터 바꾸면 수정
    startdate = ''
    enddate = ''
    empDeptName = ''
    empName = ''
    saleCompanyName = ''
    contractName = ''
    contractStep = ''
    purchaseInAdvance = ''
    modifyMode = 'N'
    outstandingcollection = 'N'

    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'purchaseInAdvance': purchaseInAdvance,
        'outstandingcollection': outstandingcollection,
        'modifyMode': modifyMode,
    }

    return render(request, 'sales/showrevenues.html', context)
