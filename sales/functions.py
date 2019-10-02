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
from .models import Contract, Category, Revenue, Contractitem, Goal, Purchase, Cost, Acceleration, Incentive
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

    teamRevenue = list(revenue.values('contractId__empDeptName').annotate(
        revenuePrice=Sum('revenuePrice'),
        revenueProfitPrice=Sum('revenueProfitPrice'))
    )
    personRevenue = revenue.values('contractId__empId', 'contractId__empName', 'contractId__empDeptName').annotate(
        revenuePrice=Sum('revenuePrice'),
        revenueProfitPrice=Sum('revenueProfitPrice')
    )
    sumRevenue = revenue.aggregate(
        revenuePrice=Sum('revenuePrice'),
        revenueProfitPrice=Sum('revenueProfitPrice')
    )

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
            'background': '#ffffec',
        }
        row['revenueRatio'] = str(round(row['revenuePrice'] / row['revenueTarget'] * 100)) + '%'
        row['profitRatio'] = str(round(row['profitPrice'] / row['profitTarget'] * 100)) + '%'
        rows.append(row)

        for person in list(personRevenue.filter(contractId__empDeptName=team)):
            row = {
                'empDeptName': person['contractId__empName'],
                'revenueTarget': '',
                'profitTarget': '',
                'revenuePrice': person['revenuePrice'],
                'profitPrice': person['revenueProfitPrice'],
                'revenueRatio': '',
                'profitRatio': '',
            }
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
            incentiveRevenue = 0
            incentiveProfit = 0
            incentiveReason = '4개월 미수채권'

        # GP가 마이너스(0원 미만)일 경우 인센티브 매출, GP는 0원
        elif contract.profitPrice < 0:
            incentiveRevenue = 0
            incentiveProfit = 0
            incentiveReason = '마이너스 GP'

        # 계약의 GP가 3% 미만이면 해당 계약의 매출과 GP는 50%만 인정
        elif contract.profitRatio < 3:
            incentiveRevenue = int(revenue.revenuePrice * 0.5)
            incentiveProfit = int(revenue.revenueProfitPrice * 0.5)
            incentiveReason = 'GP 3% 미만'

        else:
            incentiveRevenue = int(revenue.revenuePrice)
            incentiveProfit = int(revenue.revenueProfitPrice)
            incentiveReason = '정상'

    # 세금계산서 발행 안 된 매출은 인센티브 0
    else:
        incentiveRevenue = 0
        incentiveProfit = 0
        incentiveReason = '계산서미발행'

    return incentiveRevenue, incentiveProfit, incentiveReason


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


