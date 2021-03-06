# -*- coding: utf-8 -*-
import json

from django.contrib.auth.decorators import login_required
from django.core import serializers

from django.db import connection
from django.db.models import Sum, FloatField, F, Case, When, Count
from django.db.models.functions import Cast
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, reverse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_POST

from approval.models import Document
from hr.models import Employee, AdminEmail, Alert, Department
from service.models import Servicereport
from client.models import Company, Customer
from logs.models import OrderLog, ContractLog
from .forms import ContractForm, GoalForm, PurchaseorderformForm
from .models import Contract, Category, Revenue, Contractitem, Goal, Purchase, Cost, Expense, Acceleration, Incentive, \
    Purchasetypea, Purchasetypeb, Purchasetypec, Purchasetyped, Contractfile, Purchasecategory, Purchasefile,\
    Purchaseorderform, Purchaseorder, Purchaseorderfile, Relatedpurchaseestimate, Purchasecontractitem, Classification, Contractcomment,\
    IncentiveDept
from .functions import viewContract, dailyReportRows, cal_revenue_incentive, cal_acc, cal_emp_incentive, cal_over_gp, \
    empIncentive, cal_monthlybill, cal_profitloss, daily_report_sql3, award, summary, detailPurchase, billing_schedule, mail_purchaseorder

from django.db.models import Q, Value, F, CharField, IntegerField, Max, Min
from datetime import datetime, timedelta, date
import pandas as pd
from xhtml2pdf import pisa
from service.functions import link_callback
from dateutil.relativedelta import relativedelta


