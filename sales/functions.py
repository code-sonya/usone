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
from .models import Contract, Category, Revenue, Contractitem, Goal, Purchase, Cost, Acceleration
from service.models import Company, Customer, Servicereport
from django.db.models import Q
from datetime import datetime, timedelta, date
import pandas as pd
from xhtml2pdf import pisa
from service.functions import link_callback


def viewContract(contractId):
    # 계약, 세부정보, 매출, 매입, 계약서 명, 수주통보서 명
    contract = Contract.objects.get(contractId=contractId)
    items = Contractitem.objects.filter(contractId=contractId)
    revenues = Revenue.objects.filter(contractId=contractId)
    purchases = Purchase.objects.filter(contractId=contractId)
    costs = Cost.objects.filter(contractId=contractId)
    services = Servicereport.objects.filter(Q(contractId=contractId) & Q(serviceStatus='Y') & (Q(empDeptName='DB지원팀') | Q(empDeptName='솔루션지원팀')))
    contractPaper = str(contract.contractPaper).split('/')[-1]
    orderPaper = str(contract.orderPaper).split('/')[-1]

    sumRevenuePrice = revenues.aggregate(sum_revenuePrice=Coalesce(Sum('revenuePrice'), 0))['sum_revenuePrice']
    sumRevenueProfitPrice = revenues.aggregate(sum_revenueProfitPrice=Coalesce(Sum('revenueProfitPrice'), 0))['sum_revenueProfitPrice']
    if sumRevenueProfitPrice:
        sumRevenueProfitRatio = round(sumRevenueProfitPrice / sumRevenuePrice * 100)
    else:
        sumRevenueProfitRatio = 0
    sumPurchasePrice = purchases.aggregate(sum_purchasePrice=Coalesce(Sum('purchasePrice'), 0))['sum_purchasePrice']

    # 연도 별 매출·이익 기여도
    yearList = list(set([i['predictBillingDate'].year for i in list(revenues.values('predictBillingDate'))]) |
                    set([i['predictBillingDate'].year for i in list(purchases.values('predictBillingDate'))]) |
                    set([i['predictDepositDate'].year for i in list(revenues.values('predictDepositDate')) if i['predictDepositDate']]) |
                    set([i['predictWithdrawDate'].year for i in list(purchases.values('predictWithdrawDate')) if i['predictWithdrawDate']]) |
                    set([i['billingDate'].year for i in list(costs.values('billingDate'))]))
    yearSummary = []
    for year in yearList:
        temp = {
            'year': str(year),
            'revenuePrice': revenues.aggregate(revenuePrice=Coalesce(Sum('revenuePrice', filter=Q(predictBillingDate__year=year)), 0))['revenuePrice'],
            'purchasePrice': purchases.aggregate(purchasePrice=Coalesce(Sum('purchasePrice', filter=Q(predictBillingDate__year=year)), 0))['purchasePrice'] +
                             costs.aggregate(costPrice=Coalesce(Sum('costPrice', filter=Q(billingDate__year=year)), 0))['costPrice'],
            'revenueProfitPrice': revenues.aggregate(revenueProfitPrice=Coalesce(Sum('revenueProfitPrice', filter=Q(predictBillingDate__year=year)), 0))['revenueProfitPrice'],
            'depositPrice': revenues.aggregate(depositPrice=Coalesce(Sum('revenuePrice', filter=Q(depositDate__isnull=False) & Q(predictBillingDate__year=year)), 0))['depositPrice'],
            'withdrawPrice': purchases.aggregate(withdrawPrice=Coalesce(Sum('purchasePrice', filter=Q(withdrawDate__isnull=False) & Q(predictBillingDate__year=year)), 0))['withdrawPrice'],
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
        'purchasePrice': purchases.aggregate(purchasePrice=Coalesce(Sum('purchasePrice'), 0))['purchasePrice'] +
                         costs.aggregate(costPrice=Coalesce(Sum('costPrice'), 0))['costPrice'],
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
        .annotate(sum_ratio_withdraw=Coalesce(Sum('purchasePrice'), 0) * 100 / companyTotalWithdraw['total_sum_withdraw'])

    if (companyTotalWithdraw['total_sum_withdraw']) == 0:
        companyTotalWithdraw['total_sum_withdraw'] = '0'
    else:
        companyTotalWithdraw['total_ratio_withdraw'] = round(companyTotalWithdraw['total_filter_withdraw'] / companyTotalWithdraw['total_sum_withdraw'] * 100)

    context = {
        'revenueId': '',
        'purchaseId': '',
        # 계약, 세부사항, 매출, 매입, 원가, 계약서 명, 수주통보서 명
        'contract': contract,
        'services': services,
        'items': items,
        'revenues': revenues.order_by('predictBillingDate'),
        'sumRevenuePrice': sumRevenuePrice,
        'sumRevenueProfitPrice': sumRevenueProfitPrice,
        'sumRevenueProfitRatio': sumRevenueProfitRatio,
        'purchases': purchases.order_by('predictBillingDate'),
        'sumPurchasePrice': sumPurchasePrice,
        'costs': costs.order_by('billingDate'),
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
        teamGoal = goal.values('empDeptName') \
            .annotate(revenueTarget=F('salesq1'),
                      profitTarget=F('profitq1'))
        revenue = Revenue.objects.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end']))
    elif quarter == 2:
        teamGoal = goal.values('empDeptName') \
            .annotate(revenueTarget=F('salesq1') + F('salesq2'),
                      profitTarget=F('profitq1') + F('profitq2'))
        revenue = Revenue.objects.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q2_end']))
    elif quarter == 3:
        teamGoal = goal.values('empDeptName') \
            .annotate(revenueTarget=F('salesq1') + F('salesq2') + F('salesq3'),
                      profitTarget=F('profitq1') + F('profitq2') + F('profitq3'))
        revenue = Revenue.objects.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q3_end']))
    else:
        teamGoal = goal.values('empDeptName') \
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


def cal_revenue_incentive(revenueId):
    revenue = Revenue.objects.get(revenueId=revenueId)
    contract = Contract.objects.get(contractId=int(revenue.contractId.contractId))

    # 매출 세금계산서 발행 기준
    if revenue.billingDate:

        # 매출일로부터 4개월 경과된 매수채권은 인센티브에 포함하지 않음
        if revenue.depositDate is None and (date.today() - revenue.billingDate) > timedelta(120):
            print('1')
            incentiveRevenue = 0
            incentiveProfit = 0

        # GP가 마이너스(0원 미만)일 경우 인센티브 매출, GP는 0원
        elif contract.profitPrice < 0:
            print('2')
            incentiveRevenue = 0
            incentiveProfit = 0

        # 계약의 GP가 3% 미만이면 해당 계약의 매출과 GP는 50%만 인정
        elif contract.profitRatio < 3:
            print('3')
            incentiveRevenue = int(revenue.revenuePrice * 0.5)
            incentiveProfit = int(revenue.revenueProfitPrice * 0.5)

        else:
            print('4')
            incentiveRevenue = int(revenue.revenuePrice)
            incentiveProfit = int(revenue.revenueProfitPrice)

    # 세금계산서 발행 안 된 매출은 인센티브 0
    else:
        print('5')
        incentiveRevenue = 0
        incentiveProfit = 0

    return incentiveRevenue, incentiveProfit


def cal_acc(ratio):
    if ratio <= 94:
        return ratio, 0
    elif ratio < 120:
        return (
            Acceleration.objects.get(Q(accelerationMin__lte=ratio) & Q(accelerationMax__gte=ratio)).accelerationRatio,
            Acceleration.objects.get(Q(accelerationMin__lte=ratio) & Q(accelerationMax__gte=ratio)).accelerationAcc
        )
    else:
        return 140, 4


def cal_emp_incentive(salary, achieve, acc):
    if achieve < 100:
        return round(salary * (achieve / 100))
    else:
        return (((salary * (achieve / 100)) - salary) * acc) + salary

def cal_over_gp(revenue):
    max = 500000
    sum = 0
    for r in revenue:
        if (r.contractId.profitPrice - r.contractId.salePrice/100*15)/100*10 > max:
            sum += max
        else:
            sum += (r.contractId.profitPrice - r.contractId.salePrice/100*15)/100*10
    return sum