def empIncentive(year, empId):
    empDeptName = Employee.objects.get(empId=empId).empDeptName
    incentive = Incentive.objects.filter(Q(empId=empId) & Q(year=datetime.today().year))
    goal = Goal.objects.get(Q(empDeptName=empDeptName) & Q(year=datetime.today().year))
    revenues = Revenue.objects.filter(Q(contractId__empDeptName=empDeptName) & Q(contractId__contractStep='Firm'))
    revenue1 = revenues.filter(Q(billingDate__gte=year + '-01-01') & Q(billingDate__lt=year + '-04-01'))
    revenue2 = revenues.filter(Q(billingDate__gte=year + '-04-01') & Q(billingDate__lt=year + '-07-01'))
    revenue3 = revenues.filter(Q(billingDate__gte=year + '-07-01') & Q(billingDate__lt=year + '-10-01'))
    revenue4 = revenues.filter(Q(billingDate__gte=year + '-10-01') & Q(billingDate__lte=year + '-12-31'))

    table1 = [
        {
            'name': 'FULL SALARY',
            'q1': int(incentive.get(quarter=1).salary),
            'q2': int(incentive.get(quarter=2).salary),
            'q3': int(incentive.get(quarter=3).salary),
            'q4': int(incentive.get(quarter=4).salary),
        },
        {
            'name': 'BETTING PERCENT',
            'q1': str(incentive.get(quarter=1).bettingRatio) + '%',
            'q2': str(incentive.get(quarter=2).bettingRatio) + '%',
            'q3': str(incentive.get(quarter=3).bettingRatio) + '%',
            'q4': str(incentive.get(quarter=4).bettingRatio) + '%',
        },
        {
            'name': 'BASIC SALARY',
            'q1': int(incentive.get(quarter=1).basicSalary),
            'q2': int(incentive.get(quarter=2).basicSalary),
            'q3': int(incentive.get(quarter=3).basicSalary),
            'q4': int(incentive.get(quarter=4).basicSalary),
        },
        {
            'name': 'BETTING SALARY',
            'q1': int(incentive.get(quarter=1).bettingSalary),
            'q2': int(incentive.get(quarter=2).bettingSalary),
            'q3': int(incentive.get(quarter=3).bettingSalary),
            'q4': int(incentive.get(quarter=4).bettingSalary),
        },
    ]

    table2 = {
        'target': {
            'revenue': {
                'q1': goal.salesq1,
                'q2': goal.salesq2,
                'q3': goal.salesq3,
                'q4': goal.salesq4,
            },
            'profit': {
                'q1': goal.profitq1,
                'q2': goal.profitq2,
                'q3': goal.profitq3,
                'q4': goal.profitq4,
            }
        },
        'real': {
            'revenue': {
                'q1': revenue1.aggregate(sum=Sum('revenuePrice'))['sum'] or 0,
                'q2': revenue2.aggregate(sum=Sum('revenuePrice'))['sum'] or 0,
                'q3': revenue3.aggregate(sum=Sum('revenuePrice'))['sum'] or 0,
                'q4': revenue4.aggregate(sum=Sum('revenuePrice'))['sum'] or 0,
            },
            'profit': {
                'q1': revenue1.aggregate(sum=Sum('revenueProfitPrice'))['sum'] or 0,
                'q2': revenue2.aggregate(sum=Sum('revenueProfitPrice'))['sum'] or 0,
                'q3': revenue3.aggregate(sum=Sum('revenueProfitPrice'))['sum'] or 0,
                'q4': revenue4.aggregate(sum=Sum('revenueProfitPrice'))['sum'] or 0,
            }
        },
        'incentive': {
            'revenue': {
                'q1': revenue1.aggregate(sum=Sum('incentivePrice'))['sum'] or 0,
                'q2': revenue2.aggregate(sum=Sum('incentivePrice'))['sum'] or 0,
                'q3': revenue3.aggregate(sum=Sum('incentivePrice'))['sum'] or 0,
                'q4': revenue4.aggregate(sum=Sum('incentivePrice'))['sum'] or 0,
            },
            'profit': {
                'q1': revenue1.aggregate(sum=Sum('incentiveProfitPrice'))['sum'] or 0,
                'q2': revenue2.aggregate(sum=Sum('incentiveProfitPrice'))['sum'] or 0,
                'q3': revenue3.aggregate(sum=Sum('incentiveProfitPrice'))['sum'] or 0,
                'q4': revenue4.aggregate(sum=Sum('incentiveProfitPrice'))['sum'] or 0,
            }
        },
    }
    table2['achieve'] = {
        'revenue': {
            'q1': round((table2['incentive']['revenue']['q1'] / table2['target']['revenue']['q1'] * 100), 1),
            'q2': round((table2['incentive']['revenue']['q2'] / table2['target']['revenue']['q2'] * 100), 1),
            'q3': round((table2['incentive']['revenue']['q3'] / table2['target']['revenue']['q3'] * 100), 1),
            'q4': round((table2['incentive']['revenue']['q4'] / table2['target']['revenue']['q4'] * 100), 1),
        },
        'profit': {
            'q1': round((table2['incentive']['profit']['q1'] / table2['target']['profit']['q1'] * 100), 1),
            'q2': round((table2['incentive']['profit']['q2'] / table2['target']['profit']['q2'] * 100), 1),
            'q3': round((table2['incentive']['profit']['q3'] / table2['target']['profit']['q3'] * 100), 1),
            'q4': round((table2['incentive']['profit']['q4'] / table2['target']['profit']['q4'] * 100), 1),
        },
    }
    table2['achieve']['total'] = {
        'q1': round(((table2['achieve']['revenue']['q1'] * 0.3) + (table2['achieve']['profit']['q1'] * 0.7)), 1),
        'q2': round(((table2['achieve']['revenue']['q2'] * 0.3) + (table2['achieve']['profit']['q2'] * 0.7)), 1),
        'q3': round(((table2['achieve']['revenue']['q3'] * 0.3) + (table2['achieve']['profit']['q3'] * 0.7)), 1),
        'q4': round(((table2['achieve']['revenue']['q4'] * 0.3) + (table2['achieve']['profit']['q4'] * 0.7)), 1),
    }
    table2['target']['cumulation'] = {
        'revenue': {
            'q1': table2['target']['revenue']['q1'],
            'q2': table2['target']['revenue']['q1'] + table2['target']['revenue']['q2'],
            'q3': table2['target']['revenue']['q1'] + table2['target']['revenue']['q2'] +
                  table2['target']['revenue']['q3'],
            'q4': table2['target']['revenue']['q1'] + table2['target']['revenue']['q2'] +
                  table2['target']['revenue']['q3'] + table2['target']['revenue']['q4'],
        },
        'profit': {
            'q1': table2['target']['profit']['q1'],
            'q2': table2['target']['profit']['q1'] + table2['target']['profit']['q2'],
            'q3': table2['target']['profit']['q1'] + table2['target']['profit']['q2'] +
                  table2['target']['profit']['q3'],
            'q4': table2['target']['profit']['q1'] + table2['target']['profit']['q2'] +
                  table2['target']['profit']['q3'] + table2['target']['profit']['q4'],
        },
    }
    table2['real']['cumulation'] = {
        'revenue': {
            'q1': table2['real']['revenue']['q1'],
            'q2': table2['real']['revenue']['q1'] + table2['real']['revenue']['q2'],
            'q3': table2['real']['revenue']['q1'] + table2['real']['revenue']['q2'] +
                  table2['real']['revenue']['q3'],
            'q4': table2['real']['revenue']['q1'] + table2['real']['revenue']['q2'] +
                  table2['real']['revenue']['q3'] + table2['real']['revenue']['q4'],
        },
        'profit': {
            'q1': table2['real']['profit']['q1'],
            'q2': table2['real']['profit']['q1'] + table2['real']['profit']['q2'],
            'q3': table2['real']['profit']['q1'] + table2['real']['profit']['q2'] +
                  table2['real']['profit']['q3'],
            'q4': table2['real']['profit']['q1'] + table2['real']['profit']['q2'] +
                  table2['real']['profit']['q3'] + table2['real']['profit']['q4'],
        },
    }
    table2['incentive']['cumulation'] = {
        'revenue': {
            'q1': table2['incentive']['revenue']['q1'],
            'q2': table2['incentive']['revenue']['q1'] + table2['incentive']['revenue']['q2'],
            'q3': table2['incentive']['revenue']['q1'] + table2['incentive']['revenue']['q2'] +
                  table2['incentive']['revenue']['q3'],
            'q4': table2['incentive']['revenue']['q1'] + table2['incentive']['revenue']['q2'] +
                  table2['incentive']['revenue']['q3'] + table2['incentive']['revenue']['q4'],
        },
        'profit': {
            'q1': table2['incentive']['profit']['q1'],
            'q2': table2['incentive']['profit']['q1'] + table2['incentive']['profit']['q2'],
            'q3': table2['incentive']['profit']['q1'] + table2['incentive']['profit']['q2'] +
                  table2['incentive']['profit']['q3'],
            'q4': table2['incentive']['profit']['q1'] + table2['incentive']['profit']['q2'] +
                  table2['incentive']['profit']['q3'] + table2['incentive']['profit']['q4'],
        },
    }
    table2['achieve']['cumulation'] = {
        'revenue': {
            'q1': round((table2['incentive']['cumulation']['revenue']['q1'] /
                        table2['target']['cumulation']['revenue']['q1'] * 100), 1),
            'q2': round((table2['incentive']['cumulation']['revenue']['q2'] /
                        table2['target']['cumulation']['revenue']['q2'] * 100), 1),
            'q3': round((table2['incentive']['cumulation']['revenue']['q3'] /
                        table2['target']['cumulation']['revenue']['q3'] * 100), 1),
            'q4': round((table2['incentive']['cumulation']['revenue']['q1'] /
                        table2['target']['cumulation']['revenue']['q4'] * 100), 1),
        },
        'profit': {
            'q1': round((table2['incentive']['cumulation']['profit']['q1'] /
                        table2['target']['cumulation']['profit']['q1'] * 100), 1),
            'q2': round((table2['incentive']['cumulation']['profit']['q2'] /
                        table2['target']['cumulation']['profit']['q2'] * 100), 1),
            'q3': round((table2['incentive']['cumulation']['profit']['q3'] /
                        table2['target']['cumulation']['profit']['q3'] * 100), 1),
            'q4': round((table2['incentive']['cumulation']['profit']['q4'] /
                        table2['target']['cumulation']['profit']['q4'] * 100), 1),
        },
    }
    table2['achieve']['cumulation']['total'] = {
        'q1': round(((table2['achieve']['cumulation']['revenue']['q1'] * 0.3) +
                    (table2['achieve']['cumulation']['profit']['q1'] * 0.7)), 1),
        'q2': round(((table2['achieve']['cumulation']['revenue']['q2'] * 0.3) +
                    (table2['achieve']['cumulation']['profit']['q2'] * 0.7)), 1),
        'q3': round(((table2['achieve']['cumulation']['revenue']['q3'] * 0.3) +
                    (table2['achieve']['cumulation']['profit']['q3'] * 0.7)), 1),
        'q4': round(((table2['achieve']['cumulation']['revenue']['q4'] * 0.3) +
                    (table2['achieve']['cumulation']['profit']['q4'] * 0.7)), 1),
    }

    table3 = [
        {
            'name': '목표 달성률',
            'q1': str(table2['achieve']['cumulation']['total']['q1']) + '%',
            'q2': str(table2['achieve']['cumulation']['total']['q2']) + '%',
            'q3': str(table2['achieve']['cumulation']['total']['q3']) + '%',
            'q4': str(table2['achieve']['cumulation']['total']['q4']) + '%',
        },
        {
            'name': '급여',
            'q1': int(incentive.get(quarter=1).salary),
            'q2': int(incentive.get(quarter=1).salary) + int(incentive.get(quarter=2).salary),
            'q3': int(incentive.get(quarter=1).salary) + int(incentive.get(quarter=2).salary) +
                  int(incentive.get(quarter=3).salary),
            'q4': int(incentive.get(quarter=1).salary) + int(incentive.get(quarter=2).salary) +
                  int(incentive.get(quarter=3).salary) + int(incentive.get(quarter=4).salary),
        },
        {
            'name': '기본급',
            'q1': int(incentive.get(quarter=1).basicSalary),
            'q2': int(incentive.get(quarter=2).basicSalary),
            'q3': int(incentive.get(quarter=3).basicSalary),
            'q4': int(incentive.get(quarter=4).basicSalary),
        },
        {
            'name': '배팅액',
            'q1': int(incentive.get(quarter=1).bettingSalary),
            'q2': int(incentive.get(quarter=2).bettingSalary),
            'q3': int(incentive.get(quarter=3).bettingSalary),
            'q4': int(incentive.get(quarter=4).bettingSalary),
        },
        {
            'name': '인정률',
            'q1': str(cal_acc(table2['achieve']['cumulation']['total']['q1'])[0]) + '%',
            'q2': str(cal_acc(table2['achieve']['cumulation']['total']['q2'])[0]) + '%',
            'q3': str(cal_acc(table2['achieve']['cumulation']['total']['q3'])[0]) + '%',
            'q4': str(cal_acc(table2['achieve']['cumulation']['total']['q4'])[0]) + '%',
        },
        {
            'name': 'ACC',
            'q1': cal_acc(table2['achieve']['cumulation']['total']['q1'])[1],
            'q2': cal_acc(table2['achieve']['cumulation']['total']['q2'])[1],
            'q3': cal_acc(table2['achieve']['cumulation']['total']['q3'])[1],
            'q4': cal_acc(table2['achieve']['cumulation']['total']['q4'])[1],
        },
        {
            'name': '예상누적인센티브',
            'q1': cal_emp_incentive(
                int(incentive.get(quarter=1).bettingSalary),
                cal_acc(table2['achieve']['cumulation']['total']['q1'])[0],
                cal_acc(table2['achieve']['cumulation']['total']['q1'])[1]
            ),
            'q2': cal_emp_incentive(
                int(incentive.get(quarter=1).bettingSalary) + int(incentive.get(quarter=2).bettingSalary),
                cal_acc(table2['achieve']['cumulation']['total']['q2'])[0],
                cal_acc(table2['achieve']['cumulation']['total']['q2'])[1]
            ),
            'q3': cal_emp_incentive(
                int(incentive.get(quarter=1).bettingSalary) + int(incentive.get(quarter=2).bettingSalary) +
                int(incentive.get(quarter=3).bettingSalary),
                cal_acc(table2['achieve']['cumulation']['total']['q3'])[0],
                cal_acc(table2['achieve']['cumulation']['total']['q3'])[1]
            ),
            'q4': cal_emp_incentive(
                int(incentive.get(quarter=1).bettingSalary) + int(incentive.get(quarter=2).bettingSalary) +
                int(incentive.get(quarter=3).bettingSalary) + int(incentive.get(quarter=4).bettingSalary),
                cal_acc(table2['achieve']['cumulation']['total']['q4'])[0],
                cal_acc(table2['achieve']['cumulation']['total']['q4'])[1]
            ),
        },
        {
            'name': '예상분기인센티브',
            'q1': cal_emp_incentive(
                int(incentive.get(quarter=1).bettingSalary),
                cal_acc(table2['achieve']['cumulation']['total']['q1'])[0],
                cal_acc(table2['achieve']['cumulation']['total']['q1'])[1]
            ),
            'q2': cal_emp_incentive(
                int(incentive.get(quarter=1).bettingSalary) + int(incentive.get(quarter=2).bettingSalary),
                cal_acc(table2['achieve']['cumulation']['total']['q2'])[0],
                cal_acc(table2['achieve']['cumulation']['total']['q2'])[1]
            ) - int(incentive.get(quarter=1).achieveIncentive),
            'q3': cal_emp_incentive(
                int(incentive.get(quarter=1).bettingSalary) + int(incentive.get(quarter=2).bettingSalary) +
                int(incentive.get(quarter=3).bettingSalary),
                cal_acc(table2['achieve']['cumulation']['total']['q3'])[0],
                cal_acc(table2['achieve']['cumulation']['total']['q3'])[1]
            ) - (int(incentive.get(quarter=1).achieveIncentive) + int(incentive.get(quarter=2).achieveIncentive)),
            'q4': cal_emp_incentive(
                int(incentive.get(quarter=1).bettingSalary) + int(incentive.get(quarter=2).bettingSalary) +
                int(incentive.get(quarter=3).bettingSalary) + int(incentive.get(quarter=4).bettingSalary),
                cal_acc(table2['achieve']['cumulation']['total']['q4'])[0],
                cal_acc(table2['achieve']['cumulation']['total']['q4'])[1]
            ) - (int(incentive.get(quarter=1).achieveIncentive) + int(incentive.get(quarter=2).achieveIncentive) +
                 int(incentive.get(quarter=3).achieveIncentive)),
        },
        {
            'name': '확정지급액',
            'q1': int(incentive.get(quarter=1).achieveIncentive),
            'q2': int(incentive.get(quarter=2).achieveIncentive),
            'q3': int(incentive.get(quarter=3).achieveIncentive),
            'q4': int(incentive.get(quarter=4).achieveIncentive),
        },
    ]

    return table1, table2, table3


def cal_over_gp(revenue):
    max = 500000
    sum = 0
    for r in revenue:
        if (r.contractId.profitPrice - r.contractId.salePrice/100*15)/100*10 > max:
            sum += max
        else:
            sum += (r.contractId.profitPrice - r.contractId.salePrice/100*15)/100*10
    return sum
