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
from django.db.models.functions import Coalesce
from hr.models import Employee
from .forms import ContractForm, GoalForm, PurchaseForm
from .models import Contract, Category, Revenue, Contractitem, Goal, Purchase
from service.models import Company, Customer, Servicereport
from django.db.models import Q
from datetime import datetime, timedelta
import pandas as pd
from xhtml2pdf import pisa
from service.functions import link_callback


def viewContract(contractId):
    # 계약, 세부정보, 매출, 매입, 계약서 명, 수주통보서 명
    contract = Contract.objects.get(contractId=contractId)
    items = Contractitem.objects.filter(contractId=contractId)
    revenues = Revenue.objects.filter(contractId=contractId)
    purchases = Purchase.objects.filter(contractId=contractId)
    services = Servicereport.objects.filter(contractId=contractId)
    contractPaper = str(contract.contractPaper).split('/')[-1]
    orderPaper = str(contract.orderPaper).split('/')[-1]

    sumRevenuePrice = revenues.aggregate(sum_revenuePrice=Coalesce(Sum('revenuePrice'), 0))['sum_revenuePrice']
    sumRevenueProfitPrice = revenues.aggregate(sum_revenueProfitPrice=Coalesce(Sum('revenueProfitPrice'), 0))['sum_revenueProfitPrice']
    if sumRevenueProfitPrice:
        sumRevenueProfitRatio = round(sumRevenueProfitPrice / sumRevenuePrice * 100)
    else:
        sumRevenueProfitRatio = 0
    sumPurchasePrice = purchases.aggregate(sum_purchasePrice=Coalesce(Sum('purchasePrice'), 0))['sum_purchasePrice']

    print(list(revenues.values('predictDepositDate')))

    # 연도 별 매출·이익 기여도
    yearList = list(set([i['predictBillingDate'].year for i in list(revenues.values('predictBillingDate'))]) |
                    set([i['predictBillingDate'].year for i in list(purchases.values('predictBillingDate'))]) |
                    set([i['predictDepositDate'].year for i in list(revenues.values('predictDepositDate')) if i['predictDepositDate']]) |
                    set([i['predictWithdrawDate'].year for i in list(purchases.values('predictWithdrawDate')) if i['predictWithdrawDate']]))
    yearSummary = []
    for year in yearList:
        temp = {
            'year': str(year),
            'revenuePrice': revenues.aggregate(revenuePrice=Coalesce(Sum('revenuePrice', filter=Q(predictBillingDate__year=year)), 0))['revenuePrice'],
            'purchasePrice': purchases.aggregate(purchasePrice=Coalesce(Sum('purchasePrice', filter=Q(predictBillingDate__year=year)), 0))['purchasePrice'],
            'revenueProfitPrice': revenues.aggregate(revenueProfitPrice=Coalesce(Sum('revenueProfitPrice', filter=Q(predictBillingDate__year=year)), 0))['revenueProfitPrice'],
            'depositPrice': revenues.aggregate(depositPrice=Coalesce(Sum('revenuePrice', filter=Q(depositDate__year=year)), 0))['depositPrice'],
            'withdrawPrice': purchases.aggregate(withdrawPrice=Coalesce(Sum('purchasePrice', filter=Q(withdrawDate__year=year)), 0))['withdrawPrice'],
        }
        if temp['revenuePrice'] == 0:
            temp['revenueProfitRatio'] = '-'
            temp['depositRatio'] = '-'
        else:
            temp['revenueProfitRatio'] = round(temp['revenueProfitPrice'] / temp['revenuePrice'] * 100)
            temp['depositRatio'] = round(temp['depositPrice'] / temp['revenuePrice'] * 100)
        if temp['purchasePrice'] == 0:
            temp['withdrawRatio'] = '-'
        else:
            temp['withdrawRatio'] = round(temp['withdrawPrice'] / temp['purchasePrice'] * 100)

        yearSummary.append(temp)

    yearSum = {
        'year': '합계',
        'revenuePrice': revenues.aggregate(revenuePrice=Coalesce(Sum('revenuePrice'), 0))['revenuePrice'],
        'purchasePrice': purchases.aggregate(purchasePrice=Coalesce(Sum('purchasePrice'), 0))['purchasePrice'],
        'revenueProfitPrice': revenues.aggregate(revenueProfitPrice=Coalesce(Sum('revenueProfitPrice'), 0))['revenueProfitPrice'],
        'depositPrice': revenues.aggregate(depositPrice=Coalesce(Sum('revenuePrice', filter=Q(depositDate__isnull=False)), 0))['depositPrice'],
        'withdrawPrice': purchases.aggregate(withdrawPrice=Coalesce(Sum('purchasePrice', filter=Q(withdrawDate__isnull=False)), 0))['withdrawPrice'],
    }
    if yearSum['revenuePrice'] == 0:
        yearSum['revenueProfitRatio'] = '-'
        yearSum['depositRatio'] = '-'
    else:
        yearSum['revenueProfitRatio'] = round(yearSum['revenueProfitPrice'] / yearSum['revenuePrice'] * 100)
        yearSum['depositRatio'] = round(yearSum['depositPrice'] / yearSum['revenuePrice'] * 100)
    if yearSum['purchasePrice'] == 0:
        yearSum['withdrawRatio'] = '-'
    else:
        yearSum['withdrawRatio'] = round(yearSum['withdrawPrice'] / yearSum['purchasePrice'] * 100)

    # 입출금정보 - 총 금액
    totalDeposit = revenues.filter(depositDate__isnull=False).aggregate(sum_deposit=Coalesce(Sum('revenuePrice'), 0))["sum_deposit"]
    totalWithdraw = purchases.filter(withdrawDate__isnull=False).aggregate(sum_withdraw=Coalesce(Sum('purchasePrice'), 0))["sum_withdraw"]
    if totalDeposit == 0:
        totalRatio = '-'
    else:
        totalRatio = round(totalWithdraw / totalDeposit * 100)

    # 입출금정보 - 매출
    companyDeposit = revenues \
        .values('revenueCompany__companyNameKo') \
        .annotate(sum_deposit=Coalesce(Sum('revenuePrice'), 0)) \
        .annotate(filter_deposit=Coalesce(Sum('revenuePrice', filter=Q(depositDate__isnull=False)), 0)) \
        .annotate(ratio_deposit=Coalesce(Sum('revenuePrice', filter=Q(depositDate__isnull=False)), 0) * 100 / Coalesce(Sum('revenuePrice'), 0))

    companyTotalDeposit = revenues.aggregate(
        total_sum_deposit=Coalesce(Sum('revenuePrice'), 0),
        total_filter_deposit=Coalesce(Sum('revenuePrice', filter=Q(depositDate__isnull=False)), 0),
    )

    if companyTotalDeposit['total_sum_deposit'] == 0:
        companyTotalDeposit['total_ratio_deposit'] = '-'
    else:
        companyTotalDeposit['total_ratio_deposit'] = round(companyTotalDeposit['total_filter_deposit'] / companyTotalDeposit['total_sum_deposit'] * 100)

    # 입출금정보 - 매입
    companyTotalWithdraw = purchases.aggregate(
        total_sum_withdraw=Coalesce(Sum('purchasePrice'), 0),
        total_filter_withdraw=Coalesce(Sum('purchasePrice', filter=Q(withdrawDate__isnull=False)), 0),
    )

    companyWithdraw = purchases \
        .values('purchaseCompany__companyNameKo') \
        .annotate(sum_withdraw=Coalesce(Sum('purchasePrice'), 0)) \
        .annotate(filter_withdraw=Coalesce(Sum('purchasePrice', filter=Q(withdrawDate__isnull=False)), 0)) \
        .annotate(ratio_withdraw=Coalesce(Sum('purchasePrice', filter=Q(withdrawDate__isnull=False)), 0) * 100 / Coalesce(Sum('purchasePrice'), 0)) \
        .annotate(sum_ratio_withdraw=Coalesce(Sum('purchasePrice'), 0)*100/companyTotalWithdraw['total_sum_withdraw'])

    if (companyTotalWithdraw['total_sum_withdraw']) == 0:
        companyTotalWithdraw['total_sum_withdraw'] = '0'
    else:
        companyTotalWithdraw['total_ratio_withdraw'] = round(companyTotalWithdraw['total_filter_withdraw'] / companyTotalWithdraw['total_sum_withdraw'] * 100)

    context = {
        'revenueId': '',
        'purchaseId': '',
        # 계약, 세부사항, 매출, 매입, 계약서 명, 수주통보서 명
        'contract': contract,
        'services': services,
        'items': items,
        'revenues': revenues.order_by('predictBillingDate'),
        'sumRevenuePrice': sumRevenuePrice,
        'sumRevenueProfitPrice': sumRevenueProfitPrice,
        'sumRevenueProfitRatio': sumRevenueProfitRatio,
        'purchases': purchases.order_by('predictBillingDate'),
        'sumPurchasePrice': sumPurchasePrice,
        'contractPaper': contractPaper,
        'orderPaper': orderPaper,
        # 연도 별 매출·이익 기여도
        'yearSummary': yearSummary,
        'yearSum': yearSum,
        # 입출금정보
        'totalDeposit': totalDeposit,
        'totalWithdraw': totalWithdraw,
        'totalRatio': totalRatio,
        'companyDeposit': companyDeposit,
        'companyTotalDeposit': companyTotalDeposit,
        'companyWithdraw': companyWithdraw,
        'companyTotalWithdraw': companyTotalWithdraw,
    }

    return context