@login_required
def post_contract(request):
    if request.method == "POST":
        form = ContractForm(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.writeEmpId = Employee.objects.get(empId=request.user.employee.empId)
            post.writeDatetime = datetime.now()
            post.editEmpId = Employee.objects.get(empId=request.user.employee.empId)
            post.editDatetime = datetime.now()
            post.empName = form.clean()['empId'].empName
            post.empDeptName = form.clean()['empId'].empDeptName
            post.saleCompanyName = Company.objects.filter(companyNameKo=form.clean()['saleCompanyNames']).first()
            post.endCompanyName = Company.objects.filter(companyNameKo=form.clean()['endCompanyNames']).first()
            if form.clean()['saleCustomerId']:
                post.saleCustomerName = form.clean()['saleCustomerId'].customerName
            else:
                post.saleCustomerName = ''
            if form.clean()['saleTaxCustomerId']:
                post.saleTaxCustomerName = form.clean()['saleTaxCustomerId'].customerName
            else:
                post.saleTaxCustomerName = ''
            post.mainCategory = json.loads(request.POST['jsonItem'])[0]['mainCategory']
            post.subCategory = json.loads(request.POST['jsonItem'])[0]['subCategory']
            post.save()

            # 관리번호 자동생성
            yy = str(datetime.now().year)[2:]
            mm = str(datetime.now().month).zfill(2)
            post.contractCode = 'O-' + yy + mm + '-' + str(post.contractId)
            post.save()

            jsonItem = json.loads(request.POST['jsonItem'])
            for item in jsonItem:
                Contractitem.objects.create(
                    contractId=post,
                    companyName=Company.objects.filter(companyNameKo=item["revenueCategoryCompany"]).first(),
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
                if int(revenue["revenuePrice"]) == 0:
                    revenueProfitRatio = 0
                else:
                    revenueProfitRatio = round((int(revenue["revenueProfitPrice"]) / int(revenue["revenuePrice"]) * 100))
                instance = Revenue.objects.create(
                    contractId=post,
                    empId=post.empId,
                    billingTime=str(idx) + '/' + str(len(jsonRevenue)),
                    predictBillingDate=revenue["billingDate"] or revenue["predictBillingDate"] + '-01' or None,
                    billingDate=revenue["billingDate"] or None,
                    predictDepositDate=revenue["predictDepositDate"] or None,
                    depositDate=revenue["depositDate"] or None,
                    revenueCompany=Company.objects.filter(companyNameKo=revenue["revenueCompany"]).first(),
                    revenuePrice=int(revenue["revenuePrice"]),
                    revenueProfitPrice=int(revenue["revenueProfitPrice"]),
                    revenueProfitRatio=revenueProfitRatio,
                    comment=revenue["revenueComment"],
                )
                revenueInstance = Revenue.objects.get(revenueId=int(instance.revenueId))
                revenueInstance.incentivePrice = cal_revenue_incentive(int(instance.revenueId))[0]
                revenueInstance.incentiveProfitPrice = cal_revenue_incentive(int(instance.revenueId))[1]
                revenueInstance.incentiveReason = cal_revenue_incentive(int(instance.revenueId))[2]
                revenueInstance.save()

            jsonPurchaseItem = json.loads(request.POST['jsonPurchaseItem'])
            for item in jsonPurchaseItem:
                Purchasecontractitem.objects.create(
                    contractId=post,
                    companyName=Company.objects.filter(companyNameKo=item["purchaseCategoryCompany"]).first(),
                    mainCategory=item["purchaseMainCategory"],
                    subCategory=item["purchaseSubCategory"],
                    itemName=item["purchaseItemName"],
                    itemPrice=int(item["purchaseItemPrice"])
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
                    purchaseCompany=Company.objects.filter(companyNameKo=purchase["purchaseCompany"]).first(),
                    purchasePrice=int(purchase["purchasePrice"]),
                    comment=purchase["purchaseComment"],
                )

            jsonCost = json.loads(request.POST['jsonCost'])
            for cost in jsonCost:
                Cost.objects.create(
                    contractId=post,
                    costCompany=cost["costCompany"],
                    costPrice=int(cost["costPrice"]),
                    billingTime=None,
                    billingDate=datetime(year=int(cost["costDate"]), month=12, day=31),
                    comment=cost["costComment"],
                )


            return redirect('sales:showcontracts')

    else:
        form = ContractForm()

        companyList = Company.objects.filter(Q(companyStatus='Y')).order_by('companyNameKo')
        companyNames = []
        for company in companyList:
            temp = {'id': company.pk, 'value': company.companyNameKo}
            companyNames.append(temp)

        empList = Employee.objects.filter(Q(empDeptName__contains='영업') & Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {'id': emp.empId, 'value': emp.empName}
            empNames.append(temp)

        context = {
            'form': form,
            'contractStep': 'Opportunity',
            'companyNames': companyNames,
            'companyList': companyList,
            'empNames': empNames,
        }
        return render(request, 'sales/postcontract.html', context)


@login_required
def copy_contract(request, contractId):
    beforeContract = Contract.objects.get(contractId=contractId)
    contract = Contract.objects.get(contractId=contractId)
    contract.pk = None
    contract.save()

    # 단계 Opportunity로 변경
    contract.contractStep = 'Opportunity'
    contract.empId = request.user.employee
    contract.empName = request.user.employee.empName
    contract.empDeptName = request.user.employee.empDeptName

    # 관리번호 자동생성
    yy = str(datetime.now().year)[2:]
    mm = str(datetime.now().month).zfill(2)
    contract.contractCode = 'O-' + yy + mm + '-' + str(contract.contractId)

    # 생성로그, 수정로그
    contract.writeEmpId = request.user.employee
    contract.writeDatetime = datetime.now()
    contract.editEmpId = request.user.employee
    contract.editDatetime = datetime.now()

    # 확인서 내용은 삭제
    contract.confirmCustomer = ''
    contract.confirmDate = None
    contract.confirmContents = ''
    contract.confirmComment = ''
    contract.save()

    # 매출 세부사항, 매출 빌링스케쥴, 매입 세부사항, 매입 빌링스케쥴, 원가 생성
    items = Contractitem.objects.filter(contractId=beforeContract)
    revenues = Revenue.objects.filter(contractId=beforeContract)
    purchaseItems = Purchasecontractitem.objects.filter(contractId=beforeContract)
    purchases = Purchase.objects.filter(contractId=beforeContract)
    costs = Cost.objects.filter(contractId=beforeContract)

    for item in items:
        item.pk = None
        item.contractId = contract
        item.save()
    for revenue in revenues:
        revenue.pk = None
        revenue.contractId = contract
        revenue.empId = request.user.employee
        revenue.billingDate = None
        revenue.predictDepositDate = None
        revenue.depositDate = None
        revenue.revenueStatus = 'N'
        revenue.save()
    for item in purchaseItems:
        item.pk = None
        item.contractId = contract
        item.save()
    for purchase in purchases:
        purchase.pk = None
        purchase.contractId = contract
        purchase.billingDate = None
        purchase.predictWithdrawDate = None
        purchase.withdrawDate = None
        purchase.save()
    for cost in costs:
        cost.pk = None
        cost.contractId = contract
        cost.save()

    return redirect('sales:modifycontract', contract.contractId)


@login_required
def show_contracts(request):
    employees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y')).order_by('empDeptName', 'empRank')

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        contractStep = request.POST["contractStep"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        endCompanyName = request.POST['endCompanyName']
        contractName = request.POST['contractName']
        mainCategory = request.POST['mainCategory']
        modifyContractPaper = request.POST['modifyContractPaper']

    else:
        if request.user.employee.empName == '이현승':
            startdate = '2018-01-01'
        else:
            startdate = str(datetime.now())[:4] + '-01-01'
        enddate = str(datetime.now())[:4] + '-12-31'
        contractStep = ''
        if request.user.employee.empDeptName == '영업팀':
            empDeptName = '영업전체'
        else:
            empDeptName = '전체'

        empName = ''
        saleCompanyName = ''
        endCompanyName = ''
        contractName = ''
        mainCategory = ''
        modifyContractPaper = ''

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
        'mainCategory': mainCategory,
        'modifyContractPaper': modifyContractPaper,
    }

    return render(request, 'sales/showcontracts.html', context)


@login_required
@csrf_exempt
def view_contract(request, contractId):
    context = viewContract(request, contractId)
    return render(request, 'sales/viewcontract.html', context)


@login_required
def modify_contract(request, contractId):
    contractInstance = Contract.objects.get(contractId=contractId)
    beforeSalePrice = contractInstance.salePrice
    beforeProfitPrice = contractInstance.profitPrice
    beforeProfitRatio = contractInstance.profitRatio

    if request.method == "POST":
        form = ContractForm(request.POST, request.FILES, instance=contractInstance)

        if form.is_valid():
            # 계약금액, 이익금액이 변경 되었을 경우 로그기록
            afterSalePrice = form.clean()['salePrice']
            afterProfitPrice = form.clean()['profitPrice']
            afterProfitRatio = form.clean()['profitRatio']
            if beforeSalePrice != afterSalePrice or beforeProfitPrice != afterProfitPrice:
                logs = ContractLog.objects.filter(contractId=contractInstance)
                if logs:
                    changeCount = len(logs) + 1
                else:
                    changeCount = 1
                ContractLog.objects.create(
                    empId=request.user.employee,
                    contractId=contractInstance,
                    changeCount=changeCount,
                    beforeSalePrice=beforeSalePrice,
                    beforeProfitPrice=beforeProfitPrice,
                    beforeProfitRatio=beforeProfitRatio,
                    afterSalePrice=afterSalePrice,
                    afterProfitPrice=afterProfitPrice,
                    afterProfitRatio=afterProfitRatio,
                    diffSalePrice=afterSalePrice-beforeSalePrice,
                    diffProfitPrice=afterProfitPrice-beforeProfitPrice,
                    diffProfitRatio=afterProfitRatio-beforeProfitRatio,
                )

            # 계약내용 수정
            post = form.save(commit=False)
            post.editEmpId = Employee.objects.get(empId=request.user.employee.empId)
            post.editDatetime = datetime.now()
            post.empName = form.clean()['empId'].empName
            post.empDeptName = form.clean()['empId'].empDeptName
            post.saleCompanyName = Company.objects.filter(companyNameKo=form.clean()['saleCompanyNames']).first()
            post.endCompanyName = Company.objects.filter(companyNameKo=form.clean()['endCompanyNames']).first()
            if form.clean()['saleCustomerId']:
                post.saleCustomerName = form.clean()['saleCustomerId'].customerName
            else:
                post.saleCustomerName = ''
            if form.clean()['saleTaxCustomerId']:
                post.saleTaxCustomerName = form.clean()['saleTaxCustomerId'].customerName
            else:
                post.saleTaxCustomerName = ''
            post.mainCategory = json.loads(request.POST['jsonItem'])[0]['mainCategory']
            post.subCategory = json.loads(request.POST['jsonItem'])[0]['subCategory']
            post.save()

            # 매출 세부사항 수정
            jsonItem = json.loads(request.POST['jsonItem'])
            itemId = list(i[0] for i in Contractitem.objects.filter(contractId=contractId).values_list('contractItemId'))
            jsonItemId = []
            for item in jsonItem:
                if item['itemId'] == '추가':
                    Contractitem.objects.create(
                        contractId=post,
                        companyName=Company.objects.filter(companyNameKo=item["revenueCategoryCompany"]).first(),
                        mainCategory=item["mainCategory"],
                        subCategory=item["subCategory"],
                        itemName=item["itemName"],
                        itemPrice=int(item["itemPrice"])
                    )
                else:
                    itemInstance = Contractitem.objects.get(contractItemId=int(item["itemId"]))
                    itemInstance.contractId = post
                    itemInstance.companyName = Company.objects.filter(companyNameKo=item["revenueCategoryCompany"]).first()
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

            # 매출 빌링스케줄 수정
            jsonRevenue = json.loads(request.POST['jsonRevenue'])
            jsonRevenue = sorted(jsonRevenue, key=lambda x: x['predictBillingDate'])
            idx = 0
            revenueId = list(i[0] for i in Revenue.objects.filter(contractId=contractId).values_list('revenueId'))
            jsonRevenueId = []
            for revenue in jsonRevenue:
                idx += 1
                if revenue['revenueId'] == '추가':
                    if int(revenue["revenuePrice"]) == 0:
                        revenueProfitRatio = 0
                    else:
                        revenueProfitRatio = round((int(revenue["revenueProfitPrice"]) / int(revenue["revenuePrice"]) * 100))
                    instance = Revenue.objects.create(
                        contractId=post,
                        empId=post.empId,
                        billingTime=str(idx) + '/' + str(len(jsonRevenue)),
                        predictBillingDate=revenue["billingDate"] or revenue["predictBillingDate"] + '-01' or None,
                        billingDate=revenue["billingDate"] or None,
                        predictDepositDate=revenue["predictDepositDate"] or None,
                        depositDate=revenue["depositDate"] or None,
                        revenueCompany=Company.objects.filter(companyNameKo=revenue["revenueCompany"]).first(),
                        revenuePrice=int(revenue["revenuePrice"]),
                        revenueProfitPrice=int(revenue["revenueProfitPrice"]),
                        revenueProfitRatio=revenueProfitRatio,
                        comment=revenue["revenueComment"],
                    )
                    revenueInstance = Revenue.objects.get(revenueId=int(instance.revenueId))
                    revenueInstance.incentivePrice = cal_revenue_incentive(int(instance.revenueId))[0]
                    revenueInstance.incentiveProfitPrice = cal_revenue_incentive(int(instance.revenueId))[1]
                    revenueInstance.incentiveReason = cal_revenue_incentive(int(instance.revenueId))[2]
                    revenueInstance.save()
                else:
                    revenueInstance = Revenue.objects.get(revenueId=int(revenue["revenueId"]))
                    revenueInstance.contractId = post
                    revenueInstance.billingTime = str(idx) + '/' + str(len(jsonRevenue))
                    revenueInstance.predictBillingDate = revenue["billingDate"] or revenue["predictBillingDate"] + '-01' or None
                    revenueInstance.billingDate = revenue["billingDate"] or None
                    revenueInstance.predictDepositDate = revenue["predictDepositDate"] or None
                    revenueInstance.depositDate = revenue["depositDate"] or None
                    revenueInstance.revenueCompany = Company.objects.filter(companyNameKo=revenue["revenueCompany"]).first()
                    revenueInstance.revenuePrice = int(revenue["revenuePrice"])
                    revenueInstance.revenueProfitPrice = int(revenue["revenueProfitPrice"])
                    if int(revenue["revenuePrice"]) == 0:
                        revenueInstance.revenueProfitRatio = 0
                    else:
                        revenueInstance.revenueProfitRatio = round((int(revenue["revenueProfitPrice"]) / int(revenue["revenuePrice"]) * 100))
                    revenueInstance.comment = revenue["revenueComment"]
                    revenueInstance.save()

                    revenueInstance = Revenue.objects.get(revenueId=int(revenue["revenueId"]))
                    revenueInstance.incentivePrice = cal_revenue_incentive(int(revenue["revenueId"]))[0]
                    revenueInstance.incentiveProfitPrice = cal_revenue_incentive(int(revenue["revenueId"]))[1]
                    revenueInstance.incentiveReason = cal_revenue_incentive(int(revenue["revenueId"]))[2]
                    revenueInstance.save()

                    jsonRevenueId.append(int(revenue["revenueId"]))

            delRevenueId = list(set(revenueId) - set(jsonRevenueId))

            if delRevenueId:
                for Id in delRevenueId:
                    Revenue.objects.filter(revenueId=Id).delete()

            # 매입 세부사항 수정
            jsonPurchaseItem = json.loads(request.POST['jsonPurchaseItem'])
            purchaseItemId = list(i[0] for i in Purchasecontractitem.objects.filter(contractId=contractId).values_list('contractItemId'))
            jsonPurchaseItemId = []
            for item in jsonPurchaseItem:
                if item['purchaseItemId'] == '추가':
                    Purchasecontractitem.objects.create(
                        contractId=post,
                        companyName=Company.objects.filter(companyNameKo=item["purchaseCategoryCompany"]).first(),
                        mainCategory=item["purchaseMainCategory"],
                        subCategory=item["purchaseSubCategory"],
                        itemName=item["purchaseItemName"],
                        itemPrice=int(item["purchaseItemPrice"])
                    )
                else:
                    purchaseItemInstance = Purchasecontractitem.objects.get(contractItemId=int(item["purchaseItemId"]))
                    purchaseItemInstance.contractId = post
                    purchaseItemInstance.companyName = Company.objects.filter(companyNameKo=item["purchaseCategoryCompany"]).first()
                    purchaseItemInstance.mainCategory = item["purchaseMainCategory"]
                    purchaseItemInstance.subCategory = item["purchaseSubCategory"]
                    purchaseItemInstance.itemName = item["purchaseItemName"]
                    purchaseItemInstance.itemPrice = int(item["purchaseItemPrice"])
                    purchaseItemInstance.save()
                    jsonPurchaseItemId.append(int(item['purchaseItemId']))

            delPurchaseItemId = list(set(purchaseItemId) - set(jsonPurchaseItemId))

            if delPurchaseItemId:
                for Id in delPurchaseItemId:
                    Purchasecontractitem.objects.filter(contractItemId=Id).delete()

            # 매입 빌링스케줄 수정
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
                        purchaseCompany=Company.objects.filter(companyNameKo=purchase["purchaseCompany"]).first(),
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
                    purchaseInstance.purchaseCompany = Company.objects.filter(companyNameKo=purchase["purchaseCompany"]).first()
                    purchaseInstance.purchasePrice = int(purchase["purchasePrice"])
                    purchaseInstance.comment = purchase["purchaseComment"]
                    purchaseInstance.save()
                    jsonPurchaseId.append(int(purchase["purchaseId"]))

            delPurchaseId = list(set(purchaseId) - set(jsonPurchaseId))

            if delPurchaseId:
                for Id in delPurchaseId:
                    Purchase.objects.filter(purchaseId=Id).delete()

            # 원가세부정보 수정
            jsonCost = json.loads(request.POST['jsonCost'])
            costId = list(i[0] for i in Cost.objects.filter(contractId=contractId).values_list('costId'))
            jsonCostId = []

            for cost in jsonCost:
                if cost['costId'] == '추가':
                    Cost.objects.create(
                        contractId=post,
                        costCompany=cost["costCompany"],
                        costPrice=int(cost["costPrice"]),
                        billingTime=None,
                        billingDate=datetime(year=int(cost["costDate"]), month=12, day=31),
                        comment=cost["costComment"],
                    )
                else:
                    costInstance = Cost.objects.get(costId=int(cost["costId"]))
                    costInstance.contractId = post
                    costInstance.costCompany = cost["costCompany"]
                    costInstance.costPrice = int(cost["costPrice"])
                    costInstance.billingTime = None
                    costInstance.billingDate = datetime(year=int(cost["costDate"]), month=12, day=31)
                    costInstance.comment = cost["costComment"]
                    costInstance.save()
                    jsonCostId.append(int(cost["costId"]))

            delCostId = list(set(costId) - set(jsonCostId))

            if delCostId:
                for Id in delCostId:
                    Cost.objects.filter(costId=Id).delete()

            return redirect('sales:viewcontract', str(contractId))

    else:
        form = ContractForm(instance=contractInstance)
        items = Contractitem.objects.filter(contractId=contractId)
        revenues = Revenue.objects.filter(contractId=contractId)
        purchases = Purchase.objects.filter(contractId=contractId)
        costs = Cost.objects.filter(contractId=contractId)
        saleCompanyNames = Contract.objects.get(contractId=contractId).saleCompanyName
        endCompanyNames = Contract.objects.get(contractId=contractId).endCompanyName
        # contractPaper = str(form.save(commit=False).contractPaper).split('/')[-1]
        orderPaper = str(form.save(commit=False).orderPaper).split('/')[-1]
        purchaseItems = Purchasecontractitem.objects.filter(contractId=contractId)


        companyList = Company.objects.filter(Q(companyStatus='Y')).order_by('companyNameKo')
        companyNames = []
        for company in companyList:
            temp = {'id': company.pk, 'value': company.companyNameKo}
            companyNames.append(temp)

        empList = Employee.objects.filter(Q(empDeptName__contains='영업') & Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {'id': emp.empId, 'value': emp.empName}
            empNames.append(temp)

        context = {
            'form': form,
            'contractEmpId': contractInstance.empId.empId,
            'contractStep': contractInstance.contractStep,
            'items': items,
            'purchaseItems': purchaseItems,
            'revenues': revenues.order_by('predictBillingDate'),
            'purchases': purchases.order_by('predictBillingDate'),
            'costs': costs,
            'saleCompanyNames': saleCompanyNames,
            'endCompanyNames': endCompanyNames,
            'contractId': contractId,
            # 'contractPaper': contractPaper,
            'orderPaper': orderPaper,
            'companyNames': companyNames,
            'empNames': empNames,
        }
        return render(request, 'sales/postcontract.html', context)


@login_required
def show_revenues(request):
    employees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y')).order_by('empDeptName', 'empRank')

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        contractName = request.POST['contractName']
        contractStep = request.POST['contractStep']
        modifyMode = request.POST['modifyMode']
        maincategory = request.POST['maincategory']
        issued = request.POST['issued']

    else:
        startdate = str(datetime.now())[:4] + '-01-01'
        enddate = str(datetime.now())[:4] + '-12-31'
        if request.user.employee.empDeptName == '영업팀':
            empDeptName = '영업전체'
        else:
            empDeptName = '전체'
        empName = ''
        saleCompanyName = ''
        contractName = ''
        contractStep = '전체'
        modifyMode = 'N'
        maincategory = ''
        issued = '전체'

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
        'maincategory': maincategory,
        'issued': issued,
    }

    return render(request, 'sales/showrevenues.html', context)


@login_required
@csrf_exempt
def view_revenue(request, revenueId):
    revenue = Revenue.objects.get(revenueId=revenueId)
    contractId = revenue.contractId.contractId

    context = viewContract(request, contractId)
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
    empStatus = request.POST['empStatus']

    if empStatus == 'Y':
        employees = Employee.objects.filter(Q(empStatus='Y')).order_by('empDeptName','empRank')
    else:
        employees = Employee.objects.all().order_by('empDeptName', 'empRank')

    if empDeptName == '전체':
        employees = employees.filter(Q(empDeptName__icontains='영업')).order_by('empDeptName', 'empRank')
    elif empDeptName == '영업전체':
        employees = employees.filter(Q(empDeptName='영업1팀')|Q(empDeptName='영업2팀')|Q(empDeptName='영업팀')).order_by('empDeptName', 'empRank')
    else:
        employees = employees.filter(Q(empDeptName=empDeptName) & Q(empStatus='Y')).order_by('empDeptName', 'empRank')

    json = serializers.serialize('json', employees)
    return HttpResponse(json, content_type='application/json')


@login_required
@csrf_exempt
def category_asjson(request):
    mainCategory = request.POST['mainCategory']
    subcategory = Category.objects.filter(mainCategory=mainCategory).order_by('subCategory')
    json = serializers.serialize('json', subcategory)
    return HttpResponse(json, content_type='application/json')


@login_required
@csrf_exempt
def contracts_asjson(request):
    user = Employee.objects.get(empId=request.POST['userId'])
    startdate = request.POST["startdate"]
    enddate = request.POST["enddate"]
    contractStep = request.POST["contractStep"]
    empDeptName = request.POST['empDeptName'].replace('&amp;', '&')
    empName = request.POST['empName']
    companyName = request.POST['companyName']
    saleCompanyName = request.POST['saleCompanyName']
    endCompanyName = request.POST['endCompanyName']
    contractName = request.POST['contractName']
    mainCategory = request.POST['mainCategory']
    modifyContractPaper = request.POST['modifyContractPaper']
    drops = request.POST['drops']

    if drops == "Y":
        contracts = Contract.objects.filter(contractStep='Drop')
    else:
        contracts = Contract.objects.filter(Q(contractStep='Opportunity') | Q(contractStep='Firm'))

    if user.empDeptName == '경영지원본부' or user.user.is_staff or user.empPosition.positionRank < 1:
        None
    elif user.empManager == 'Y':
        contracts = contracts.filter(empDeptName=user.empDeptName)
    else:
        if user.empName == '채해성':
            contracts = contracts.filter(Q(empId=user.empId) | Q(saleCompanyName__companyName__icontains='NH투자') | Q(empId__empStatus='N'))
        else:
            contracts = contracts.filter(Q(empId=user.empId) | Q(empId__empStatus='N'))

    revenues = Revenue.objects.all()
    purchases = Purchase.objects.all()
    if startdate:
        revenues = revenues.filter(predictBillingDate__gte=startdate).values_list('contractId__contractId', flat=True).distinct()
        purchases = purchases.filter(predictBillingDate__gte=startdate).values_list('contractId__contractId', flat=True).distinct()
    if enddate:
        revenues = revenues.filter(predictBillingDate__lte=enddate).values_list('contractId__contractId', flat=True).distinct()
        purchases = purchases.filter(predictBillingDate__lte=enddate).values_list('contractId__contractId', flat=True).distinct()
    contracts = contracts.filter(
        Q(contractId__in=revenues) |
        Q(contractId__in=purchases)
    )
    if contractStep != '전체' and contractStep != '':
        contracts = contracts.filter(contractStep=contractStep)
    if empDeptName != '전체' and empDeptName != '':
        if empDeptName == '영업전체':
            contracts = contracts.filter(Q(empDeptName='영업1팀')|Q(empDeptName='영업2팀')|Q(empDeptName='영업팀'))
        else:
            contracts = contracts.filter(empDeptName=empDeptName)
    if empName != '전체' and empName != '':
        contracts = contracts.filter(empName=empName)
    if companyName:
        contracts = contracts.filter(Q(saleCompanyName__companyName__icontains=companyName) | Q(endCompanyName__companyName__icontains=companyName))
    else:
        if saleCompanyName:
            contracts = contracts.filter(saleCompanyName__companyName__icontains=saleCompanyName)
        if endCompanyName:
            contracts = contracts.filter(endCompanyName__companyName__icontains=endCompanyName)
    if contractName:
        contracts = contracts.filter(contractName__contains=contractName)

    if mainCategory:
        contracts = contracts.filter(mainCategory__icontains=mainCategory)

    if modifyContractPaper:
        contracts = contracts.filter(modifyContractPaper=modifyContractPaper)

    contracts = contracts.values('contractStep', 'empDeptName', 'empName', 'contractCode', 'contractName', 'saleCompanyName__companyNameKo', 'endCompanyName__companyNameKo',
                                 'contractDate', 'contractId', 'salePrice', 'profitPrice', 'mainCategory', 'subCategory', 'saleIndustry', 'saleType', 'comment',
                                 'contractStartDate', 'contractEndDate', 'depositCondition', 'depositConditionDay')
    structure = json.dumps(list(contracts), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def revenues_asjson(request):
    startdate = request.POST["startdate"]
    enddate = request.POST["enddate"]
    empDeptName = request.POST['empDeptName'].replace('&amp;', '&')
    empName = request.POST['empName']
    saleCompanyName = request.POST['saleCompanyName']
    contractName = request.POST['contractName']
    contractStep = request.POST['contractStep']
    outstandingcollection = request.POST['outstandingcollection']
    maincategory = request.POST['maincategory']
    issued = request.POST['issued']
    user = Employee.objects.get(empId=request.POST['userId'])

    if outstandingcollection == 'Y':
        revenues = Revenue.objects.filter(Q(billingDate__isnull=False) & Q(depositDate__isnull=True))
    elif outstandingcollection == 'N':
        if issued == 'A':
            revenues = Revenue.objects.filter(Q(billingDate__isnull=True))
        elif issued == 'B':
            revenues = Revenue.objects.filter(Q(billingDate__isnull=False))
        elif issued == 'C':
            revenues = Revenue.objects.filter(Q(depositDate__isnull=False))
        else:
            revenues = Revenue.objects.all()

    if user.empDeptName == '경영지원본부' or user.user.is_staff or user.empPosition.positionRank < 1:
        None
    elif user.empManager == 'Y':
        revenues = revenues.filter(contractId__empDeptName=user.empDeptName)
    else:
        revenues = revenues.filter(Q(contractId__empId=user.empId) | Q(contractId__empId__empStatus='N'))

    if startdate:
        revenues = revenues.filter(predictBillingDate__gte=startdate)
    if enddate:
        revenues = revenues.filter(predictBillingDate__lte=enddate)
    if empDeptName != '전체' and empDeptName != '':
        if empDeptName == '영업전체':
            revenues = revenues.filter(Q(contractId__empDeptName='영업1팀') | Q(contractId__empDeptName='영업2팀') | Q(contractId__empDeptName='영업팀'))
        else:
            revenues = revenues.filter(contractId__empDeptName=empDeptName)
    if empName != '전체' and empName != '':
        revenues = revenues.filter(contractId__empName=empName)
    if saleCompanyName:
        revenues = revenues.filter(contractId__saleCompanyName__companyName__icontains=saleCompanyName)
    if contractName:
        revenues = revenues.filter(contractId__contractName__contains=contractName)
    if contractStep != '전체' and contractStep != '':
        revenues = revenues.filter(contractId__contractStep=contractStep)
    if maincategory:
        revenues = revenues.filter(contractId__mainCategory__icontains=maincategory)

    revenues = revenues.values('billingDate', 'contractId__contractCode', 'contractId__contractName', 'revenueCompany__companyNameKo', 'revenuePrice', 'revenueProfitPrice',
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
    employees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y')).order_by('empDeptName', 'empRank')
    pastEmployees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='N')).order_by('empDeptName', 'empRank')

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        contractName = request.POST['contractName']
        contractStep = request.POST['contractStep']
        modifyMode = request.POST['modifyMode']
        maincategory = request.POST['maincategory']
        issued = request.POST['issued']
    else:
        startdate = str(datetime.now())[:4] + '-01-01'
        enddate = str(datetime.now())[:4] + '-12-31'
        if request.user.employee.empDeptName == '영업팀':
            empDeptName = '영업전체'
        else:
            empDeptName = '전체'
        empName = ''
        saleCompanyName = ''
        contractName = ''
        contractStep = '전체'
        modifyMode = 'N'
        maincategory = ''
        issued = '전체'

    accountspayable = 'N'
    context = {
        'employees': employees,
        'pastEmployees': pastEmployees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'accountspayable': accountspayable,
        'modifyMode': modifyMode,
        'maincategory': maincategory,
        'issued': issued
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
    maincategory = request.GET['maincategory']
    issued = request.GET['issued']
    modifyMode = request.GET['modifyMode']
    searchText = request.GET['searchText']
    copyDate = request.GET['copyDate']

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
        'maincategory': maincategory,
        'issued': issued,
        'searchText': searchText,
        'copyDate': copyDate,
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
    empDeptName = request.POST['empDeptName'].replace('&amp;', '&')
    empName = request.POST['empName']
    saleCompanyName = request.POST['saleCompanyName']
    contractName = request.POST['contractName']
    contractStep = request.POST['contractStep']
    accountspayable = request.POST['accountspayable']
    maincategory = request.POST['maincategory']
    issued = request.POST['issued']
    user = Employee.objects.get(empId=request.POST['userId'])

    if accountspayable == 'Y':
        purchase = Purchase.objects.filter(Q(billingDate__isnull=False) & Q(withdrawDate__isnull=True))
    elif accountspayable == 'N':
        if issued == 'A':
            purchase = Purchase.objects.filter(billingDate__isnull=True)
        elif issued == 'B':
            purchase = Purchase.objects.filter(billingDate__isnull=False)
        elif issued == 'C':
            purchase = Purchase.objects.filter(withdrawDate__isnull=False)
        else:
            purchase = Purchase.objects.all()

    if user.empDeptName == '경영지원본부' or user.user.is_staff or user.empPosition.positionRank < 1:
        None
    elif user.empManager == 'Y':
        purchase = purchase.filter(contractId__empDeptName=user.empDeptName)
    else:
        purchase = purchase.filter(Q(contractId__empId=user.empId) | Q(contractId__empId__empStatus='N'))

    if startdate:
        purchase = purchase.filter(predictBillingDate__gte=startdate)
    if enddate:
        purchase = purchase.filter(predictBillingDate__lte=enddate)
    if empDeptName != '전체' and empDeptName != '':
        if empDeptName == '영업전체':
            purchase = purchase.filter(Q(contractId__empDeptName='영업1팀') | Q(contractId__empDeptName='영업2팀') | Q(contractId__empDeptName='영업팀'))
        else:
            purchase = purchase.filter(contractId__empDeptName=empDeptName)
    if empName != '전체' and empName != '':
        purchase = purchase.filter(contractId__empName=empName)
    if saleCompanyName:
        purchase = purchase.filter(contractId__saleCompanyName__companyName__icontains=saleCompanyName)
    if contractName:
        purchase = purchase.filter(contractId__contractName__contains=contractName)
    if contractStep != '전체' and contractStep != '':
        purchase = purchase.filter(contractId__contractStep=contractStep)
    if maincategory:
        purchase = purchase.filter(contractId__mainCategory__icontains=maincategory)

    purchase = purchase.values('contractId__contractName', 'purchaseCompany__companyNameKo', 'contractId__contractCode', 'predictBillingDate', 'billingDate', 'purchasePrice',
                               'predictWithdrawDate', 'withdrawDate', 'purchaseId', 'contractId__empDeptName', 'contractId__empName', 'contractId__contractStep', 'comment')
    structure = json.dumps(list(purchase), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_purchase(request, purchaseId):
    purchase = Purchase.objects.get(purchaseId=purchaseId)
    contractId = purchase.contractId.contractId

    context = viewContract(request, contractId)
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
    modifyMode = request.GET['modifyMode']
    searchText = request.GET['searchText']
    copyDate = request.GET['copyDate']

    for a, b, c, d, e, f in zip(revenueId, predictBillingDate, billingDate, predictDepositDate, depositDate, comment):
        revenue = Revenue.objects.get(revenueId=a)
        revenue.predictBillingDate = c or b + '-01' or None
        revenue.billingDate = c or None
        revenue.predictDepositDate = d or None
        revenue.depositDate = e or None
        revenue.comment = f
        revenue.save()

        revenue = Revenue.objects.get(revenueId=a)
        revenue.incentivePrice = cal_revenue_incentive(a)[0]
        revenue.incentiveProfitPrice = cal_revenue_incentive(a)[1]
        revenue.incentiveReason = cal_revenue_incentive(a)[2]
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
        'searchText': searchText,
        'copyDate': copyDate,
    }
    if outstandingcollection == 'Y':
        return render(request, 'sales/showoutstandingcollections.html', context)
    elif outstandingcollection == 'N':
        return render(request, 'sales/showrevenues.html', context)


@login_required
@csrf_exempt
def show_outstandingcollections(request):
    employees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y')).order_by('empDeptName', 'empRank')
    pastEmployees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='N')).order_by('empDeptName', 'empRank')

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        contractName = request.POST['contractName']
        contractStep = request.POST['contractStep']
        modifyMode = request.POST['modifyMode']
        maincategory = request.POST['maincategory']
        issued = request.POST['issued']

    else:
        startdate = ''
        enddate = ''
        empDeptName = '전체'
        empName = ''
        saleCompanyName = ''
        contractName = ''
        contractStep = ''
        modifyMode = 'N'
        maincategory = ''
        issued = ''

    outstandingcollection = 'Y'

    today = datetime.today()
    before = datetime.today() - timedelta(days=180)
    context = {
        'employees': employees,
        'pastEmployees': pastEmployees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'outstandingcollection': outstandingcollection,
        'modifyMode': modifyMode,
        'maincategory': maincategory,
        'issued': issued,
        'today': today,
        'before': before,
    }

    return render(request, 'sales/showoutstandingcollections.html', context)


@login_required
@csrf_exempt
def view_contract_pdf(request, contractId):
    context = viewContract(request, contractId)

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
    employees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y')).order_by('empDeptName', 'empRank')
    pastEmployees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='N')).order_by('empDeptName', 'empRank')

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        contractName = request.POST['contractName']
        contractStep = request.POST['contractStep']
        modifyMode = request.POST['modifyMode']
        maincategory = request.POST['maincategory']
        issued = request.POST['issued']
    else:
        startdate = ''
        enddate = ''
        empDeptName = '전체'
        empName = ''
        saleCompanyName = ''
        contractName = ''
        contractStep = '전체'
        modifyMode = 'N'
        maincategory = ''
        issued = '전체'

    accountspayable = 'Y'
    today = datetime.today()
    before = datetime.today() - timedelta(days=180)
    context = {
        'employees': employees,
        'pastEmployees': pastEmployees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'accountspayable': accountspayable,
        'modifyMode': modifyMode,
        'maincategory': maincategory,
        'issued': issued,
        'today': today,
        'before': before,
    }

    return render(request, 'sales/showaccountspayables.html', context)


