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
from service.models import Company, Customer
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
    contractPaper = str(contract.contractPaper).split('/')[-1]
    orderPaper = str(contract.orderPaper).split('/')[-1]

    # 연도 별 매출·이익 기여도
    yearList = list(set([i['predictBillingDate'].year for i in list(revenues.values('predictBillingDate'))]))
    yearSummary = []
    for year in yearList:
        temp = {
            'year': str(year),
            'revenuePrice': revenues.aggregate(revenuePrice=Coalesce(Sum('revenuePrice', filter=Q(predictBillingDate__year=year)), 0))['revenuePrice'],
            'revenueProfitPrice': revenues.aggregate(revenueProfitPrice=Coalesce(Sum('revenueProfitPrice', filter=Q(predictBillingDate__year=year)), 0))['revenueProfitPrice'],
            'depositPrice': revenues.aggregate(depositPrice=Coalesce(Sum('revenuePrice', filter=Q(predictBillingDate__year=year) & Q(depositDate__isnull=False)), 0))['depositPrice'],
        }
        if temp['revenuePrice'] == 0:
            temp['revenueProfitRatio'] = '-'
            temp['depositRatio'] = '-'
        else:
            temp['revenueProfitRatio'] = round(temp['revenueProfitPrice'] / temp['revenuePrice'] * 100)
            temp['depositRatio'] = round(temp['depositPrice'] / temp['revenuePrice'] * 100)
        yearSummary.append(temp)

    yearSum = {
        'year': '합계',
        'revenuePrice': revenues.aggregate(revenuePrice=Coalesce(Sum('revenuePrice'), 0))['revenuePrice'],
        'revenueProfitPrice': revenues.aggregate(revenueProfitPrice=Coalesce(Sum('revenueProfitPrice'), 0))['revenueProfitPrice'],
        'depositPrice': revenues.aggregate(depositPrice=Coalesce(Sum('revenuePrice', filter=Q(depositDate__isnull=False)), 0))['depositPrice'],
    }
    if yearSum['revenuePrice'] == 0:
        yearSum['revenueProfitRatio'] = '-'
        yearSum['depositRatio'] = '-'
    else:
        yearSum['revenueProfitRatio'] = round(yearSum['revenueProfitPrice'] / yearSum['revenuePrice'] * 100)
        yearSum['depositRatio'] = round(yearSum['depositPrice'] / yearSum['revenuePrice'] * 100)

    # 입출금정보 - 총 금액
    totalDeposit = revenues.filter(depositDate__isnull=False).aggregate(sum_deposit=Coalesce(Sum('revenuePrice'), 0))["sum_deposit"]
    totalWithdraw = purchases.filter(withdrawDate__isnull=False).aggregate(sum_withdraw=Coalesce(Sum('purchasePrice'), 0))["sum_withdraw"]
    if totalDeposit == 0:
        totalRatio = '-'
    else:
        totalRatio = round(totalWithdraw / totalDeposit * 100)

    # 입출금정보 - 매출
    companyDeposit = revenues \
        .values('revenueCompany') \
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
        .values('purchaseCompany') \
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
        'items': items,
        'revenues': revenues.order_by('predictBillingDate'),
        'purchases': purchases.order_by('predictBillingDate'),
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