def dailyReportRows(year, quarter=4, contractStep="F"):
    if year < 1000 or year > 9999:
        raise Exception('Please enter in year format.(4 digit integer)')
    if quarter not in [1, 2, 3, 4]:
        raise Exception('Please enter in quarter format.(1 to 4 integer)')
    if contractStep not in ['F', 'O', 'FO', 'OF']:
        raise Exception('Please enter in one of ["F", "O", "FO", "OF"].')

    dict_quarter = {"q1_start": "{}-01-01".format(year),
                    "q1_end": "{}-04-01".format(year), "q2_end": "{}-07-01".format(year),
                    "q3_end": "{}-10-01".format(year), "q4_end": "{}-01-01".format(year + 1)}

    goal = Goal.objects.filter(Q(year=year))
    if quarter == 1:
        teamGoal = goal.values('empDeptName')\
            .annotate(revenueTarget=F('salesq1'),
                      profitTarget=F('profitq1'))
        revenue = Revenue.objects.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end']))
    elif quarter == 2:
        teamGoal = goal.values('empDeptName')\
            .annotate(revenueTarget=F('salesq1') + F('salesq2'),
                      profitTarget=F('profitq1') + F('profitq2'))
        revenue = Revenue.objects.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q2_end']))
    elif quarter == 3:
        teamGoal = goal.values('empDeptName')\
            .annotate(revenueTarget=F('salesq1') + F('salesq2') + F('salesq3'),
                      profitTarget=F('profitq1') + F('profitq2') + F('profitq3'))
        revenue = Revenue.objects.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q3_end']))
    else:
        teamGoal = goal.values('empDeptName')\
            .annotate(revenueTarget=F('salesq1') + F('salesq2') + F('salesq3') + F('salesq4'),
                      profitTarget=F('profitq1') + F('profitq2') + F('profitq3') + F('profitq4'))
        revenue = Revenue.objects.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q4_end']))
    sumGoal = teamGoal.aggregate(revenueTargetSum=Sum('revenueTarget'), profitTargetSum=Sum('profitTarget'))

    if contractStep == 'F':
        revenue = revenue.filter(contractId__contractStep='Firm')
    elif contractStep == 'O':
        revenue = revenue.filter(contractId__contractStep='Opportunity')
    elif contractStep == 'FO' or contractStep == 'OF':
        revenue = revenue.filter(Q(contractId__contractStep='Opportunity') | Q(contractId__contractStep='Firm'))

    teamRevenue = list(revenue.values('contractId__empDeptName').annotate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice')))
    sumRevenue = revenue.aggregate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))

    rows = []
    teams = teamGoal.values('empDeptName').distinct()
    teams = [i['empDeptName'] for i in list(teams)]

    for team in teams:
        revenuePrice = [i['revenuePrice'] for i in teamRevenue if i['contractId__empDeptName'] == team] or [0]
        profitPrice = [i['revenueProfitPrice'] for i in teamRevenue if i['contractId__empDeptName'] == team] or [0]
        row = {
            'empDeptName': team[:4],
            'revenueTarget': teamGoal.filter(empDeptName=team)[0]['revenueTarget'],
            'profitTarget': teamGoal.filter(empDeptName=team)[0]['profitTarget'],
            'revenuePrice': revenuePrice[0],
            'profitPrice': profitPrice[0],
        }
        row['revenueRatio'] = round(row['revenuePrice'] / row['revenueTarget'] * 100)
        row['profitRatio'] = round(row['profitPrice'] / row['profitTarget'] * 100)
        rows.append(row)

    revenuePrice = sumRevenue['revenuePrice'] or 0
    profitPrice = sumRevenue['revenueProfitPrice'] or 0
    row = {
        'empDeptName': '합계',
        'revenueTarget': sumGoal['revenueTargetSum'],
        'profitTarget': sumGoal['profitTargetSum'],
        'revenuePrice': revenuePrice,
        'profitPrice': profitPrice,
    }
    row['revenueRatio'] = round(row['revenuePrice'] / row['revenueTarget'] * 100)
    row['profitRatio'] = round(row['profitPrice'] / row['profitTarget'] * 100)
    rows.append(row)

    return rows
