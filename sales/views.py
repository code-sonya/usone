# -*- coding: utf-8 -*-
import json

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Sum, FloatField, F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
from django.core.serializers.json import DjangoJSONEncoder

from hr.models import Employee
from .forms import ContractForm, GoalForm
from .models import Contract, Category, Revenue, Contractitem, Goal, Purchase
from service.models import Company, Customer
from django.db.models import Q
from datetime import datetime, timedelta
import pandas as pd


@login_required
def post_contract(request):
    if request.method == "POST":
        form = ContractForm(request.POST)

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
    todayYear = datetime.today().year
    contract = Contract.objects.get(contractId=contractId)
    print(contract.contractStartDate.year)
    print(contract.contractEndDate)
    yearList = [i for i in range(int(contract.contractStartDate.year), int(contract.contractEndDate.year) + 1)]
    items = Contractitem.objects.filter(contractId=contractId)
    revenues = Revenue.objects.filter(contractId=contractId)
    purchases = Purchase.objects.filter(revenueId__contractId=contractId)
    totalDeposit = revenues.filter(depositDate__isnull=False).aggregate(sum_deposit=Sum('revenuePrice'))
    totalWithdraw = purchases.filter(withdrawDate__isnull=False).values('purchaseCompany').aggregate(sum_purchase=Sum('purchasePrice'))
    totalRatio = round(totalWithdraw['sum_purchase'] / totalDeposit['sum_deposit'] * 100, 2)
    ##### 입출금정보-매출
    companyDeposit = revenues.values('revenueCompany').annotate(
        filter_deposit=Sum('revenuePrice', filter=Q(depositDate__isnull=False) & (Q(predictBillingDate__year=todayYear) | Q(billingDate__year=todayYear)))
    ).annotate(
        sum_deposit=Sum('revenuePrice', filter=(Q(predictBillingDate__year=todayYear) | Q(billingDate__year=todayYear)))
    ).annotate(
        ratio_deposit=(Sum('revenuePrice', filter=Q(depositDate__isnull=False) & (Q(predictBillingDate__year=todayYear) | Q(billingDate__year=todayYear))) * 100 /
                        Sum('revenuePrice', filter=(Q(predictBillingDate__year=todayYear) | Q(billingDate__year=todayYear))))
    )

    companyTotalDeposit = revenues.annotate(
        filter_deposit=Sum('revenuePrice', filter=Q(depositDate__isnull=False) & (Q(predictBillingDate__year=todayYear) | Q(billingDate__year=todayYear)))
    ).annotate(
        sum_deposit=Sum('revenuePrice', filter=(Q(predictBillingDate__year=todayYear) | Q(billingDate__year=todayYear)))
    ).aggregate(
        a_filter_deposit=Sum('filter_deposit'),
        a_sum_deposit=Sum('sum_deposit')
    )
    companyTotalDeposit['a_ratio_deposit'] = round(companyTotalDeposit['a_filter_deposit'] / companyTotalDeposit['a_sum_deposit'] * 100)

    ##### 입출금정보-매입
    companyWithdraw = purchases.values('purchaseCompany').annotate(
        filter_withdraw=Sum('purchasePrice', filter=Q(withdrawDate__isnull=False) & (Q(revenueId__predictBillingDate__year=todayYear) | Q(revenueId__billingDate__year=todayYear)))
    ).annotate(
        sum_withdraw=Sum('purchasePrice', filter=(Q(revenueId__predictBillingDate__year=todayYear) | Q(revenueId__billingDate__year=todayYear)))
    ).annotate(
        ratio_withdraw=(Sum('purchasePrice', filter=Q(withdrawDate__isnull=False) & (Q(revenueId__predictBillingDate__year=todayYear) | Q(revenueId__billingDate__year=todayYear))) * 100 /
                        Sum('purchasePrice', filter=(Q(revenueId__predictBillingDate__year=todayYear) | Q(revenueId__billingDate__year=todayYear))))
    )

    companyTotalWithdraw = purchases.annotate(
        filter_withdraw=Sum('purchasePrice', filter=Q(withdrawDate__isnull=False) & (Q(revenueId__predictBillingDate__year=todayYear) | Q(revenueId__billingDate__year=todayYear)))
    ).annotate(
        sum_withdraw=Sum('purchasePrice', filter=(Q(revenueId__predictBillingDate__year=todayYear) | Q(revenueId__billingDate__year=todayYear)))
    ).aggregate(
        a_filter_withdraw=Sum('filter_withdraw'),
        a_sum_withdraw=Sum('sum_withdraw')
    )
    companyTotalWithdraw['a_ratio_withdraw'] = round(companyTotalWithdraw['a_filter_withdraw'] / companyTotalWithdraw['a_sum_withdraw'] * 100)

    context = {
        'revenueId': '',
        'contract': contract,
        'items': items,
        'revenues': revenues,
        'purchases': purchases,
        'companyWithdraw': companyWithdraw,
        'totalWithdraw': totalWithdraw,
        'totalDeposit': totalDeposit,
        'totalRatio': totalRatio,
        'companyDeposit':companyDeposit,
        'companyTotalDeposit':companyTotalDeposit,
        'companyTotalWithdraw':companyTotalWithdraw,
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
            post.saleCompanyName = Company.objects.filter(companyName=form.clean()['saleCompanyNames']).first()
            post.endCompanyName = Company.objects.filter(companyName=form.clean()['endCompanyNames']).first()
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
        saleCompanyNames = Contract.objects.get(contractId=contractId).saleCompanyName
        endCompanyNames = Contract.objects.get(contractId=contractId).endCompanyName
        companyList = Company.objects.filter(Q(companyStatus='Y'))
        companyNames = []
        for company in companyList:
            temp = {'id': company.pk, 'value': company.companyName}
            companyNames.append(temp)

        context = {
            'form': form,
            'items': items,
            'revenues': revenues,
            'saleCompanyNames': saleCompanyNames,
            'endCompanyNames': endCompanyNames,
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

    else:
        startdate = ''
        enddate = ''
        empDeptName = ''
        empName = ''
        saleCompanyName = ''
        contractName = ''

    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
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
        'revenueId': int(revenueId),
        'contract': contract,
        'items': items,
        'revenues': revenues,
    }
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

    contracts = contracts.values('contractStep', 'empDeptName', 'empName', 'contractCode', 'contractName', 'saleCompanyName', 'contractDate', 'contractId', 'salePrice', 'profitPrice')
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

    revenues = Revenue.objects.all()

    if startdate:
        revenues = revenues.filter(billingDate__gte=startdate)
    if enddate:
        revenues = revenues.filter(billingDate__lte=enddate)
    if empDeptName != '전체' and empDeptName != '':
        revenues = revenues.filter(contractId__empDeptName=empDeptName)
    if empName != '전체' and empName != '':
        revenues = revenues.filter(contractId__empName=empName)
    if saleCompanyName:
        revenues = revenues.filter(contractId__saleCompanyName__companyName__icontains=saleCompanyName)
    if contractName:
        revenues = revenues.filter(contractId__contractName__contains=contractName)

    revenues = revenues.values('billingDate', 'contractId__contractCode', 'contractId__contractName', 'contractId__saleCompanyName__companyName',
                               'revenuePrice', 'revenueProfitPrice', 'contractId__empName', 'contractId__empDeptName', 'revenueId')
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
    data = {}
    if "GET" == request.method:
        pass

    try:
        csv_file = request.FILES["csv_file"]
        xl_file = pd.ExcelFile(csv_file)
        dfs = pd.read_excel(xl_file, sheet_name='매출현황자료', skiprows=[0, 1, 2])
        print(dfs)

    except Exception as e:
        print(e)

    context = {
        "dfs": dfs
    }

    return render(request, 'sales/uploadpurchase.html', context)