@login_required
@csrf_exempt
def change_predictpurchase(request):
    todayDate = datetime(datetime.today().year, datetime.today().month, 1).date()
    lastDate = datetime.today() - relativedelta(months=1)
    purchases = Purchase.objects.filter(Q(billingDate__isnull=True) & Q(predictBillingDate__lte=lastDate)).exclude(contractId__contractStep='Drop')
    purchases = purchases.values('purchaseId', 'contractId__contractStep', 'contractId__contractCode', 'contractId__contractName', 'predictBillingDate')
    for purchase in purchases:
        purchase['nextBillingDate'] = todayDate
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
    modifyMode = 'Y'
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
    todayDate = datetime(datetime.today().year, datetime.today().month, 1).date()
    lastDate = datetime.today() - relativedelta(months=1)

    revenues = Revenue.objects.filter(Q(billingDate__isnull=True) & Q(predictBillingDate__lte=lastDate)).exclude(contractId__contractStep='Drop')

    revenues = revenues.values('revenueId', 'contractId__contractStep', 'contractId__contractCode', 'contractId__contractName', 'predictBillingDate')

    for revenue in revenues:
        revenue['nextBillingDate'] = todayDate

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


@login_required
@csrf_exempt
def transfer_contract(request):
    context = {}
    return render(request, 'sales/transfercontract.html', context)


@login_required
@csrf_exempt
def empid_asjson(request):
    empId = request.POST['empId']
    startdate = request.POST['transferStartDate']
    enddate = request.POST['transferEndDate']
    if empId:
        revenues = Revenue.objects.filter(empId=empId, revenueStatus='N')
    else:
        revenues = Revenue.objects.filter(revenueStatus='N')

    if startdate:
        revenues = revenues.filter(billingDate__gte=startdate)

    if enddate:
        revenues = revenues.filter(billingDate__lte=enddate)

    contractIds = revenues.values_list('contractId__contractId', flat=True).distinct()
    contracts = Contract.objects.filter(contractId__in=contractIds).values()

    for contract in contracts:
        revenue = revenues.filter(contractId=contract['contractId']).order_by('predictBillingDate')
        contract['revenue'] = list(revenue.values(
            'revenueId', 'contractId', 'revenueCompany_id', 'empId__empName', 'predictBillingDate', 'billingDate', 'revenuePrice')
        )

    structure = json.dumps(list(contracts), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def save_transfercontract(request):
    empId = Employee.objects.get(empId=request.POST['afterempName'])
    transferrevenues = request.POST.getlist('revenuecheck')
    for revenueId in transferrevenues:
        # 매출 영업대표 변경
        revenue = Revenue.objects.get(revenueId=revenueId)
        revenue.empId = empId
        revenue.save()

        contract = Contract.objects.get(contractId=revenue.contractId.contractId)
        # 계약의 영업대표 변경
        if contract.empId_id != empId.empId:
            contract.empId = empId
            contract.empName = empId.empName
            contract.empDeptName = empId.empDeptName
            contract.save()
    return redirect('sales:transfercontract')


def show_purchaseinadvance(request):
    employees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y')).order_by('empDeptName', 'empRank')
    pastEmployees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='N')).order_by('empDeptName', 'empRank')

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
        empDeptName = '전체'
        empName = ''
        saleCompanyName = ''
        contractName = ''
        contractStep = '전체'
        modifyMode = 'N'

    accountspayable = 'N'
    maincategory = ''
    issued = '전체'
    context = {
        'employees': employees,
        'pastEmployees': pastEmployees,
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'contractName': contractName,
        'contractStep': contractStep,
        'accountspayable': accountspayable,
        'modifyMode': modifyMode,
        'maincategory': maincategory,
        'issued': issued
    }

    return render(request, 'sales/showinadvance.html', context)


def save_company(request):
    companyName = request.POST['companyName']
    companyNameKo = request.POST['companyNameKo']
    companyNumber = request.POST['companyNumber']
    if request.POST['salesEmpId']:
        salesEmpId = Employee.objects.get(empId=request.POST['salesEmpId'])
    else:
        salesEmpId = None
    companyAddress = request.POST['companyAddress']

    if Company.objects.filter(companyName=companyName):
        result = 'N'
    else:
        Company.objects.create(companyName=companyName, companyNameKo=companyNameKo, companyNumber=companyNumber, saleEmpId=salesEmpId, companyAddress=companyAddress)
        result = ['Y', companyName, companyNameKo]

    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


def daily_report(request):
    # 연도, 월, 분기
    todayYear = datetime.today().year
    todayMonth = datetime.today().month
    todayQuarter = 0
    if todayMonth in [1, 2, 3]:
        todayQuarter = 1
    elif todayMonth in [4, 5, 6]:
        todayQuarter = 2
    elif todayMonth in [7, 8, 9]:
        todayQuarter = 3
    elif todayMonth in [10, 11, 12]:
        todayQuarter = 4

    # 2019년 실적 현황
    #  1. Firm 기준 연간 누계 달성 현황
    #   1-1. 연간 누계 달성 현황
    rowsFY = dailyReportRows(todayYear, 4, 'F')
    #   1-2. 분기 누계 달성 현황
    rowsFQ = dailyReportRows(todayYear, todayQuarter, 'F')
    #  2. Firm, Oppt'y 기준 연간 누계 달성 현황
    #   2-1. 연간 누계 달성 현황
    rowsFOY = dailyReportRows(todayYear, 4, 'FO')
    #   2-2. 분기 누계 달성 현황
    rowsFOQ = dailyReportRows(todayYear, todayQuarter, 'FO')

    with connection.cursor() as cursor:
        cursor.execute(daily_report_sql3)
        row = cursor.fetchone()
    money = {
        'A': int(row[0]),
        'B': int(row[1]),
        'AmB': int(row[2]),
        'C': int(row[3]),
        'D': int(row[4]),
        'E': int(row[5]),
        'CpD': int(row[6]),
        'F': int(row[7]),
        'AmF': int(row[8]),
    }

    # # 3. 채권 및 채무 현황
    # contracts = Contract.objects.filter(Q(contractStep='Opportunity') | Q(contractStep='Firm'))
    # revenues = Revenue.objects.all()
    # purchases = Purchase.objects.all()
    # money = {}
    #
    # # 3-1. 회계기준 기본 잔액
    # # 매출채권잔액(A)
    # money['A'] = revenues.filter(
    #     Q(billingDate__isnull=False) &
    #     Q(depositDate__isnull=True)
    # ).aggregate(sum=Sum('revenuePrice'))['sum']
    # # 매입채무잔액(B)
    # money['B'] = purchases.filter(
    #     Q(billingDate__isnull=False) &
    #     Q(withdrawDate__isnull=True)
    # ).aggregate(sum=Sum('purchasePrice'))['sum']
    # # A - B
    # money['AmB'] = money['A'] - money['B']
    #
    # # 2. 매입채무 조정
    # # 미접수(C), 선매입(D), 선지급(E)
    # money['C'] = 0
    # money['D'] = 0
    # money['E'] = 0
    # for contract in contracts:
    #     # 계약 별 매출발행비율
    #     contractRevenues = revenues.filter(contractId=contract.contractId)
    #     billingContractRevenues = contractRevenues.filter(Q(billingDate__isnull=False)).aggregate(sum=Sum('revenuePrice'))['sum'] or 0
    #     sumContractRevenues = contractRevenues.aggregate(sum=Sum('revenuePrice'))['sum'] or 0
    #     if sumContractRevenues:
    #         ratioContractRevenues = billingContractRevenues / sumContractRevenues
    #     else:
    #         ratioContractRevenues = 0
    #
    #     # 계약 별 매입접수비율
    #     contractPurchases = purchases.filter(contractId=contract.contractId)
    #     billingContractPurchases = contractPurchases.filter(Q(billingDate__isnull=False)).aggregate(sum=Sum('purchasePrice'))['sum'] or 0
    #     sumContractPurchases = contractPurchases.aggregate(sum=Sum('purchasePrice'))['sum'] or 0
    #     if sumContractPurchases:
    #         ratioContractPurchases = billingContractPurchases / sumContractPurchases
    #     else:
    #         ratioContractPurchases = 0
    #
    #     # 계약 별 수금비율
    #     depositContractRevenues = contractRevenues.filter(Q(depositDate__isnull=False)).aggregate(sum=Sum('revenuePrice'))['sum'] or 0
    #     if sumContractRevenues:
    #         depositRatioContractRevenues = depositContractRevenues / sumContractRevenues
    #     else:
    #         depositRatioContractRevenues = 0
    #
    #     # 계약 별 지급비율
    #     withdrawContractPurchases = contractPurchases.filter(Q(withdrawDate__isnull=False)).aggregate(sum=Sum('purchasePrice'))['sum'] or 0
    #     if sumContractPurchases:
    #         withdrawRatioContractPurchases = withdrawContractPurchases / sumContractPurchases
    #     else:
    #         withdrawRatioContractPurchases = 0
    #
    #     # 미접수, 선매입, 선수금, 선지급 계산
    #     if ratioContractRevenues > ratioContractPurchases:
    #         money['C'] += round(sumContractPurchases * (ratioContractRevenues - ratioContractPurchases))
    #     elif ratioContractRevenues < ratioContractPurchases:
    #         money['D'] += round(sumContractPurchases * (ratioContractRevenues - ratioContractPurchases))
    #     if depositRatioContractRevenues < withdrawRatioContractPurchases:
    #         money['E'] += round(sumContractPurchases * (depositRatioContractRevenues - withdrawRatioContractPurchases))
    # money['CpD'] = money['C'] + money['D']
    # money['F'] = money['B'] + money['CpD']
    #
    # # 3. 조정사항 반영 후 잔액
    # money['AmF'] = money['A'] - money['F']

    context = {
        'todayYear': todayYear,
        'todayMonth': todayMonth,
        'todayQuarter': str(todayQuarter) + 'Q',
        'today': datetime.today(),
        'before': datetime.today() - timedelta(days=180),
        'rowsFY': rowsFY,
        'rowsFQ': rowsFQ,
        'rowsFOY': rowsFOY,
        'rowsFOQ': rowsFOQ,
        'money': money,
    }

    return render(request, 'sales/dailyreport.html', context)


@login_required
@csrf_exempt
def outstanding_asjson(request):
    today = datetime.today()
    revenues = Revenue.objects.filter(Q(billingDate__isnull=False) & Q(depositDate__isnull=True) & Q(predictDepositDate__lt=today))
    revenues = revenues.values('billingDate', 'contractId__contractCode', 'contractId__contractName', 'revenueCompany__companyNameKo', 'revenuePrice', 'revenueProfitPrice',
                               'contractId__empName', 'contractId__empDeptName', 'revenueId', 'predictBillingDate', 'predictDepositDate', 'depositDate', 'contractId__contractStep',
                               'contractId__depositCondition', 'contractId__depositConditionDay', 'comment')

    structure = json.dumps(list(revenues), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def check_gp(request):
    contracts = Contract.objects.all().exclude(contractStep='Drop')
    revenues = Revenue.objects.values('contractId').annotate(sum_price=Sum('revenuePrice'), sum_profit=Sum('revenueProfitPrice'))
    purchases = Purchase.objects.values('contractId').annotate(sum_price=Sum('purchasePrice'))
    costs = Cost.objects.values('contractId').annotate(sum_price=Sum('costPrice'))
    contractFalse = []

    for contract in contracts:
        revenue = revenues.get(contractId=contract.contractId)
        revenuePrice = revenue['sum_price']
        revenueProfit = revenue['sum_profit']
        try:
            purchasePrice = purchases.get(contractId=contract.contractId)['sum_price']
        except:
            purchasePrice = 0
        try:
            costPrice = costs.get(contractId=contract.contractId)['sum_price']
        except:
            costPrice = 0

        if contract.salePrice != revenuePrice:
            contractFalse.append({"id": contract.contractId, 'code': contract.contractCode, 'name': contract.contractName, 'reason': '메출합계불일치'})
        if contract.profitPrice != revenueProfit:
            contractFalse.append({"id": contract.contractId, 'code': contract.contractCode, 'name': contract.contractName, 'reason': '이익합계불일치'})
        if revenuePrice - (purchasePrice + costPrice) != revenueProfit:
            contractFalse.append({
                "id": contract.contractId, 'code': contract.contractCode, 'name': contract.contractName, 'reason': 'GP불일치',
                'revenuePrice': revenuePrice,
                'purchasePrice': purchasePrice,
                'costPrice': costPrice,
                'gap': revenuePrice - (purchasePrice + costPrice),
                'gap_gp': revenuePrice - (purchasePrice + costPrice) - revenueProfit,
            })

    context = {
        'contractFalse': contractFalse,
        'contracts': contracts,
    }
    return render(request, 'sales/checkgp.html', context)


@login_required
@csrf_exempt
def check_service(request):
    services = Servicereport.objects.filter(
        Q(contractId__isnull=False) &
        Q(serviceStatus='Y') &
        ~Q(serviceType__typeName__icontains='상주') &
        (
                Q(empDeptName='DB지원팀') |
                Q(empDeptName='솔루션지원팀') |
                Q(empDeptName='인프라서비스사업팀')
        )
    )

    services = services.values('contractId').annotate(
        salary=Sum(F('serviceRegHour') * F('empId__empPosition__positionSalary'), output_field=FloatField()),
        overSalary=Sum(F('serviceOverHour') * F('empId__empPosition__positionSalary') * 1.5, output_field=FloatField()),
        sumSalary=Sum(F('serviceRegHour') * F('empId__empPosition__positionSalary'), output_field=FloatField()) +
                  Sum(F('serviceOverHour') * F('empId__empPosition__positionSalary') * 1.5, output_field=FloatField())
    )

    services = services.values(
        'contractId_id', 'contractId__contractCode', 'contractId__contractName', 'contractId__contractStartDate',
        'contractId__contractEndDate', 'contractId__salePrice', 'contractId__profitPrice', 'salary', 'overSalary', 'sumSalary'
    )

    for service in services:
        service['gpSalary'] = service['contractId__profitPrice'] - service['sumSalary']

    context = {
        'services': services,
    }
    return render(request, 'sales/checkservice.html', context)


@login_required
@csrf_exempt
def inadvance_asjson(request):
    user = Employee.objects.get(empId=request.POST['userId'])
    startdate = request.POST["startdate"]
    enddate = request.POST["enddate"]
    contractStep = request.POST["contractStep"]
    empDeptName = request.POST['empDeptName'].replace('&amp;', '&')
    empName = request.POST['empName']
    saleCompanyName = request.POST['saleCompanyName']
    endCompanyName = request.POST['endCompanyName']
    contractName = request.POST['contractName']
    mainCategory = request.POST['mainCategory']
    title = request.POST['title']

    contracts = Contract.objects.filter(Q(contractStep='Opportunity') | Q(contractStep='Firm'))

    if user.empDeptName == '경영지원본부' or user.user.is_staff or user.empPosition.positionRank < 1:
        None
    elif user.empManager == 'Y':
        contracts = contracts.filter(empDeptName=user.empDeptName)
    else:
        contracts = contracts.filter(empId=user.empId)

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
    if mainCategory:
        contracts = contracts.filter(mainCategory__icontains=mainCategory)

    revenues = Revenue.objects.all()
    purchases = Purchase.objects.all()

    contracts = contracts.values('contractStep', 'contractCode', 'empDeptName', 'empName', 'contractName', 'saleCompanyName__companyNameKo', 'endCompanyName__companyNameKo',
                                 'contractDate', 'contractId', 'salePrice', 'profitPrice', 'mainCategory', 'subCategory', 'saleIndustry', 'saleType', 'comment',
                                 'contractStartDate', 'contractEndDate', 'depositCondition', 'depositConditionDay')

    purchaseinadvanceList = []

    for contract in contracts:
        # 계약 별 매출발행비율
        contractRevenues = revenues.filter(contractId=contract['contractId'])
        billingContractRevenues = contractRevenues.filter(Q(billingDate__isnull=False)).aggregate(sum=Sum('revenuePrice'))['sum'] or 0
        sumContractRevenues = contractRevenues.aggregate(sum=Sum('revenuePrice'))['sum'] or 0
        if sumContractRevenues:
            ratioContractRevenues = billingContractRevenues / sumContractRevenues
        else:
            ratioContractRevenues = 0

            # 계약 별 매입접수비율
        contractPurchases = purchases.filter(contractId=contract['contractId'])
        billingContractPurchases = contractPurchases.filter(Q(billingDate__isnull=False)).aggregate(sum=Sum('purchasePrice'))['sum'] or 0
        sumContractPurchases = contractPurchases.aggregate(sum=Sum('purchasePrice'))['sum'] or 0
        if sumContractPurchases:
            ratioContractPurchases = billingContractPurchases / sumContractPurchases
        else:
            ratioContractPurchases = 0

        # 계약 별 수금비율
        depositContractRevenues = contractRevenues.filter(Q(depositDate__isnull=False)).aggregate(sum=Sum('revenuePrice'))['sum'] or 0
        if sumContractRevenues:
            depositRatioContractRevenues = depositContractRevenues / sumContractRevenues
        else:
            depositRatioContractRevenues = 0

            # 계약 별 지급비율
        withdrawContractPurchases = contractPurchases.filter(Q(withdrawDate__isnull=False)).aggregate(sum=Sum('purchasePrice'))['sum'] or 0
        if sumContractPurchases:
            withdrawRatioContractPurchases = withdrawContractPurchases / sumContractPurchases
        else:
            withdrawRatioContractPurchases = 0

        contract['billingInadvance'] = round(sumContractPurchases * (ratioContractRevenues - ratioContractPurchases))

        if depositRatioContractRevenues < withdrawRatioContractPurchases:
            contract['withdrawInadvance'] = round(sumContractPurchases * (depositRatioContractRevenues - withdrawRatioContractPurchases))
            contract['depositInadvance'] = 0
        elif depositRatioContractRevenues > withdrawRatioContractPurchases:
            contract['withdrawInadvance'] = 0
            contract['depositInadvance'] = round(sumContractPurchases * (depositRatioContractRevenues - withdrawRatioContractPurchases))
        else:
            contract['withdrawInadvance'] = 0
            contract['depositInadvance'] = 0
        if contract['billingInadvance'] != 0 or contract['withdrawInadvance'] != 0 or contract['depositInadvance'] != 0:
            if title == '선매입관리':
                if ratioContractRevenues <= ratioContractPurchases:
                    purchaseinadvanceList.append(contract)
            elif title == '미접수관리':
                if ratioContractRevenues > ratioContractPurchases:
                    purchaseinadvanceList.append(contract)

    structure = json.dumps(purchaseinadvanceList, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


def show_purchaseinadvance(request):
    employees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y')).order_by('empDeptName', 'empRank')

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        contractStep = request.POST["contractStep"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        endCompanyName = request.POST['endCompanyName']
        contractName = request.POST['contractName']
        mainCategory = request.POST['mainCategory']

    else:
        startdate = ''
        enddate = ''
        contractStep = ''
        empDeptName = '전체'
        empName = ''
        saleCompanyName = ''
        endCompanyName = ''
        contractName = ''
        mainCategory = ''

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
        'mainCategory': mainCategory,
        'title': '선매입관리',
        'money': '선매입금액',
    }

    return render(request, 'sales/showinadvance.html', context)


def show_revenueinadvance(request):
    employees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y')).order_by('empDeptName', 'empRank')

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        contractStep = request.POST["contractStep"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        saleCompanyName = request.POST['saleCompanyName']
        endCompanyName = request.POST['endCompanyName']
        contractName = request.POST['contractName']
        mainCategory = request.POST['mainCategory']

    else:
        startdate = ''
        enddate = ''
        contractStep = ''
        empDeptName = '전체'
        empName = ''
        saleCompanyName = ''
        endCompanyName = ''
        contractName = ''
        mainCategory = ''

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
        'mainCategory': mainCategory,
        'title': '미접수관리',
        'money': '미접수금액',
    }

    return render(request, 'sales/showinadvance.html', context)


@login_required
@csrf_exempt
def contract_revenues(request):
    contractId = request.POST['contractId']
    revenues = Revenue.objects.filter(Q(contractId__contractId=contractId))
    revenues = revenues.values(
        'billingTime', 'empId__empName', 'predictBillingDate', 'billingDate', 'predictDepositDate', 'depositDate',
        'revenueCompany__companyNameKo', 'revenuePrice', 'revenueProfitPrice', 'comment', 'revenueId'
    )
    structure = json.dumps(list(revenues), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def contract_purchases(request):
    contractId = request.POST['contractId']
    purchases = Purchase.objects.filter(Q(contractId__contractId=contractId))
    purchases = purchases.values(
        'billingTime', 'predictBillingDate', 'billingDate', 'predictWithdrawDate', 'withdrawDate',
        'purchaseCompany__companyNameKo', 'purchasePrice', 'comment', 'purchaseId'
    )
    structure = json.dumps(list(purchases), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def contract_costs(request):
    contractId = request.POST['contractId']
    costs = Cost.objects.filter(Q(contractId__contractId=contractId))
    costs = costs.values('billingTime', 'billingDate', 'costCompany', 'costPrice', 'comment', 'costId')
    structure = json.dumps(list(costs), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def contract_services(request):
    contractId = request.POST['contractId']
    services = Servicereport.objects.filter(
        Q(contractId=contractId) & Q(serviceStatus='Y') & (Q(empDeptName='DB지원팀') | Q(empDeptName='솔루션지원팀') | Q(empDeptName='인프라서비스사업팀')))
    services = services.annotate(
        salary=Case(
            When(serviceType__typeName='상주' or '프로젝트상주', then=Value(0)),
            default=Cast(F('serviceRegHour') * F('empId__empPosition__positionSalary'), FloatField()),
            output_field=FloatField(),
        ),
    ).annotate(
        overSalary=Case(
            When(serviceType__typeName='상주' or '프로젝트상주', then=Value(0)),
            default=Cast(F('serviceOverHour') * F('empId__empPosition__positionSalary') * 1.5, FloatField()),
            output_field=FloatField(),
        )
    )
    services = services.values(
        'empName', 'serviceType__typeName', 'serviceDate', 'serviceTitle',
        'serviceHour', 'serviceRegHour', 'serviceOverHour', 'salary', 'overSalary', 'serviceId'
    )
    structure = json.dumps(list(services), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_incentive(request, year, empId):
    year = str(year)
    if int(year) <= 2019:
        # 2019년 정책 (팀별 목표, 팀별 매출)
        empName = Employee.objects.get(empId=empId).empName
        empDeptName = IncentiveDept.objects.get(empId=empId, year=year).deptName
        incentive = Incentive.objects.filter(Q(empId=empId) & Q(year=year))
        if not incentive:
            msg = '인센티브 산출에 필요한 개인 정보가 없습니다.'
            return render(request, 'sales/viewincentive.html', {'msg': msg, 'empName': empName, 'empId': empId, 'year': year})
        goal = Goal.objects.filter(Q(empDeptName=empDeptName) & Q(year=year))
        if not goal:
            msg = '인센티브 산출에 필요한 목표 정보가 없습니다.'
            return render(request, 'sales/viewincentive.html', {'msg': msg, 'empName': empName, 'empId': empId, 'year': year})
        table1, table2, table3 = empIncentive(year, empId)
        table4, sumachieveIncentive, sumachieveAward, GPachieve, newCount, overGp, incentiveRevenues = award(
            year, empDeptName, table2, goal.first(), empName, incentive, empId
        )

        context = {
            'empId': empId,
            'empName': empName,
            'table1': table1,
            'table2': table2,
            'table3': table3,
            'table4': table4,
            'sumachieveIncentive': sumachieveIncentive,
            'sumachieveAward': sumachieveAward,
            'GPachieve': GPachieve,
            'newCount': newCount,
            'overGp': overGp,
            'incentiveRevenues': incentiveRevenues,
            'year': year,
        }
        return render(request, 'sales/viewincentive.html', context)

    else:
        # 2020년 정책
        empName = Employee.objects.get(empId=empId).empName
        empDeptName = Employee.objects.get(empId=empId).empDeptName
        incentive = Incentive.objects.filter(Q(empId=empId) & Q(year=year))
        if not incentive:
            msg = '인센티브 산출에 필요한 개인 정보가 없습니다.'
            return render(request, 'sales/viewincentive.html', {'msg': msg, 'empName': empName, 'empId': empId, 'year': year})
        goal = Goal.objects.filter(Q(empDeptName=empDeptName) & Q(year=year))
        if not goal:
            msg = '인센티브 산출에 필요한 목표 정보가 없습니다.'
            return render(request, 'sales/viewincentive.html', {'msg': msg, 'empName': empName, 'empId': empId, 'year': year})
        table1, table2, table3 = empIncentive(year, empId)
        table4, sumachieveIncentive, sumachieveAward, GPachieve, newCount, overGp, incentiveRevenues = award(
            year, empDeptName, table2, goal.first(), empName, incentive, empId
        )

        context = {
            'empId': empId,
            'empName': empName,
            'table1': table1,
            'table2': table2,
            'table3': table3,
            'table4': table4,
            'sumachieveIncentive': sumachieveIncentive,
            'sumachieveAward': sumachieveAward,
            'GPachieve': GPachieve,
            'newCount': newCount,
            'overGp': overGp,
            'incentiveRevenues': incentiveRevenues,
            'year': year,
        }
        return render(request, 'sales/viewincentive.html', context)


@login_required
@csrf_exempt
def upload_profitloss(request):
    context = {}
    return render(request, 'sales/uploadprofitloss.html', context)


@login_required
def save_profitloss(request):
    date = request.POST["month"]
    todayYear = int(date[:4])
    todayMonth = int(date[5:])
    if datetime.today().year == todayYear and datetime.today().month == todayMonth:
        today = datetime.today()
    else:
        today = datetime(todayYear, todayMonth, 1) + relativedelta(months=1) - relativedelta(days=1)

    profitloss_file = request.FILES["profitloss_file"]
    xl_file = pd.ExcelFile(profitloss_file)
    data = pd.read_excel(xl_file, index_col=0)
    data = data.fillna(0)
    if todayYear < 2020:
        select_col = ['합    계', '대표이사(1000)', '감사(1100)', '고문(1200)', '경영지원본부(1300)', '사장(1400)',
                  '인프라솔루션_임원(3000)', '영업1팀(3100)', '영업2팀(3200)', '인프라서비스(3400)', '고객서비스_임원(5000)',
                  '솔루션지원팀(5100)', 'DB지원팀(5300)']
    else:
        select_col = ['합    계', '대표이사(1000)', '감사(1100)', '고문(1200)', '경영지원본부(1300)', '사장(1400)',
                      '인프라_부사장(3000)', '영업팀(3100)', 'R&D전략_이사(4000)', 'TA팀(4100)', 'AI Platform Labs(4200)', 'Platform Biz_이사(5000)',
                      '솔루션팀(5100)', 'DB Expert팀(5200)']
    index_lst = ["".join(i.split()) for i in data.index]
    if 'Ⅳ.판매비와관리비' not in index_lst or 'Ⅴ.영업이익' not in index_lst:
        return HttpResponse("잘못된 양식입니다. 엑셀에 Ⅳ.판매비와관리비 , Ⅴ.영업이익이 포함 되어 있어야 합니다. 관리자에게 문의하세요 :)")

    status = False
    Expense.objects.filter(Q(expenseStatus='Y') & Q(expenseType='손익') & Q(expenseDate__year=todayYear) & Q(expenseDate__month=todayMonth)).update(expenseStatus='N')
    for index, rows in data[select_col].iterrows():

        if "".join(index.split()) == 'Ⅴ.영업이익':
            break

        if status == True:
            nindex = index.replace('▷', '')
            sub = "".join(nindex.split())
            if sub in ['임원급여', '직원급여']:
                group = '급여'
            elif sub in ['인센티브', '상여금', '특별인센티브']:
                group = '상여금'
            else:
                group = sub
            if todayYear < 2020:
                for i, v in enumerate(['전사', '대표이사', '감사', '고문', '경영지원본부', '사장', '인프라솔루션_임원', '영업1팀',
                                       '영업2팀', '인프라서비스', '고객서비스_임원', '솔루션지원팀', 'DB지원팀']):
                    Expense.objects.create(expenseDate=today, expenseType='손익', expenseDept=v, expenseMain='판관비',
                                           expenseSub=sub, expenseMoney=rows[i], expenseGroup=group)
            else:
                for i, v in enumerate(['전사', '대표이사', '감사', '고문', '경영지원본부', '사장', '인프라_부사장', '영업팀',
                                       'R&D전략_이사', 'TA팀', 'AI Platform Labs', 'Platform Biz_이사', '솔루션팀', 'DB Expert팀']):
                    Expense.objects.create(expenseDate=today, expenseType='손익', expenseDept=v, expenseMain='판관비',
                                           expenseSub=sub, expenseMoney=rows[i], expenseGroup=group)

        if "".join(index.split()) == 'Ⅳ.판매비와관리비':
            status = True

    return redirect('sales:uploadprofitloss')


@login_required
def save_cost(request):
    date = request.POST["month"]
    todayYear = int(date[:4])
    todayMonth = int(date[5:])
    if datetime.today().year == todayYear and datetime.today().month == todayMonth:
        today = datetime.today()
    else:
        today = datetime(todayYear, todayMonth, 1) + relativedelta(months=1) - relativedelta(days=1)

    cost_file = request.FILES["cost_file"]
    xl_file = pd.ExcelFile(cost_file)
    data = pd.read_excel(xl_file, index_col=0)
    data = data.fillna(0)
    index_lst = ["".join(i.split()) for i in data.index]
    if 'Ⅲ.당기총공사비용' not in index_lst or 'Ⅰ.노무비' not in index_lst or 'Ⅱ.경비' not in index_lst:
        return HttpResponse("잘못된 양식입니다. 엑셀에 Ⅰ.노무비, Ⅱ.경비, Ⅲ.당기총공사비용이 포함 되어 있어야 합니다. 관리자에게 문의하세요 :)")

    if todayYear < 2020:
        select_col = ['솔루션지원팀(5100)', 'DB지원팀(5300)']
    else:
        select_col = ['Platform Biz_이사(5000)', '솔루션팀(5100)', 'DB Expert팀(5200)']
    Expense.objects.filter(Q(expenseStatus='Y') & Q(expenseType='원가') & Q(expenseDate__year=todayYear) & Q(expenseDate__month=todayMonth)).update(expenseStatus='N')

    main_cate = ''
    for index, rows in data[select_col].iterrows():
        nindex = index.replace('▶', '')
        sub = "".join(nindex.split())
        if sub in ['급여']:
            group = '급여'
        elif sub in ['상여금']:
            group = '상여금'
        else:
            group = sub
        if index == 'Ⅰ.노무비':
            main_cate = '노무비'
        elif index == 'Ⅱ.경비':
            main_cate = '경비'
        elif index == 'Ⅲ.당기총공사비용':
            break
        else:
            if main_cate != '':
                if todayYear < 2020:
                    for i, v in enumerate(['솔루션지원팀', 'DB지원팀']):
                        Expense.objects.create(expenseDate=today, expenseType='원가', expenseDept=v, expenseMain=main_cate,
                                               expenseSub=sub, expenseMoney=rows[i], expenseGroup=group)
                else:
                    for i, v in enumerate(['Platform Biz_이사', '솔루션팀', 'DB Expert팀']):
                        Expense.objects.create(expenseDate=today, expenseType='원가', expenseDept=v, expenseMain=main_cate,
                                               expenseSub=sub, expenseMoney=rows[i], expenseGroup=group)

    return redirect('sales:uploadprofitloss')


@login_required
def view_incentiveall(request):
    # 조회 분기 (기본값은 현재 분기)
    if request.method == "POST":
        todayYear = int(request.POST["year"])
        todayQuarter = int(request.POST["quarter"])
    else:
        todayYear = datetime.today().year
        todayMonth = datetime.today().month
        todayQuarter = ((todayMonth + 2) // 3)

    # 다음 월
    if todayQuarter == 4:
        nextMonth = 1
    else:
        nextMonth = todayQuarter * 3 + 1

    # 이전 분기
    if todayQuarter == 1:
        beforeQuarter = 0
    else:
        beforeQuarter = todayQuarter - 1

    emps = Incentive.objects.filter(
        Q(year=todayYear) &
        Q(quarter__lte=todayQuarter)
        # Q(empId__empStatus='Y')
    ).values('empId').distinct()

    excludeEmps = Incentive.objects.filter(
        Q(year=todayYear) &
        Q(quarter=todayQuarter) &
        Q(salary=0)
    ).values('empId').distinct()

    basic = Incentive.objects.filter(
        Q(year=todayYear) &
        Q(quarter__lte=todayQuarter)
    ).values('empId', 'empId__empPosition__positionName', 'empId__empName').annotate(
        empPosition=F('empId__empPosition__positionName'),
        empName=F('empId__empName'),
        sum_salary=Sum('salary'),
        sum_basicSalary=Sum('basicSalary'),
        sum_bettingSalary=Sum('bettingSalary'),
        sum_achieveIncentive=Sum('achieveIncentive'),
        sum_achieveAward=Sum('achieveAward'),
    )

    if beforeQuarter:
        before = Incentive.objects.filter(
            Q(year=todayYear) &
            Q(quarter__lte=beforeQuarter)
        ).values('empId').annotate(
            sum_achieveIncentive=Sum('achieveIncentive'),
            sum_achieveAward=Sum('achieveAward'),
        )
    else:
        before = []

    current = Incentive.objects.filter(
        Q(year=todayYear) &
        Q(quarter=todayQuarter)
    ).values('empId', 'achieveIncentive', 'achieveAward')

    table = []
    sum_table = {
        'sum_salary': 0, 'sum_basicSalary': 0, 'sum_bettingSalary': 0,
        'sum_cumulateIncentive': 0, 'sum_achieveIncentive': 0, 'achieveIncentive': 0,
        'achieveAward': 0, 'sum_achieveAward': 0, 'compareIncentive': 0
    }

    for emp in emps:
        if emp not in excludeEmps:
            _, _, tmp_table3 = empIncentive(str(todayYear), int(emp['empId']))
            tmp_basic = basic.get(empId=emp['empId'])

            if beforeQuarter:
                tmp_before = before.get(empId=emp['empId'])
            else:
                tmp_before = {'sum_achieveIncentive': 0}
            tmp_current = current.get(empId=emp['empId'])

            achieveRatio = 0
            creditRatio = 0
            ACC = 0
            cumulateIncentive = 0

            for t in tmp_table3:
                if t['name'] == '목표 달성률':
                    achieveRatio = t['q' + str(todayQuarter)]
                if t['name'] == '인정률':
                    creditRatio = t['q' + str(todayQuarter)]
                if t['name'] == 'ACC':
                    ACC = t['q' + str(todayQuarter)]
                if t['name'] == '예상누적인센티브':
                    cumulateIncentive = t['q' + str(todayQuarter)]

            sum_table['sum_salary'] += tmp_basic['sum_salary']
            sum_table['sum_basicSalary'] += tmp_basic['sum_basicSalary']
            sum_table['sum_bettingSalary'] += tmp_basic['sum_bettingSalary']
            sum_table['sum_cumulateIncentive'] += cumulateIncentive
            sum_table['sum_achieveIncentive'] += tmp_before['sum_achieveIncentive']
            sum_table['achieveIncentive'] += tmp_current['achieveIncentive']
            sum_table['sum_achieveAward'] += tmp_basic['sum_achieveAward']
            sum_table['achieveAward'] += tmp_current['achieveAward']
            sum_table['compareIncentive'] += (cumulateIncentive + tmp_basic['sum_achieveAward']) - tmp_basic['sum_bettingSalary']

            table.append({
                'empId': emp['empId'],
                'empPosition': tmp_basic['empPosition'],
                'empName': tmp_basic['empName'],
                'achieveRatio': achieveRatio,
                'sum_salary': tmp_basic['sum_salary'],
                'sum_basicSalary': tmp_basic['sum_basicSalary'],
                'sum_bettingSalary': tmp_basic['sum_bettingSalary'],
                'creditRatio': creditRatio,
                'ACC': ACC,
                'cumulateIncentive': cumulateIncentive,
                'before_achieve': tmp_before['sum_achieveIncentive'],
                'achieveIncentive': tmp_current['achieveIncentive'],
                'achieveAward': tmp_current['achieveAward'],
                'sum_achieveAward': tmp_basic['sum_achieveAward'],
                'compareIncentive': (cumulateIncentive + tmp_basic['sum_achieveAward']) - tmp_basic['sum_bettingSalary'],
            })

    context = {
        'todayYear': todayYear,
        'todayQuarter': todayQuarter,
        'beforeQuarter': beforeQuarter,
        'nextMonth': nextMonth,
        'table': table,
        'sum_table': sum_table,
    }

    return render(request, 'sales/viewincentiveall.html', context)


@login_required
def show_incentives(request):
    if request.method == "POST":
        todayYear = datetime.today().year
        if request.POST["quarter"] != '':
            quarter = int(request.POST["quarter"])
            empId = int(request.POST["empId"])
            salary = int(request.POST["salary"])
            betting = int(request.POST["betting"])
            modifyMode = request.POST["modifyMode"]
            employee = Employee.objects.get(Q(empId=empId))
            incentives = Incentive.objects.filter(Q(empId=empId) & Q(quarter=quarter))
            if incentives.first() != None:
                return HttpResponse("해당 분기에 이미 등록된 정보가 있습니다.")
            else:
                bettingSalary = salary * betting / 100.0
                basicSalary = salary - bettingSalary
                Incentive.objects.create(empId=employee, year=todayYear, quarter=quarter, salary=salary, bettingRatio=betting, basicSalary=basicSalary, bettingSalary=bettingSalary)
        else:
            modifyMode = 'Y'
    else:
        modifyMode = 'N'

    employee = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y'))
    context = {
        'employee': employee,
        'modifyMode': modifyMode,
    }
    return render(request, 'sales/showincentives.html', context)


@login_required
@csrf_exempt
def incentives_asjson(request):
    incentives = Incentive.objects.all()
    incentives = incentives.values('year', 'empId__empDeptName', 'empId__empName', 'quarter', 'salary', 'bettingRatio',
                                   'basicSalary', 'bettingSalary', 'achieveIncentive', 'achieveAward', 'incentiveId')

    structure = json.dumps(list(incentives), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def save_incentivetable(request):
    employee = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y'))
    achieveIncentive = request.GET.getlist('achieveIncentive')
    achieveAward = request.GET.getlist('achieveAward')
    incentiveId = request.GET.getlist('incentiveId')
    modifyMode = request.GET['modifyMode']

    for a, b, c in zip(incentiveId, achieveIncentive, achieveAward):
        incentive = Incentive.objects.get(incentiveId=a)
        incentive.achieveIncentive = b or 0
        incentive.achieveAward = c or 0
        incentive.save()

    context = {
        'employee': employee,
        'modifyMode': modifyMode,
    }
    return render(request, 'sales/showincentives.html', context)


@login_required
@csrf_exempt
@require_POST
def delete_incentive(request):
    if request.method == 'POST' and request.is_ajax():
        incentiveId = request.POST.get('incentiveId', None)
        Incentive.objects.filter(incentiveId=incentiveId).delete()
        return HttpResponse(json.dumps({'incentiveId': incentiveId}), content_type="application/json")


@login_required
@csrf_exempt
def change_incentive_all(request):
    revenues = Revenue.objects.all()

    for revenue in revenues:
        revenue.incentivePrice = cal_revenue_incentive(revenue.revenueId)[0]
        revenue.incentiveProfitPrice = cal_revenue_incentive(revenue.revenueId)[1]
        revenue.incentiveReason = cal_revenue_incentive(revenue.revenueId)[2]
        revenue.save()

    return HttpResponse('성공!')


@login_required
@csrf_exempt
def monthly_bill(request):
    if request.method == 'POST':
        todayYear = int(request.POST['searchYear'])
        todayMonth = 12
        if todayYear == datetime.today().year:
            todayYear = datetime.today().year
            todayMonth = datetime.today().month
    else:
        todayYear = datetime.today().year
        todayMonth = datetime.today().month

    if todayMonth in [1, 2, 3]:
        todayQuarter = 1
    elif todayMonth in [4, 5, 6]:
        todayQuarter = 2
    elif todayMonth in [7, 8, 9]:
        todayQuarter = 3
    elif todayMonth in [10, 11, 12]:
        todayQuarter = 4

    try:
        expenseDate = Expense.objects.filter(Q(expenseStatus='Y') & Q(expenseDate__year=todayYear) & Q(expenseDate__month=todayMonth)).aggregate(expenseDate=Max('expenseDate'))
        expenseDate = expenseDate['expenseDate']
    except:
        expenseDate = '-'

    # 2.월별 예상 손익 계산서 현황
    month_table = cal_monthlybill(todayYear)

    # 1. 해당 월 누적 손익 계산서 현황
    todayMonth_table = {'revenuePrice': 0, 'revenueProfitPrice': 0, 'cogs': 0, 'expenses': 0, 'profit': 0}
    for month in month_table:
        if month['name']=='매출액':
            for m in range(1, todayMonth+1):
                todayMonth_table['revenuePrice'] += month['month{}'.format(m)]
        if month['name']=='매출원가':
            for m in range(1, todayMonth+1):
                todayMonth_table['cogs'] += month['month{}'.format(m)]
        if month['name']=='GP':
            for m in range(1, todayMonth+1):
                todayMonth_table['revenueProfitPrice'] += month['month{}'.format(m)]
        if month['name']=='판관비':
            for m in range(1, todayMonth+1):
                todayMonth_table['expenses'] += month['month{}'.format(m)]
        if month['name']=='영업이익':
            for m in range(1, todayMonth+1):
                todayMonth_table['profit'] += month['month{}'.format(m)]
    if todayMonth == 12:
        expenseDetail = Expense.objects.filter(Q(expenseStatus='Y') &
                                               Q(expenseDate__gte='{}-01-01'.format(todayYear)) &
                                               Q(expenseDate__lt='{}-01-01'.format(todayYear+1))).exclude(expenseDept='전사').values('expenseGroup') \
            .annotate(expenseMoney__sum=Sum('expenseMoney')).annotate(expensePercent=Cast(F('expenseMoney__sum') * 100.0 / todayMonth_table['expenses'], FloatField())).order_by('-expenseMoney__sum')
        sum_expenseDetail = expenseDetail.aggregate(sum_expenseDetail=Sum('expenseMoney__sum'), sum_expensePercent=Sum('expensePercent'))
    else:
        expenseDetail = Expense.objects.filter(Q(expenseStatus='Y') &
                                               Q(expenseDate__gte='{}-01-01'.format(todayYear)) &
                                               Q(expenseDate__lt='{}-{}-01'.format(todayYear, todayMonth+1))).exclude(expenseDept='전사').values('expenseGroup') \
            .annotate(expenseMoney__sum=Sum('expenseMoney')).annotate(expensePercent=Cast(F('expenseMoney__sum') * 100.0 / todayMonth_table['expenses'], FloatField())).order_by('-expenseMoney__sum')
        sum_expenseDetail = expenseDetail.aggregate(sum_expenseDetail=Sum('expenseMoney__sum'), sum_expensePercent=Sum('expensePercent'))



    if todayYear < 2020:
        # 3.월별 예상 손익 계산서 현황
        businessAll, sum_businessAll = cal_profitloss(['인프라솔루션_임원', '영업1팀', '영업2팀', '인프라서비스'], todayYear)
        businessExecutives, sum_businessExecutives = cal_profitloss(['인프라솔루션_임원'], todayYear)
        businessSales1, sum_businessSales1 = cal_profitloss(['영업1팀'], todayYear)
        businessSales2, sum_businessSales2 = cal_profitloss(['영업2팀'], todayYear)
        businessInfra, sum_businessInfra = cal_profitloss(['인프라서비스'], todayYear)
        # 고객서비스부문
        serviceAll, sum_serviceAll = cal_profitloss(['고객서비스_임원', '솔루션지원팀', 'DB지원팀'], todayYear)
        serviceExecutives, sum_serviceExecutives = cal_profitloss(['고객서비스_임원'], todayYear)
        serviceSolution, sum_serviceSolution = cal_profitloss(['솔루션지원팀'], todayYear)
        serviceDB, sum_serviceDB = cal_profitloss(['DB지원팀'], todayYear)
        # 경영지원
        supportAll, sum_supportAll = cal_profitloss(['대표이사', '사장', '감사', '고문', '경영지원본부'], todayYear)
        # 전체
        unioneAll, sum_unioneAll = cal_profitloss(['인프라솔루션_임원', '영업1팀', '영업2팀', '인프라서비스', '고객서비스_임원', '솔루션지원팀', 'DB지원팀', '대표이사', '사장', '감사', '고문', '경영지원본부'], todayYear)

        business = [{'name': '1) 인프라솔루션사업부문', 'class': 'businessAll', 'expense': businessAll, 'sum': sum_businessAll, 'btn': 'Y'},
                     {'name': '① 임원', 'class': 'businessExecutives', 'expense': businessExecutives, 'sum': sum_businessExecutives, 'btn': 'N'},
                     {'name': '② 영업1팀', 'class': 'businessSales1', 'expense': businessSales1, 'sum': sum_businessSales1, 'btn': 'N'},
                     {'name': '③ 영업2팀', 'class': 'businessSales2',  'expense': businessSales2, 'sum': sum_businessSales2, 'btn': 'N'},
                     {'name': '④ 인프라서비스사업팀', 'class': 'businessInfra',  'expense': businessInfra, 'sum': sum_businessInfra, 'btn': 'N'},
                     {'name': '2) 고객서비스부문',  'class': 'serviceAll', 'expense': serviceAll, 'sum': sum_serviceAll, 'btn': 'Y'},
                     {'name': '① 임원', 'class': 'serviceExecutives',  'expense': serviceExecutives, 'sum': sum_serviceExecutives, 'btn': 'N'},
                     {'name': '② 솔루션지원팀', 'class': 'serviceSolution',  'expense': serviceSolution, 'sum': sum_serviceSolution, 'btn': 'N'},
                     {'name': '③ DB지원팀', 'class': 'serviceDB',  'expense': serviceDB, 'sum': sum_serviceDB, 'btn': 'N'},
                     {'name': '3) 경영지원', 'class': 'supportAll',  'expense': supportAll, 'sum': sum_supportAll, 'btn': 'N'},
                     {'name': '', 'class': 'unioneAll', 'sum': sum_unioneAll, 'btn': 'N'}
                     ]
    else:
        # 3.월별 예상 손익 계산서 현황
        # 인프라솔루션사업부
        businessAll, sum_businessAll = cal_profitloss(['인프라_부사장', '영업팀'], todayYear)
        businessExecutives, sum_businessExecutives = cal_profitloss(['인프라_부사장'], todayYear)
        businessSales1, sum_businessSales1 = cal_profitloss(['영업팀'], todayYear)
        # R&D 전략사업부
        strategyAll, sum_strategyAll = cal_profitloss(['R&D전략_이사', 'TA팀', 'AI Platform Labs'], todayYear)
        strategyExecutives, sum_strategyExecutives = cal_profitloss(['R&D전략_이사'], todayYear)
        strategyTA, sum_strategyTA = cal_profitloss(['TA팀'], todayYear)
        strategyAI, sum_strategyAI = cal_profitloss(['AI Platform Labs'], todayYear)
        # Platform Biz
        serviceAll, sum_serviceAll = cal_profitloss(['Platform Biz_이사', '솔루션팀', 'DB Expert팀'], todayYear)
        serviceExecutives, sum_serviceExecutives = cal_profitloss(['Platform Biz_이사'], todayYear)
        serviceSolution, sum_serviceSolution = cal_profitloss(['솔루션팀'], todayYear)
        serviceDB, sum_serviceDB = cal_profitloss(['DB Expert팀'], todayYear)
        # 경영지원
        supportAll, sum_supportAll = cal_profitloss(['대표이사', '사장', '감사', '고문', '경영지원본부'], todayYear)
        # 전체
        unioneAll, sum_unioneAll = cal_profitloss(['인프라_부사장', '영업팀', 'R&D전략_이사', 'TA팀', 'AI Platform Labs', 'Platform Biz_이사', '솔루션팀', 'DB Expert팀', '대표이사', '사장', '감사', '고문', '경영지원본부'], todayYear)

        business = [{'name': '1) 인프라솔루션사업부', 'class': 'businessAll', 'expense': businessAll, 'sum': sum_businessAll, 'btn': 'Y'},
                     {'name': '① 인프라_부사장', 'class': 'businessExecutives', 'expense': businessExecutives, 'sum': sum_businessExecutives, 'btn': 'N'},
                     {'name': '② 영업팀', 'class': 'businessSales1', 'expense': businessSales1, 'sum': sum_businessSales1, 'btn': 'N'},
                     {'name': '2) R&D 전략사업부', 'class': 'strategyAll', 'expense': strategyAll, 'sum': sum_strategyAll, 'btn': 'Y'},
                     {'name': '① R&D전략_이사', 'class': 'strategyExecutives', 'sum': sum_strategyExecutives, 'btn': 'N'},
                     {'name': '② TA팀', 'class': 'strategyTA', 'expense': strategyTA, 'sum': sum_strategyTA, 'btn': 'N'},
                     {'name': '③ AI Platform Labs', 'class': 'strategyAI', 'expense': strategyAI, 'sum': sum_strategyAI, 'btn': 'N'},
                     {'name': '3) Platform Biz', 'class': 'serviceAll', 'expense': serviceAll, 'sum': sum_serviceAll, 'btn': 'Y'},
                     {'name': '① Platform Biz_이사', 'class': 'serviceExecutives', 'expense': serviceExecutives, 'sum': sum_serviceExecutives, 'btn': 'N'},
                     {'name': '② 솔루션팀', 'class': 'serviceSolution', 'expense': serviceSolution, 'sum': sum_serviceSolution, 'btn': 'N'},
                     {'name': '③ DB Expert팀', 'class': 'serviceDB', 'expense': serviceDB, 'sum': sum_serviceDB, 'btn': 'N'},
                     {'name': '4) 경영지원', 'class': 'supportAll', 'expense': supportAll, 'sum': sum_supportAll, 'btn': 'N'},
                     {'name': '', 'class': 'unioneAll', 'sum': sum_unioneAll, 'btn': 'N'}
                    ]

    context = {
        'todayYear': todayYear,
        'todayMonth': todayMonth,
        'todayQuarter': str(todayQuarter) + 'Q',
        'today': datetime.today(),
        'before': datetime.today() - timedelta(days=180),
        'expenseDetail': expenseDetail,
        'sum_expenseDetail': sum_expenseDetail,
        'expenseDate': expenseDate,
        'todayMonth_table': todayMonth_table,
        'month_table': month_table,
        'business': business,
    }
    return render(request, 'sales/monthlybill.html', context)

@login_required
def view_incentiveall_pdf(request, year, quarter):
    todayYear = year

    # 조회 분기 (기본값은 현재 분기)
    todayQuarter = int(quarter)

    # 다음 월
    if todayQuarter == 4:
        nextMonth = 1
    else:
        nextMonth = todayQuarter * 3 + 1

    # 이전 분기
    if todayQuarter == 1:
        beforeQuarter = 0
    else:
        beforeQuarter = todayQuarter - 1

    emps = Incentive.objects.filter(
        Q(year=todayYear) &
        Q(quarter__lte=todayQuarter)
    ).values('empId').distinct()

    excludeEmps = Incentive.objects.filter(
        Q(year=todayYear) &
        Q(quarter=todayQuarter) &
        Q(salary=0)
    ).values('empId').distinct()

    basic = Incentive.objects.filter(
        Q(year=todayYear) &
        Q(quarter__lte=todayQuarter)
    ).values('empId', 'empId__empPosition__positionName', 'empId__empName').annotate(
        empPosition=F('empId__empPosition__positionName'),
        empName=F('empId__empName'),
        sum_salary=Sum('salary'),
        sum_basicSalary=Sum('basicSalary'),
        sum_bettingSalary=Sum('bettingSalary'),
        sum_achieveIncentive=Sum('achieveIncentive'),
        sum_achieveAward=Sum('achieveAward'),
    )

    if beforeQuarter:
        before = Incentive.objects.filter(
            Q(year=todayYear) &
            Q(quarter__lte=beforeQuarter)
        ).values('empId').annotate(
            sum_achieveIncentive=Sum('achieveIncentive'),
            sum_achieveAward=Sum('achieveAward'),
        )
    else:
        before = []

    current = Incentive.objects.filter(
        Q(year=todayYear) &
        Q(quarter=todayQuarter)
    ).values('empId', 'achieveIncentive', 'achieveAward')

    table = []
    sum_table = {
        'sum_salary': 0, 'sum_basicSalary': 0, 'sum_bettingSalary': 0,
        'sum_cumulateIncentive': 0, 'sum_achieveIncentive': 0,
        'achieveIncentive': 0, 'achieveAward': 0, 'sum_achieveAward': 0
    }

    for emp in emps:
        if emp not in excludeEmps:
            _, _, tmp_table3 = empIncentive(str(todayYear), int(emp['empId']))
            tmp_basic = basic.get(empId=emp['empId'])

            if beforeQuarter:
                tmp_before = before.get(empId=emp['empId'])
            else:
                tmp_before = {'sum_achieveIncentive': 0}
            tmp_current = current.get(empId=emp['empId'])

            achieveRatio = 0
            creditRatio = 0
            ACC = 0
            cumulateIncentive = 0

            for t in tmp_table3:
                if t['name'] == '목표 달성률':
                    achieveRatio = t['q' + str(todayQuarter)]
                if t['name'] == '인정률':
                    creditRatio = t['q' + str(todayQuarter)]
                if t['name'] == 'ACC':
                    ACC = t['q' + str(todayQuarter)]
                if t['name'] == '예상누적인센티브':
                    cumulateIncentive = t['q' + str(todayQuarter)]

            sum_table['sum_salary'] += tmp_basic['sum_salary']
            sum_table['sum_basicSalary'] += tmp_basic['sum_basicSalary']
            sum_table['sum_bettingSalary'] += tmp_basic['sum_bettingSalary']
            sum_table['sum_cumulateIncentive'] += cumulateIncentive
            sum_table['sum_achieveIncentive'] += tmp_before['sum_achieveIncentive']
            sum_table['achieveIncentive'] += tmp_current['achieveIncentive']
            sum_table['sum_achieveAward'] += tmp_basic['sum_achieveAward']
            sum_table['achieveAward'] += tmp_current['achieveAward']

            table.append({
                'empId': emp['empId'],
                'empPosition': tmp_basic['empPosition'],
                'empName': tmp_basic['empName'],
                'achieveRatio': achieveRatio,
                'sum_salary': tmp_basic['sum_salary'],
                'sum_basicSalary': tmp_basic['sum_basicSalary'],
                'sum_bettingSalary': tmp_basic['sum_bettingSalary'],
                'creditRatio': creditRatio,
                'ACC': ACC,
                'cumulateIncentive': cumulateIncentive,
                'before_achieve': tmp_before['sum_achieveIncentive'],
                'achieveIncentive': tmp_current['achieveIncentive'],
                'achieveAward': tmp_current['achieveAward'],
                'sum_achieveAward': tmp_basic['sum_achieveAward'],
                'compareIncentive': (cumulateIncentive + tmp_basic['sum_achieveAward']) - tmp_basic['sum_bettingSalary'],
            })

    context = {
        'todayYear': todayYear,
        'todayQuarter': quarter,
        'beforeQuarter': beforeQuarter,
        'nextMonth': nextMonth,
        'table': table,
        'sum_table': sum_table,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="incentive_{}분기.pdf"'.format(quarter)

    template = get_template('sales/viewincentiveallpdf.html')
    html = template.render(context, request)
    # create a pdf
    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@login_required
def view_salaryall(request, year):
    todayYear = str(year)
    emps = Incentive.objects.filter(year=todayYear).values('empId').distinct()
    table = []
    basic = Incentive.objects.filter(
        Q(year=todayYear)
    ).values('empId', 'empId__empPosition__positionName', 'empId__empName').annotate(
        empPosition=F('empId__empPosition__positionName'),
        empName=F('empId__empName'),
        sum_salary=Sum('salary'),
        sum_basicSalary=Sum('basicSalary'),
        sum_bettingSalary=Sum('bettingSalary'),
        sum_achieveIncentive=Sum('achieveIncentive'),
        sum_achieveAward=Sum('achieveAward'),
    )
    sum_table = {
        'sum_quarter1_bettingSalary': 0, 'sum_quarter2_bettingSalary': 0, 'sum_quarter3_bettingSalary': 0, 'sum_quarter4_bettingSalary': 0,
        'sum_quarter1_achieveIncentiveAward': 0, 'sum_quarter2_achieveIncentiveAward': 0,
        'sum_quarter3_achieveIncentiveAward': 0, 'sum_quarter4_achieveIncentiveAward': 0,
        'sum_quarter1_salaryIncreaseDecrease': 0, 'sum_quarter2_salaryIncreaseDecrease': 0,
        'sum_quarter3_salaryIncreaseDecrease': 0, 'sum_quarter4_salaryIncreaseDecrease': 0
    }
    for emp in emps:
        emp_quarter = {}
        for q in range(1, 5):
            tmp_quarter = basic.get(Q(empId=emp['empId']) & Q(quarter__lte=q))
            emp_quarter['empId'] = emp['empId']
            emp_quarter['empPosition'] = tmp_quarter['empPosition']
            emp_quarter['empName'] = tmp_quarter['empName']
            emp_quarter['quarter{}_bettingSalary'.format(str(q))] = tmp_quarter['sum_bettingSalary']
            emp_quarter['quarter{}_achieveIncentiveAward'.format(str(q))] = tmp_quarter['sum_achieveIncentive'] + tmp_quarter['sum_achieveAward']
            emp_quarter['quarter{}_salaryIncreaseDecrease'.format(str(q))] = (tmp_quarter['sum_achieveIncentive'] + tmp_quarter['sum_achieveAward']) \
                                                                             - tmp_quarter['sum_bettingSalary']

        sum_table['sum_quarter1_bettingSalary'] += emp_quarter['quarter1_bettingSalary']
        sum_table['sum_quarter2_bettingSalary'] += emp_quarter['quarter2_bettingSalary']
        sum_table['sum_quarter3_bettingSalary'] += emp_quarter['quarter3_bettingSalary']
        sum_table['sum_quarter4_bettingSalary'] += emp_quarter['quarter4_bettingSalary']
        sum_table['sum_quarter1_achieveIncentiveAward'] += emp_quarter['quarter1_achieveIncentiveAward']
        sum_table['sum_quarter2_achieveIncentiveAward'] += emp_quarter['quarter2_achieveIncentiveAward']
        sum_table['sum_quarter3_achieveIncentiveAward'] += emp_quarter['quarter3_achieveIncentiveAward']
        sum_table['sum_quarter4_achieveIncentiveAward'] += emp_quarter['quarter4_achieveIncentiveAward']
        sum_table['sum_quarter1_salaryIncreaseDecrease'] += emp_quarter['quarter1_salaryIncreaseDecrease']
        sum_table['sum_quarter2_salaryIncreaseDecrease'] += emp_quarter['quarter2_salaryIncreaseDecrease']
        sum_table['sum_quarter3_salaryIncreaseDecrease'] += emp_quarter['quarter3_salaryIncreaseDecrease']
        sum_table['sum_quarter4_salaryIncreaseDecrease'] += emp_quarter['quarter4_salaryIncreaseDecrease']

        table.append(emp_quarter)

    context = {
        'todayYear': todayYear,
        'table': table,
        'sum_table': sum_table
    }
    return render(request, 'sales/viewsalaryall.html', context)


@login_required
def view_salaryall_pdf(request, year):
    todayYear = str(year)
    emps = Incentive.objects.filter(Q(year=year)).values('empId').distinct()
    table = []
    basic = Incentive.objects.filter(
        Q(year=todayYear)
    ).values('empId', 'empId__empPosition__positionName', 'empId__empName').annotate(
        empPosition=F('empId__empPosition__positionName'),
        empName=F('empId__empName'),
        sum_salary=Sum('salary'),
        sum_basicSalary=Sum('basicSalary'),
        sum_bettingSalary=Sum('bettingSalary'),
        sum_achieveIncentive=Sum('achieveIncentive'),
        sum_achieveAward=Sum('achieveAward'),
    )
    sum_table = {
        'sum_quarter1_bettingSalary': 0, 'sum_quarter2_bettingSalary': 0,
        'sum_quarter3_bettingSalary': 0, 'sum_quarter4_bettingSalary': 0,
        'sum_quarter1_achieveIncentiveAward': 0, 'sum_quarter2_achieveIncentiveAward': 0,
        'sum_quarter3_achieveIncentiveAward': 0, 'sum_quarter4_achieveIncentiveAward': 0,
        'sum_quarter1_salaryIncreaseDecrease': 0, 'sum_quarter2_salaryIncreaseDecrease': 0,
        'sum_quarter3_salaryIncreaseDecrease': 0, 'sum_quarter4_salaryIncreaseDecrease': 0
    }
    for emp in emps:
        emp_quarter = {}
        for q in range(1, 5):
            tmp_quarter = basic.get(Q(empId=emp['empId']) & Q(quarter__lte=q))
            emp_quarter['empId'] = emp['empId']
            emp_quarter['empPosition'] = tmp_quarter['empPosition']
            emp_quarter['empName'] = tmp_quarter['empName']
            emp_quarter['quarter{}_bettingSalary'.format(str(q))] = tmp_quarter['sum_bettingSalary']
            emp_quarter['quarter{}_achieveIncentiveAward'.format(str(q))] = tmp_quarter['sum_achieveIncentive'] + \
                                                                            tmp_quarter['sum_achieveAward']
            emp_quarter['quarter{}_salaryIncreaseDecrease'.format(str(q))] = (tmp_quarter['sum_achieveIncentive'] +
                                                                              tmp_quarter['sum_achieveAward']) - \
                                                                             tmp_quarter['sum_bettingSalary']

        sum_table['sum_quarter1_bettingSalary'] += emp_quarter['quarter1_bettingSalary']
        sum_table['sum_quarter2_bettingSalary'] += emp_quarter['quarter2_bettingSalary']
        sum_table['sum_quarter3_bettingSalary'] += emp_quarter['quarter3_bettingSalary']
        sum_table['sum_quarter4_bettingSalary'] += emp_quarter['quarter4_bettingSalary']
        sum_table['sum_quarter1_achieveIncentiveAward'] += emp_quarter['quarter1_achieveIncentiveAward']
        sum_table['sum_quarter2_achieveIncentiveAward'] += emp_quarter['quarter2_achieveIncentiveAward']
        sum_table['sum_quarter3_achieveIncentiveAward'] += emp_quarter['quarter3_achieveIncentiveAward']
        sum_table['sum_quarter4_achieveIncentiveAward'] += emp_quarter['quarter4_achieveIncentiveAward']
        sum_table['sum_quarter1_salaryIncreaseDecrease'] += emp_quarter['quarter1_salaryIncreaseDecrease']
        sum_table['sum_quarter2_salaryIncreaseDecrease'] += emp_quarter['quarter2_salaryIncreaseDecrease']
        sum_table['sum_quarter3_salaryIncreaseDecrease'] += emp_quarter['quarter3_salaryIncreaseDecrease']
        sum_table['sum_quarter4_salaryIncreaseDecrease'] += emp_quarter['quarter4_salaryIncreaseDecrease']

        table.append(emp_quarter)

    context = {
        'todayYear': todayYear,
        'table': table,
        'sum_table': sum_table
    }
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{}년도 급여증감현황.pdf"'.format(year)

    template = get_template('sales/viewsalaryallpdf.html')
    html = template.render(context, request)
    # create a pdf
    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


def view_incentive_pdf(request, year, empId):
    year = str(year)
    if int(year) <= 2019:
        # 2019년 정책 (팀별 목표, 팀별 매출)
        empName = Employee.objects.get(empId=empId).empName
        empDeptName = IncentiveDept.objects.get(empId=empId, year=year).deptName
        incentive = Incentive.objects.filter(Q(empId=empId) & Q(year=year))
        if not incentive:
            msg = '인센티브 산출에 필요한 개인 정보가 없습니다.'
            return render(request, 'sales/viewincentive.html', {'msg': msg, 'empName': empName, 'empId': empId, 'year': year})
        goal = Goal.objects.filter(Q(empDeptName=empDeptName) & Q(year=year))
        if not goal:
            msg = '인센티브 산출에 필요한 목표 정보가 없습니다.'
            return render(request, 'sales/viewincentive.html', {'msg': msg, 'empName': empName, 'empId': empId, 'year': year})
        table1, table2, table3 = empIncentive(year, empId)
        table4, sumachieveIncentive, sumachieveAward, GPachieve, newCount, overGp, incentiveRevenues = award(
            year, empDeptName, table2, goal.first(), empName, incentive, empId
        )

        context = {
            'empId': empId,
            'empName': empName,
            'table1': table1,
            'table2': table2,
            'table3': table3,
            'table4': table4,
            'sumachieveIncentive': sumachieveIncentive,
            'sumachieveAward': sumachieveAward,
            'GPachieve': GPachieve,
            'newCount': newCount,
            'overGp': overGp,
            'incentiveRevenues': incentiveRevenues,
            'year': year,
        }
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}님인센티브현황.pdf"'.format(empId)

        template = get_template('sales/viewincentivepdf.html')
        html = template.render(context, request)
        # create a pdf
        pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
        # if error then show some funy view
        if pisaStatus.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response
    else:
        # 2020년 정책
        empName = Employee.objects.get(empId=empId).empName
        empDeptName = IncentiveDept.objects.get(empId=empId, year=year).deptName
        incentive = Incentive.objects.filter(Q(empId=empId) & Q(year=year))
        if not incentive:
            msg = '인센티브 산출에 필요한 개인 정보가 없습니다.'
            return render(request, 'sales/viewincentive.html', {'msg': msg, 'empName': empName, 'empId': empId, 'year': year})
        goal = Goal.objects.filter(Q(empDeptName=empDeptName) & Q(year=year))
        if not goal:
            msg = '인센티브 산출에 필요한 목표 정보가 없습니다.'
            return render(request, 'sales/viewincentive.html', {'msg': msg, 'empName': empName, 'empId': empId, 'year': year})
        table1, table2, table3 = empIncentive(year, empId)
        table4, sumachieveIncentive, sumachieveAward, GPachieve, newCount, overGp, incentiveRevenues = award(
            year, empDeptName, table2, goal.first(), empName, incentive, empId
        )

        context = {
            'empId': empId,
            'empName': empName,
            'table1': table1,
            'table2': table2,
            'table3': table3,
            'table4': table4,
            'sumachieveIncentive': sumachieveIncentive,
            'sumachieveAward': sumachieveAward,
            'GPachieve': GPachieve,
            'newCount': newCount,
            'overGp': overGp,
            'incentiveRevenues': incentiveRevenues,
            'year': year,
        }
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}님인센티브현황.pdf"'.format(empId)

        template = get_template('sales/viewincentivepdf.html')
        html = template.render(context, request)
        # create a pdf
        pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
        # if error then show some funy view
        if pisaStatus.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response



def save_contract_files(request, contractId):
    if request.method == 'POST':

        # 1. 첨부파일 업로드 정보
        jsonFile = json.loads(request.POST['jsonFile'])
        filesInfo = {}  # {fileName1: fileSize1, fileName2: fileSize2, ...}
        filesName = []  # [fileName1, fileName2, ...]
        for i in jsonFile:
            filesInfo[i['fileName']] = i['fileSize']
            filesName.append(i['fileName'])

        # 2. 업로드 된 파일 중, 화면에서 삭제하지 않은 것만 등록
        for f in request.FILES.getlist('files'):
            if f.name in filesName:
                Contractfile.objects.create(
                    contractId=Contract.objects.get(contractId=contractId),
                    fileCategory=request.POST['fileType'],
                    fileName=f.name,
                    fileSize=filesInfo[f.name][:-2],
                    file=f,
                    uploadEmp=request.user.employee,
                    uploadDatetime=datetime.now(),
                )
        return redirect('sales:viewcontract', contractId)


def save_purchase_files(request, contractId):
    if request.method == 'POST':
        fileType = request.POST['fileType']
        contract = Contract.objects.get(contractId=contractId)

        for fileKey in request.FILES.keys():
            tempJsonFile = json.loads(request.POST[fileKey.replace('purchaseFiles', 'jsonFile')])
            company = ''
            tempFilesInfo = {}
            tempFilesName = []
            tempBool = True
            for i in tempJsonFile:
                if tempBool:
                    company = Company.objects.get(companyNameKo=i['companyName'])
                    tempBool = False
                tempFilesInfo[i['fileName']] = i['fileSize']
                tempFilesName.append(i['fileName'])

            for f in request.FILES.getlist(fileKey):
                if f.name in tempFilesName:
                    Purchasefile.objects.create(
                        contractId=contract,
                        purchaseCompany=company,
                        fileCategory=fileType,
                        fileName=f.name,
                        fileSize=tempFilesInfo[f.name][:-2],
                        file=f,
                        uploadEmp=request.user.employee,
                        uploadDatetime=datetime.now(),
                    )
        return redirect('sales:viewcontract', contractId)


@login_required
@csrf_exempt
def contract_details(request):
    contractId = request.POST['contractId']
    table = request.POST['table']
    classNumber = request.POST['classNumber']
    if table == 'a':
        purchaseTypes = Purchasetypea.objects.all()
    elif table == 'b':
        purchaseTypes = Purchasetypeb.objects.all()
    elif table == 'c':
        purchaseTypes = Purchasetypec.objects.all()
    elif table == 'd':
        purchaseTypes = Purchasetyped.objects.all()

    purchaseTypes = purchaseTypes.filter(Q(contractId=contractId) & Q(classNumber=classNumber))

    if table == 'a':
        purchaseTypes = purchaseTypes.values('companyName', 'contents', 'price', 'typeId')
    elif table == 'b':
        purchaseTypes = purchaseTypes.values('classification', 'times', 'sites', 'units', 'price', 'typeId')
    elif table == 'c':
        purchaseTypes = purchaseTypes.values('classification', 'contents', 'price', 'typeId')
    elif table == 'd':
        purchaseTypes = purchaseTypes.values('contractNo', 'contractStartDate', 'contractEndDate', 'price', 'typeId')

    structure = json.dumps(list(purchaseTypes), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_ordernoti_pdf(request, contractId):
    context = viewContract(request, contractId)
    today = datetime.today()
    context['today'] = today
    context['result'] = round((context['contract'].profitRatio - 15.0), 3)
    context['summary'] = summary(contractId)
    context['revenueItem'] = Contractitem.objects.filter(Q(contractId=contractId))
    context['sumRevenueItem'] = context['revenueItem'].aggregate(Sum('itemPrice'))
    context['purchaseItem'] = Purchasecontractitem.objects.filter(Q(contractId=contractId))
    context['sumPurchaseItem'] = context['purchaseItem'].aggregate(Sum('itemPrice'))

    for i in range(1, 9):
        context['class{}'.format(str(i))], context['sum_class{}'.format(str(i))] = detailPurchase(contractId, i)

    # billing schedule
    purchases = context['purchases']
    revenues = context['revenues']

    if len(purchases) > 0 or len(revenues) > 0:
        if len(purchases) == 0:
            pMinYear = {'predictBillingDate__year__min': date(2999, 12, 31)}
            pMaxYear = {'predictBillingDate__year__max': date(1999, 12, 31)}
        else:
            pMinYear = purchases.aggregate(Min('predictBillingDate__year'))
            pMaxYear = purchases.aggregate(Max('predictBillingDate__year'))
        if len(revenues) == 0:
            rMinYear = {'predictBillingDate__year__min': date(2999, 12, 31)}
            rMaxYear = {'predictBillingDate__year__max': date(1999, 12, 31)}
        else:
            rMinYear = revenues.aggregate(Min('predictBillingDate__year'))
            rMaxYear = revenues.aggregate(Max('predictBillingDate__year'))

        if pMinYear['predictBillingDate__year__min'] < rMinYear['predictBillingDate__year__min']:
            minYear = pMinYear
        else:
            minYear = rMinYear
        if pMaxYear['predictBillingDate__year__max'] > rMaxYear['predictBillingDate__year__max']:
            maxYear = pMaxYear
        else:
            maxYear = rMaxYear

        yearList = []
        for y in range(minYear['predictBillingDate__year__min'].year, maxYear['predictBillingDate__year__max'].year+1):
            yearList.append(y)

        monthList = []
        for y in yearList:
            dateList = []
            for d in range(1, 13):
                dateList.append('{}-{}'.format(y, str(d).zfill(2)))
            monthList.append(dateList)
        context['yearList'] = monthList

        # billingSchedule
        groupPurchases = purchases.values('predictBillingDate__year', 'predictBillingDate__month', 'purchaseCompany').annotate(price=Sum('purchasePrice'))
        groupRevenues = revenues.values('predictBillingDate__year', 'predictBillingDate__month', 'revenueCompany').annotate(price=Sum('revenuePrice'))
        groupMonthPurchases = purchases.values('predictBillingDate__year', 'predictBillingDate__month').annotate(price=Sum('purchasePrice'))
        groupMonthRevenues = revenues.values('predictBillingDate__year', 'predictBillingDate__month').annotate(price=Sum('revenuePrice'))
        companyPurchases = purchases.values_list('purchaseCompany__companyName', flat=True).distinct()
        companyRevenues = revenues.values_list('revenueCompany__companyName', flat=True).distinct()

        pBillingSchedule = []
        sumpBillingSchedule = []
        rBillingSchedule = []
        sumrBillingSchedule = []

        for month in monthList:
            sumrBillingSchedule.append(
                {'list': month, 'year': month[0][:4], 'name': 'sum', '1': '', '2': '', '3': '', '4': '', '5': '', '6': '', '7': '', '8': '', '9': '', '10': '', '11': '', '12': '', 'sum': 0})
            sumpBillingSchedule.append(
                {'list': month, 'year': month[0][:4], 'name': 'sum', '1': '', '2': '', '3': '', '4': '', '5': '', '6': '', '7': '', '8': '', '9': '', '10': '', '11': '', '12': '', 'sum': 0})
            for c in list(set(companyPurchases)):
                pBillingSchedule.append({'list': month, 'year': month[0][:4], 'name': c, '1': '', '2': '', '3': '', '4': '', '5': '', '6': '', '7': '', '8': '', '9': '', '10': '', '11': '', '12': '', 'sum': 0})
            for c in list(set(companyRevenues)):
                rBillingSchedule.append({'list': month, 'year': month[0][:4], 'name': c, '1': '', '2': '', '3': '', '4': '', '5': '', '6': '', '7': '', '8': '', '9': '', '10': '', '11': '', '12': '', 'sum': 0})
        # 매입
        for group in groupPurchases:
            for schedule in pBillingSchedule:
                if schedule['year'] == str(group['predictBillingDate__year']) and schedule['name'] == group['purchaseCompany']:
                    if schedule[str(group['predictBillingDate__month'])]:
                        schedule[str(group['predictBillingDate__month'])] += group['price']
                    else:
                        schedule[str(group['predictBillingDate__month'])] = group['price']
                    schedule['sum'] += group['price']
        for groupMonth in groupMonthPurchases:
            for sumBilling in sumpBillingSchedule:
                if sumBilling['year'] == str(groupMonth['predictBillingDate__year']):
                    if sumBilling[str(groupMonth['predictBillingDate__month'])]:
                        sumBilling[str(groupMonth['predictBillingDate__month'])] += groupMonth['price']
                    else:
                        sumBilling[str(groupMonth['predictBillingDate__month'])] = groupMonth['price']
                    sumBilling['sum'] += groupMonth['price']
        # 매출
        for group in groupRevenues:
            for schedule in rBillingSchedule:
                if schedule['year'] == str(group['predictBillingDate__year']) and schedule['name'] == group['revenueCompany']:
                    if schedule[str(group['predictBillingDate__month'])]:
                        schedule[str(group['predictBillingDate__month'])] += group['price']
                    else:
                        schedule[str(group['predictBillingDate__month'])] = group['price']
                    schedule['sum'] += group['price']
        for groupMonth in groupMonthRevenues:
            for sumBilling in sumrBillingSchedule:
                if sumBilling['year'] == str(groupMonth['predictBillingDate__year']):
                    if sumBilling[str(groupMonth['predictBillingDate__month'])]:
                        sumBilling[str(groupMonth['predictBillingDate__month'])] += groupMonth['price']
                    else:
                        sumBilling[str(groupMonth['predictBillingDate__month'])] = groupMonth['price']
                    sumBilling['sum'] += groupMonth['price']
        context['pBillingSchedule'] = pBillingSchedule
        context['sumpBillingSchedule'] = sumpBillingSchedule
        context['rBillingSchedule'] = rBillingSchedule
        context['sumrBillingSchedule'] = sumrBillingSchedule

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{}_수주통보서.pdf"'.format(contractId)
    template = get_template('sales/viewordernotipdf.html')
    html = template.render(context, request)

    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@login_required
@csrf_exempt
def view_confirm_pdf(request, contractId):
    if request.method == 'POST':
        contract = Contract.objects.get(contractId=contractId)
        print(request.POST)
        confirmDate = request.POST['confirmDate']
        confirmCustomer = request.POST['confirmCustomer']
        confirmContents = request.POST['confirmContents']
        confirmComment = request.POST['confirmComment']
        if confirmDate:
            contract.confirmDate = confirmDate
        if confirmCustomer:
            contract.confirmCustomer = confirmCustomer
        if confirmContents:
            contract.confirmContents = confirmContents
        if confirmComment:
            contract.confirmComment = confirmComment
        contract.save()
        context = {
            'contract': contract
        }
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}_수주통보서.pdf"'.format(contractId)
        template = get_template('sales/viewconfirmpdf.html')
        html = template.render(context, request)

        pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
        if pisaStatus.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response
    else:
        contract = Contract.objects.get(contractId=contractId)
        context = {
            'contract': contract
        }
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{}_수주통보서.pdf"'.format(contractId)
        template = get_template('sales/viewconfirmpdf.html')
        html = template.render(context, request)

        pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
        if pisaStatus.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response


@login_required
def save_customer(request):
    companyName = Company.objects.get(companyName=request.POST['customerCompany'])
    customerName = request.POST['customerName']
    if request.POST['customerDept']:
        customerDept = request.POST['customerDept']
    else:
        customerDept = None

    if request.POST['customerPhone']:
        customerPhone = request.POST['customerPhone']
    else:
        customerPhone = None

    if request.POST['customerEmail']:
        customerEmail = request.POST['customerEmail']
    else:
        customerEmail = None

    if Customer.objects.filter(companyName=companyName, customerName__icontains=customerName).first():
        result = 'N'
    else:
        Customer.objects.create(companyName=companyName, customerName=customerName, customerDeptName=customerDept, customerPhone=customerPhone, customerEmail=customerEmail)
        result = 'Y'
    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')

@login_required
def save_category(request):
    mainCategory = request.POST['mainCategory']
    subCategory = request.POST['subCategory']

    if Category.objects.filter(mainCategory=mainCategory, subCategory=subCategory).first():
        result = 'N'
    else:
        Category.objects.create(mainCategory=mainCategory, subCategory=subCategory)
        result = 'Y'
    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def maincategory_asjson(request):
    contractId = request.POST['contractId']
    if contractId:
        items = Contractitem.objects.filter(contractId=contractId).values('mainCategory', 'subCategory')
        maincategory = Category.objects.all().values('mainCategory').distinct().order_by('mainCategory')
        jsonList = []
        jsonList.append(list(maincategory))
        jsonList.append(list(items))
    else:
        maincategory = Category.objects.all().values('mainCategory').distinct().order_by('mainCategory')
        jsonList = list(maincategory)
    structure = json.dumps(jsonList, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def classification_asjson(request):
    category = request.POST['classification']
    contractId = request.POST['contractId']
    if contractId:
        jsonList = []
        costcontents = Purchasecategory.objects.filter(purchaseType=category).values('categoryName').distinct()
        jsonList.append(list(costcontents))
        if category == '매입_미접수':
            data = Cost.objects.filter(contractId=contractId).values('costCompany')
        elif category == 'classificationB':
            data = Purchasetypeb.objects.filter(Q(contractId=contractId) & Q(classNumber=5)).values('classification')
        elif category == 'classificationC1':
            data = Purchasetypec.objects.filter(Q(contractId=contractId) & Q(classNumber=6)).values('classification')
        elif category == 'classificationC2':
            data = Purchasetypec.objects.filter(Q(contractId=contractId) & Q(classNumber=8)).values('classification')
        jsonList.append(list(data))
    else:
        costcontents = Purchasecategory.objects.filter(purchaseType=category).values('categoryName').distinct()
        jsonList = list(costcontents)
    structure = json.dumps(jsonList, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')

@login_required
def change_contract_step(request, contractStep, contractId):
    contract = Contract.objects.get(contractId=contractId)
    contract.contractStep = contractStep

    if contractStep == 'Firm':
        # 관리번호 자동생성
        today = str(datetime.now())[:10]
        yy = str(today)[2:4]
        mm = str(today)[5:7]
        count = [int(code[-3:]) for code in Contract.objects.filter(Q(contractCode__startswith=yy)).values_list('contractCode', flat=True)]
        count.append(0)
        codeNumber = str(max(count) + 1).zfill(3)
        contract.contractCode = yy + mm + '-' + codeNumber
    elif contractStep == 'Drop':
        # 매출, 매입, 원가, 하도급 삭제(매출 발행 또는 매입 접수 항목은 삭제하지 않음.)
        Revenue.objects.filter(Q(contractId=contract) & (Q(billingDate__isnull=True) & Q(depositDate__isnull=True))).delete()
        Purchase.objects.filter(Q(contractId=contract) & (Q(billingDate__isnull=True) & Q(withdrawDate__isnull=True))).delete()
        Cost.objects.filter(contractId=contract).delete()
        Purchasetypea.objects.filter(contractId=contract).delete()
        Purchasetypeb.objects.filter(contractId=contract).delete()
        Purchasetypec.objects.filter(contractId=contract).delete()
        Purchasetyped.objects.filter(contractId=contract).delete()
        # 관리번호 변경
        yy = str(datetime.now().year)[2:]
        mm = str(datetime.now().month).zfill(2)
        contract.contractCode = 'D-' + yy + mm + '-' + contractId

    contract.save()
    return redirect('sales:viewcontract', contractId)


@login_required
def save_classification(request):
    classification = request.POST['classification']
    categoryName = request.POST['categoryName']
    if Purchasecategory.objects.filter(purchaseType=classification, categoryName=categoryName).first():
        result = 'N'
    else:
        Purchasecategory.objects.create(purchaseType=classification, categoryName=categoryName)
        result = 'Y'
    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def calculate_billing(request):
    try:
        company = request.POST['company']
        date = request.POST['date']
        times = int(request.POST['times'])
        price = int(request.POST['price'])
        profit = int(request.POST['profit'])
        billing = billing_schedule(company, date, times, price, profit)
        jsonList = []
        jsonList.append({'result': 'Y'})
        jsonList.append(billing)
    except Exception as e:
        print('Exception!!!!!:', e)
        jsonList = list({'result': 'N'})
    structure = json.dumps(jsonList, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_purchase_order(request, contractId, purchaseOrderCompanyName):
    contract = Contract.objects.get(contractId=contractId)
    purchaseOrderCompany = Company.objects.get(companyNameKo=purchaseOrderCompanyName)
    emp = request.user.employee

    purchaseIds = json.loads(request.POST['purchaseIds'])
    purchasePrice = Purchase.objects.filter(purchaseId__in=purchaseIds).aggregate(sum=Sum('purchasePrice'))['sum']
    formTitle = request.POST['purchaseOrderFormTitle']
    purchaseOrderForm = Purchaseorderform.objects.get(formTitle=formTitle)

    contentHtml = purchaseOrderForm.formHtml
    contentHtml = contentHtml.replace('매입처자동입력', purchaseOrderCompany.companyNameKo)
    if purchaseOrderCompany.ceo:
        contentHtml = contentHtml.replace('매입처대표이사자동입력', purchaseOrderCompany.ceo)
    else:
        contentHtml = contentHtml.replace('매입처대표이사자동입력', '')
    contentHtml = contentHtml.replace('매입처전화번호자동입력', '')
    if purchaseOrderCompany.companyNumber:
        contentHtml = contentHtml.replace('매입처사업자번호자동입력', purchaseOrderCompany.companyNumber)
    else:
        contentHtml = contentHtml.replace('매입처사업자번호자동입력', '')
    if purchaseOrderCompany.companyAddress:
        contentHtml = contentHtml.replace('매입처주소자동입력', purchaseOrderCompany.companyAddress)
    else:
        contentHtml = contentHtml.replace('매입처주소자동입력', '')
    contentHtml = contentHtml.replace('매입처수신자자동입력', '')
    contentHtml = contentHtml.replace('매입처직통자동입력', '')
    contentHtml = contentHtml.replace('매입처팩스자동입력', '')

    today = str(datetime.today())
    contentHtml = contentHtml.replace('발주일자동입력', today[:4] + '. ' + today[5:7] + '. ' + today[8:10])
    contentHtml = contentHtml.replace('영업대표자동입력', contract.empName + ' ' + contract.empId.empPosition.positionName)
    contentHtml = contentHtml.replace('영업대표직통자동입력', contract.empId.empPhone)
    contentHtml = contentHtml.replace('총발주금액자동입력별도', format(purchasePrice, ','))
    contentHtml = contentHtml.replace('총발주금액자동입력포함', format(int(purchasePrice*1.1), ','))

    purchaseOrder = Purchaseorder.objects.create(
        contractId=contract,
        purchaseCompany=purchaseOrderCompany,
        formId=purchaseOrderForm,
        writeEmp=emp,
        title='[유니원아이앤씨] ' + contract.contractName + '의 발주서를 송부드립니다.' ,
        contentHtml=contentHtml,
        writeDatetime=datetime.now(),
        modifyDatetime=datetime.now(),
    )
    for purchaseId in purchaseIds:
        purchaseInstance = Purchase.objects.get(purchaseId=purchaseId)
        purchaseInstance.purchaseOrder = purchaseOrder
        purchaseInstance.save()

    purchaseOrder.contentHtml = contentHtml.replace('발주번호자동입력', 'UN' + today[2:4] + today[5:7] + today[8:10] + '-' + str(purchaseOrder.orderId))
    purchaseOrder.save()

    return redirect('sales:modifypurchaseorder', purchaseOrder.orderId)


@login_required
def modify_purchase_order(request, orderId):
    purchaseOrder = Purchaseorder.objects.get(orderId=orderId)
    purchaseOrderCompany = purchaseOrder.purchaseCompany
    emp = purchaseOrder.writeEmp
    if request.method == 'POST':
        purchaseOrder.title = request.POST['title']
        purchaseOrder.contentHtml = request.POST['contentHtml']
        purchaseOrder.modifyDatetime = datetime.now()
        purchaseOrder.save()
        return redirect('sales:viewpurchaseorder', purchaseOrder.orderId)
    else:
        formTitle = purchaseOrder.formId.formTitle
        contentHtml = purchaseOrder.contentHtml
        context = {
            'purchaseOrderCompany': purchaseOrderCompany,
            'formTitle': formTitle,
            'contentHtml': contentHtml,
            'emp': emp,
            'purchaseOrder': purchaseOrder,
        }
        return render(request, 'sales/postpurchaseorder.html', context)


@login_required
def delete_purchase_order(request, orderId):
    purchaseOrder = Purchaseorder.objects.get(orderId=orderId)
    contractId = purchaseOrder.contractId.contractId
    purchaseOrder.delete()
    return redirect('sales:viewcontract', contractId)


@login_required
def view_purchase_order(request, orderId):
    # smtp 정보
    email = AdminEmail.objects.aggregate(Max('adminId'))
    email = AdminEmail.objects.filter(adminId=email['adminId__max']).first()

    purchaseOrder = Purchaseorder.objects.get(orderId=orderId)
    purchaseOrderFiles = Purchaseorderfile.objects.filter(purchaseOrder=purchaseOrder)
    relatedPurchaseEstimate = Relatedpurchaseestimate.objects.filter(purchaseOrder=purchaseOrder)
    purchaseFiles = Purchasefile.objects.filter(
        contractId=purchaseOrder.contractId,
        purchaseCompany=purchaseOrder.purchaseCompany
    )

    # 수주통보서 결재 완료 여부 확인 (최종 수주통보서의 상태가 완료된 건에 대해서만 발송 가능)
    ordernotis = Document.objects.filter(
        contractId=purchaseOrder.contractId,
        formId__formTitle='수주통보서',
    ).exclude(
        documentStatus='임시'
    ).order_by(
        '-draftDatetime'
    )
    if ordernotis:
        ordernoti = ordernotis.first()
        if ordernoti.documentStatus == '완료':
            isApproval = True
        else:
            isApproval = False
    else:
        isApproval = False

    context = {
        'purchaseOrder': purchaseOrder,
        'purchaseOrderFiles': purchaseOrderFiles,
        'relatedPurchaseEstimate': relatedPurchaseEstimate,
        'purchaseFiles': purchaseFiles,
        'email': email,
        'isApproval': isApproval,
    }
    return render(request, 'sales/viewpurchaseorder.html', context)


@login_required
def post_purchase_order_form(request):
    if request.method == 'POST':
        form = PurchaseorderformForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            HTML = request.POST['formHtml']
            HTML = HTML.replace('\'', '"')
            HTML = HTML.replace('\r', '')
            HTML = HTML.replace('\n', '')
            post.formHtml = HTML
            post.save()
        return redirect('sales:showpurchaseorderform')
    else:
        form = PurchaseorderformForm()
        context = {
            'form': form,
        }
        return render(request, 'sales/postpurchaseorderform.html', context)


@login_required
def delete_purchase_order_form(request, formId):
    purchaseOrderForm = Purchaseorderform.objects.get(formId=formId)
    purchaseOrderForm.delete()
    return redirect('sales:showpurchaseorderform')


@login_required
def show_purchase_order_form(request):
    if request.method == 'POST':
        form = PurchaseorderformForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.formHtml = request.POST['formHtml']
            post.save()
        return redirect('sales:postpurchaseorderform')
    else:
        form = PurchaseorderformForm()
        context = {
            'form': form,
        }
        return render(request, 'sales/showpurchaseorderform.html', context)


@login_required
def showpurchaseorderform_asjson(request):
    purchaseorderforms = Purchaseorderform.objects.all().values('formId', 'formNumber', 'formTitle', 'comment').order_by('formNumber')

    structure = json.dumps(list(purchaseorderforms), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def modify_purchase_order_form(request, formId):
    instance = Purchaseorderform.objects.get(formId=formId)
    if request.method == 'POST':
        form = PurchaseorderformForm(request.POST, instance=instance)
        if form.is_valid():
            post = form.save(commit=False)
            HTML = request.POST['formHtml']
            HTML = HTML.replace('\'', '"')
            HTML = HTML.replace('\r', '')
            HTML = HTML.replace('\n', '')
            post.formHtml = HTML
            post.save()
        return redirect('sales:showpurchaseorderform')
    else:
        form = PurchaseorderformForm(instance=instance)
        formHtml = instance.formHtml
        context = {
            'form': form,
            'formHtml': formHtml,
            'formId': instance.formId,
        }
        return render(request, 'sales/postpurchaseorderform.html', context)


@login_required
def upload_purchase_order_files(request, orderId):
    purchaseOrder = Purchaseorder.objects.get(orderId=orderId)
    for f in request.FILES.getlist('files'):
        Purchaseorderfile.objects.create(
            purchaseOrder=purchaseOrder,
            fileCategory='매입발주서',
            fileName=f.name,
            fileSize=round((f.size / 1048576), 2),
            uploadEmp=request.user.employee,
            uploadDatetime=datetime.now(),
            file=f,
        )
    return redirect('sales:viewpurchaseorder', orderId)


@login_required
def delete_purchase_order_file(request, fileId):
    purchaseOrderFile = Purchaseorderfile.objects.get(fileId=fileId)
    orderId = purchaseOrderFile.purchaseOrder.orderId
    purchaseOrderFile.delete()
    return redirect('sales:viewpurchaseorder', orderId)


@login_required
def upload_related_purchase_estimate(request, orderId):
    purchaseOrder = Purchaseorder.objects.get(orderId=orderId)
    purchaseFileIds = json.loads(request.POST['purchaseFileIds'])
    if purchaseFileIds:
        for fileId in purchaseFileIds:
            Relatedpurchaseestimate.objects.create(
                purchaseOrder=purchaseOrder,
                purchaseEstimate=Purchasefile.objects.get(fileId=fileId),
            )
    return redirect('sales:viewpurchaseorder', orderId)


@login_required
def delete_related_purchase_estimate(request, relatedId):
    relatedPurchaseEstimate = Relatedpurchaseestimate.objects.get(relatedId=relatedId)
    orderId = relatedPurchaseEstimate.purchaseOrder.orderId
    relatedPurchaseEstimate.delete()
    return redirect('sales:viewpurchaseorder', orderId)


@login_required
@csrf_exempt
def send_purchaseorder(request, orderId):
    if request.method == 'POST':
        orders = Purchaseorder.objects.get(orderId=orderId)
        purchaseorderfile = Purchaseorderfile.objects.filter(purchaseOrder=orderId)
        relatedpurchaseestimate = Relatedpurchaseestimate.objects.filter(purchaseOrder=orderId)
        empEmail = request.POST['empEmail']
        address = request.POST['address']

        empEmail ='{}@{}'.format(empEmail, address)
        if empEmail:
            result = mail_purchaseorder(empEmail, request.user.employee.empEmail, orders, purchaseorderfile, relatedpurchaseestimate)
        if result == 'Y':
            OrderLog.objects.create(
                empId=Employee(empId=request.user.employee.empId),
                toEmail=empEmail,
                orderId=orders,
                orderDatetime=datetime.now(),
            )
            orders.sendDatetime=datetime.now()
            orders.save()
            structure = json.dumps(result, cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')
        else:
            OrderLog.objects.create(
                empId=Employee(empId=request.user.employee.empId),
                toEmail=empEmail,
                orderDatetime=datetime.now(),
                orderId=orders,
                orderStatus='전송실패',
                orderError=result,
            )
            structure = json.dumps('N', cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')


@login_required
def show_purchaseorder(request):
    employees = Employee.objects.filter(Q(empDeptName__icontains='영업') & Q(empStatus='Y')).order_by('empDeptName', 'empRank')

    if request.method == "POST":
        startdate = request.POST["startdate"]
        enddate = request.POST["enddate"]
        contractName = request.POST["contractName"]
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        purchaseCompany = request.POST['purchaseCompany']

    else:
        startdate = ''
        enddate = ''
        contractName = ''
        empDeptName = '전체'
        empName = ''
        purchaseCompany = ''

    context = {
        'employees': employees,
        'startdate': startdate,
        'enddate': enddate,
        'contractName': contractName,
        'empDeptName': empDeptName,
        'empName': empName,
        'purchaseCompany': purchaseCompany,
    }

    return render(request, 'sales/showpurchaseorder.html', context)


@login_required
@csrf_exempt
def showpurchaseorder_asjson(request):
    startdate = request.POST["startdate"]
    enddate = request.POST["enddate"]
    contractName = request.POST["contractName"]
    empDeptName = request.POST['empDeptName']
    empName = request.POST['empName']
    purchaseCompany = request.POST['purchaseCompany']

    if request.user.employee.empPosition.positionName == '임원' or request.user.employee.empDeptName == '경영지원부' or request.user.is_staff:
        purchaseorders = Purchaseorder.objects.all()
    else:
        purchaseorders = Purchaseorder.objects.filter(Q(writeEmp=request.user.employee.empId))

    if startdate:
        purchaseorders = purchaseorders.filter(Q(modifyDatetime__gte=startdate))

    if enddate:
        purchaseorders = purchaseorders.filter(Q(modifyDatetime__lte=enddate))

    if contractName:
        purchaseorders = purchaseorders.filter(Q(contractId__contractName__icontains=contractName))

    if empDeptName != '전체':
        purchaseorders = purchaseorders.filter(Q(writeEmp__empDeptName__icontains=empDeptName))

    if empName != '전체':
        purchaseorders = purchaseorders.filter(Q(writeEmp__empName__icontains=empName))

    if purchaseCompany:
        purchaseorders = purchaseorders.filter(Q(purchaseCompany__companyNameKo__icontains=purchaseCompany))

    purchaseorders = purchaseorders.\
        values('modifyDatetime', 'writeEmp__empName', 'contractId__contractName', 'contractId__contractId', 'purchaseCompany', 'title', 'sendDatetime', 'orderId').order_by('-modifyDatetime')
    structure = json.dumps(list(purchaseorders), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def purchasemaincategory_asjson(request):
    contractId = request.POST['contractId']
    if contractId:
        items = Purchasecontractitem.objects.filter(contractId=contractId).values('mainCategory', 'subCategory')
        maincategory = Classification.objects.all().values('mainCategory').distinct()
        jsonList = []
        jsonList.append(list(maincategory))
        jsonList.append(list(items))
    else:
        maincategory = Classification.objects.all().values('mainCategory').distinct()
        jsonList = list(maincategory)
    structure = json.dumps(jsonList, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def clssificaion_asjson(request):
    mainCategory = request.POST['mainCategory']
    subcategory = Classification.objects.filter(mainCategory=mainCategory)
    json = serializers.serialize('json', subcategory)
    return HttpResponse(json, content_type='application/json')


@login_required
def save_purchasecategory(request):
    mainCategory = request.POST['mainCategory']
    subCategory = request.POST['subCategory']

    if Classification.objects.filter(mainCategory=mainCategory, subCategory=subCategory).first():
        result = 'N'
    else:
        Classification.objects.create(mainCategory=mainCategory, subCategory=subCategory)
        result = 'Y'
    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def comment_asjson(request):
    contractId = request.POST['contractId']
    # 의견
    comments = Contractcomment.objects.filter(Q(contractId=contractId)).order_by('created')
    comments = comments.values('commentId', 'author__empName', 'comment', 'created').annotate(
        viewer=Case(
            When(author=request.user.employee.empId, then=Value("Y")),
            default=Value("N"),
            output_field=CharField()
        )
    )
    structure = json.dumps(list(comments), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def save_comment(request):
    comment = request.POST['comment']
    contractId = request.POST['contractId']
    contract = Contract.objects.get(contractId=contractId)
    employee = Employee.objects.get(empId=request.user.employee.empId)
    # 댓글 추가
    comments = Contractcomment.objects.create(
        contractId=contract,
        author=employee,
        comment=comment,
        created=datetime.now()
    )
    # 알림 추가 부분
    # 알림을 받을 사람들
    alertEmpList = []
    # 계약의 영업대표 추가
    alertEmpList.append(contract.empId_id)
    # level=1 추가
    deptManager = Department.objects.get(deptLevel=0).deptManager.empId
    if deptManager:
        alertEmpList.append(deptManager)
    # 계약에 댓글을 달은 모든 사람 추가
    alertEmpList.extend(Contractcomment.objects.filter(contractId=contractId).values_list('author_id', flat=True).distinct())
    # 해당 댓글을 달은 사람 뺴기
    alertEmpList = list(set(alertEmpList)-{employee.empId})
    for emp in alertEmpList:
        Alert.objects.create(
            empId=Employee.objects.get(empId=emp),
            type="의견",
            text="'{}'님이 '{}'계약에 의견을 올렸습니다.".format(employee.empName, contract.contractName),
            url="/sales/viewcontract/{}/".format(contract.contractId)
        )

    comments = Contractcomment.objects.filter(commentId=comments.commentId)\
        .values('commentId', 'author__empName', 'comment', 'created').annotate(
        viewer=Case(
            When(author=request.user.employee.empId, then=Value("Y")),
            default=Value("N"),
            output_field=CharField()
        )
    )
    structure = json.dumps(list(comments), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def closing_revenues(request):
    context = {}
    return render(request, 'sales/closingrevenues.html', context)


@login_required
@csrf_exempt
def save_closingrevenues(request):
    closingrevenues = request.POST.getlist('revenuecheck')
    for revenueId in closingrevenues:
        # 매출 상태 변경 : Y-마감
        revenue = Revenue.objects.get(revenueId=revenueId)
        revenue.revenueStatus = 'Y'
        revenue.save()

    return redirect('sales:closingrevenues')


@login_required
@csrf_exempt
def closing_revenue_money(request):
    startdate = request.POST['transferStartDate']
    enddate = request.POST['transferEndDate']
    revenues = Revenue.objects.filter(revenueStatus='N')
    if startdate:
        revenues = revenues.filter(billingDate__gte=startdate)
    if enddate:
        revenues = revenues.filter(billingDate__lte=enddate)

    result = [
        {
            'revenuePrice': revenues.aggregate(Sum('revenuePrice'))['revenuePrice__sum'],
            'profitPrice': revenues.aggregate(Sum('revenueProfitPrice'))['revenueProfitPrice__sum'],
        }
    ]

    structure = json.dumps(list(result), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')