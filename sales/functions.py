# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.db.models import Sum, F, Count
from django.db.models.functions import Coalesce
import os
import smtplib
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from service.functions import link_callback
from xhtml2pdf import pisa
from smtplib import SMTP_SSL

from service.models import Servicereport
from approval.models import Document
from .models import Contract, Revenue, Contractitem, Goal, Purchase, Cost, Acceleration, Incentive, Expense, Contractfile,\
    Purchasetypea, Purchasetypeb, Purchasetypec, Purchasetyped, Purchasefile, Purchaseorderform, Purchaseorder, Purchasecontractitem
from hr.models import AdminEmail
from service.models import Employee
from django.db.models import Q, Max
from django.template import loader


def viewContract(contractId):
    # 첨부파일
    files_a = Purchasefile.objects.filter(contractId__contractId=contractId, fileCategory='매입견적서').order_by('uploadDatetime')
    files_b = Contractfile.objects.filter(contractId__contractId=contractId, fileCategory='매출견적서').order_by('uploadDatetime')
    files_c = Contractfile.objects.filter(contractId__contractId=contractId, fileCategory='계약서').order_by('uploadDatetime')
    files_e = Contractfile.objects.filter(contractId__contractId=contractId, fileCategory='매입발주서').order_by('uploadDatetime')
    files_f = Contractfile.objects.filter(contractId__contractId=contractId, fileCategory='납품,구축,검수확인서').order_by('uploadDatetime')
    files_g = Contractfile.objects.filter(contractId__contractId=contractId, fileCategory='매출발행').order_by('uploadDatetime')

    # 결재문서
    documents = Document.objects.filter(contractId=contractId).exclude(documentStatus='임시')
    ordernotis = documents.filter(formId__formTitle='수주통보서', documentStatus='완료')

    # 계약, 세부정보, 매출, 매입, 계약서 명, 수주통보서 명
    contract = Contract.objects.get(contractId=contractId)
    items = Contractitem.objects.filter(contractId=contractId)
    revenues = Revenue.objects.filter(contractId=contractId)
    purchaseItems = Purchasecontractitem.objects.filter(contractId=contractId)
    purchases = Purchase.objects.filter(contractId=contractId)
    purchaseCompany = list(purchases.values_list('purchaseCompany__companyNameKo', flat=True).distinct().order_by('purchaseCompany__companyNameKo'))
    purchasesNotBilling = purchases.filter(billingDate__isnull=True)
    costs = Cost.objects.filter(contractId=contractId)
    services = Servicereport.objects.filter(
        Q(contractId=contractId) & 
        Q(serviceStatus='Y') & 
        (Q(empDeptName='DB지원팀') | Q(empDeptName='솔루션지원팀') | Q(empDeptName='인프라서비스사업팀'))
    )
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
            'revenuePrice': revenues.aggregate(
                revenuePrice=Coalesce(Sum('revenuePrice', filter=Q(predictBillingDate__year=year)), 0)
            )['revenuePrice'],
            'purchasePrice': purchases.aggregate(
                purchasePrice=Coalesce(Sum('purchasePrice', filter=Q(predictBillingDate__year=year)), 0)
            )['purchasePrice'] + costs.aggregate(
                costPrice=Coalesce(Sum('costPrice', filter=Q(billingDate__year=year)), 0)
            )['costPrice'],
            'revenueProfitPrice': revenues.aggregate(
                revenueProfitPrice=Coalesce(Sum('revenueProfitPrice', filter=Q(predictBillingDate__year=year)), 0)
            )['revenueProfitPrice'],
            'depositPrice': revenues.aggregate(
                depositPrice=Coalesce(Sum('revenuePrice', filter=Q(depositDate__isnull=False) & Q(predictBillingDate__year=year)), 0)
            )['depositPrice'],
            'withdrawPrice': purchases.aggregate(
                withdrawPrice=Coalesce(Sum('purchasePrice', filter=Q(withdrawDate__isnull=False) & Q(predictBillingDate__year=year)), 0)
            )['withdrawPrice'],
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

    # 매입발주서
    purchaseOrderForm = list(Purchaseorderform.objects.all().values_list('formTitle', flat=True).order_by('formNumber'))
    purchaseOrderDocument = Purchaseorder.objects.filter(contractId=contract)

    context = {
        'revenueId': '',
        'purchaseId': '',
        # 첨부파일
        'files_a': files_a,
        'files_b': files_b,
        'files_c': files_c,
        'files_e': files_e,
        'files_f': files_f,
        'files_g': files_g,
        # 결재문서, 매입발주서
        'documents': documents,
        'ordernotis': ordernotis,
        'purchaseOrderForm': purchaseOrderForm,
        'purchaseOrderDocument': purchaseOrderDocument,
        # 계약, 세부사항, 매출, 매입, 원가, 계약서 명, 수주통보서 명
        'contract': contract,
        'services': services,
        'items': items,
        'revenues': revenues.order_by('predictBillingDate'),
        'sumRevenuePrice': sumRevenuePrice,
        'sumRevenueProfitPrice': sumRevenueProfitPrice,
        'sumRevenueProfitRatio': sumRevenueProfitRatio,
        'purchaseItems': purchaseItems.order_by('mainCategory', 'subCategory'),
        'purchases': purchases.order_by('predictBillingDate', 'purchaseCompany__companyNameKo'),
        'purchaseCompany': purchaseCompany,
        'purchasesNotBilling': purchasesNotBilling,
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
        teamGoal = goal.values(
            'empDeptName'
        ).annotate(
            revenueTarget=F('salesq1'),
            profitTarget=F('profitq1')
        )
        revenue = Revenue.objects.filter(
            Q(predictBillingDate__gte=dict_quarter['q1_start']) &
            Q(predictBillingDate__lt=dict_quarter['q1_end'])
        ).select_related()
    elif quarter == 2:
        teamGoal = goal.values(
            'empDeptName'
        ).annotate(
            revenueTarget=F('salesq1') + F('salesq2'),
            profitTarget=F('profitq1') + F('profitq2')
        )
        revenue = Revenue.objects.filter(
            Q(predictBillingDate__gte=dict_quarter['q1_start']) &
            Q(predictBillingDate__lt=dict_quarter['q2_end'])
        ).select_related()
    elif quarter == 3:
        teamGoal = goal.values(
            'empDeptName'
        ).annotate(
            revenueTarget=F('salesq1') + F('salesq2') + F('salesq3'),
            profitTarget=F('profitq1') + F('profitq2') + F('profitq3')
        )
        revenue = Revenue.objects.filter(
            Q(predictBillingDate__gte=dict_quarter['q1_start']) &
            Q(predictBillingDate__lt=dict_quarter['q3_end'])
        ).select_related()
    else:
        teamGoal = goal.values(
            'empDeptName'
        ).annotate(
            revenueTarget=F('salesq1') + F('salesq2') + F('salesq3') + F('salesq4'),
            profitTarget=F('profitq1') + F('profitq2') + F('profitq3') + F('profitq4')
        )
        revenue = Revenue.objects.filter(
            Q(predictBillingDate__gte=dict_quarter['q1_start']) &
            Q(predictBillingDate__lt=dict_quarter['q4_end'])
        ).select_related()
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
    ).order_by('-revenuePrice', '-revenueProfitPrice')
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
    if row['revenueTarget']:
        row['revenueRatio'] = round(row['revenuePrice'] / row['revenueTarget'] * 100)
        row['profitRatio'] = round(row['profitPrice'] / row['profitTarget'] * 100)
    else:
        row['revenueRatio'] = '-'
        row['profitRatio'] = '-'

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


def cal_emp_incentive(empId, table2, year, quarter):
    incentive = Incentive.objects.filter(Q(empId=empId) & Q(year=year))

    if quarter > 1:
        incentiveZero = incentive.get(quarter=quarter - 1).bettingSalary != incentive.get(quarter=quarter).bettingSalary
    else:
        incentiveZero = False

    if int(incentive.get(quarter=quarter).bettingSalary) == 0 or incentiveZero:
        if quarter == 1:
            return 0
        else:
            tempQuarter = 1
            tempSalary = 0
            while tempQuarter <= quarter - 1:
                tempSalary += int(incentive.get(quarter=tempQuarter).bettingSalary)
                tempQuarter += 1

            return cal_emp_incentive(
                empId, table2, year, quarter - 1,
            )
    else:
        tempQuarter = 1
        tempSalary = 0
        while tempQuarter <= quarter:
            tempSalary += int(incentive.get(quarter=tempQuarter).bettingSalary)
            tempQuarter += 1
        achieve = cal_acc(table2['achieve']['cumulation']['total']['q' + str(quarter)])[0]
        acc = cal_acc(table2['achieve']['cumulation']['total']['q' + str(quarter)])[1]

        if achieve < 100:
            return round(tempSalary * (achieve / 100))
        else:
            return (((tempSalary * (achieve / 100)) - tempSalary) * acc) + tempSalary


def empIncentive(year, empId):
    empDeptName = Employee.objects.get(empId=empId).empDeptName
    incentive = Incentive.objects.filter(Q(empId=empId) & Q(year=year))
    goal = Goal.objects.get(Q(empDeptName=empDeptName) & Q(year=year))
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
            'q1': cal_emp_incentive(empId, table2, year, 1),
            'q2': cal_emp_incentive(empId, table2, year, 2),
            'q3': cal_emp_incentive(empId, table2, year, 3),
            'q4': cal_emp_incentive(empId, table2, year, 4),
        },
        {
            'name': '예상분기인센티브',
            'q1': cal_emp_incentive(empId, table2, year, 1),
            'q2': cal_emp_incentive(empId, table2, year, 2) - int(incentive.get(quarter=1).achieveIncentive),
            'q3': cal_emp_incentive(empId, table2, year, 3) -
                  (int(incentive.get(quarter=1).achieveIncentive) + int(incentive.get(quarter=2).achieveIncentive)),
            'q4': cal_emp_incentive(empId, table2, year, 4) -
                  (int(incentive.get(quarter=1).achieveIncentive) + int(incentive.get(quarter=2).achieveIncentive) +
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


def cal_monthlybill(todayYear):
    # 월별 매출액
    revenue_month = {'name': '매출액','sum': 0}
    # 월별 매출원가
    cost_month = {'name': '매출원가','sum': 0}
    # 월별 GP
    gp_month = {'name': 'GP','sum': 0}
    # 월별 판관비
    expense_month = {'name': '판관비','sum': 0}
    # 월별 영업 이익
    profit_month = {'name': '영업이익','sum': 0}
    table = []
    for todayMonth in range(1, 13):
        if todayMonth != 12:
            revenues = Revenue.objects.filter(
                Q(contractId__contractStep='Firm') &
                Q(predictBillingDate__gte='{}-{}-01'.format(todayYear, str(todayMonth).zfill(2))) &
                Q(predictBillingDate__lt='{}-{}-01'.format(todayYear, str(todayMonth + 1).zfill(2)))
            ).aggregate(
                revenuePrice=Sum('revenuePrice'),
                revenueProfitPrice=Sum('revenueProfitPrice')
            )
            expenses = Expense.objects.filter(
                Q(expenseStatus='Y') &
                Q(expenseDate__year=todayYear) &
                Q(expenseDate__month=todayMonth)
            ).exclude(
                expenseDept='전사'
            ).aggregate(
                expenseMoney__sum=Sum('expenseMoney')
            )
        else:
            revenues = Revenue.objects.filter(
                Q(contractId__contractStep='Firm') &
                Q(predictBillingDate__gte='{}-{}-01'.format(todayYear, str(todayMonth).zfill(2)))&
                Q(predictBillingDate__lt='{}-{}-01'.format(todayYear + 1, '01'))
            ).aggregate(
                revenuePrice=Sum('revenuePrice'),
                revenueProfitPrice=Sum('revenueProfitPrice')
            )
            expenses = Expense.objects.filter(
                Q(expenseStatus='Y') &
                Q(expenseDate__year=todayYear) &
                Q(expenseDate__month=todayMonth)
            ).exclude(
                expenseDept='전사'
            ).aggregate(
                expenseMoney__sum=Sum('expenseMoney')
            )

        revenue_month['month{}'.format(str(todayMonth))] = revenues['revenuePrice']
        revenue_month['sum'] += revenues['revenuePrice']
        gp_month['month{}'.format(str(todayMonth))] = revenues['revenueProfitPrice']
        gp_month['sum'] += revenues['revenueProfitPrice']
        cost_month['month{}'.format(str(todayMonth))] = revenues['revenuePrice'] - revenues['revenueProfitPrice']
        cost_month['sum'] += revenues['revenuePrice'] - revenues['revenueProfitPrice']
        expense_month['month{}'.format(str(todayMonth))] = expenses['expenseMoney__sum'] or 0
        expense_month['sum'] += expenses['expenseMoney__sum'] or 0
        profit_month['month{}'.format(str(todayMonth))] = revenues['revenueProfitPrice'] - (expenses['expenseMoney__sum'] or 0)
        profit_month['sum'] += revenues['revenueProfitPrice'] - (expenses['expenseMoney__sum'] or 0)

    table.append(revenue_month)
    table.append(cost_month)
    table.append(gp_month)
    table.append(expense_month)
    table.append(profit_month)

    return table


def cal_profitloss(dept, todayYear):
    # 계정과목 월별
    expenses1 = Expense.objects.filter(
        Q(expenseStatus='Y') &
        Q(expenseDate__year=todayYear) &
        Q(expenseDept__in=dept)
    ).values('expenseGroup').annotate(
        month1_expense=Sum('expenseMoney', filter=Q(expenseDate__month=1)),
        month2_expense=Sum('expenseMoney', filter=Q(expenseDate__month=2)),
        month3_expense=Sum('expenseMoney', filter=Q(expenseDate__month=3)),
        month4_expense=Sum('expenseMoney', filter=Q(expenseDate__month=4)),
        month5_expense=Sum('expenseMoney', filter=Q(expenseDate__month=5)),
        month6_expense=Sum('expenseMoney', filter=Q(expenseDate__month=6)),
        month7_expense=Sum('expenseMoney', filter=Q(expenseDate__month=7)),
        month8_expense=Sum('expenseMoney', filter=Q(expenseDate__month=8)),
        month9_expense=Sum('expenseMoney', filter=Q(expenseDate__month=9)),
        month10_expense=Sum('expenseMoney', filter=Q(expenseDate__month=10)),
        month11_expense=Sum('expenseMoney', filter=Q(expenseDate__month=11)),
        month12_expense=Sum('expenseMoney', filter=Q(expenseDate__month=12)),
        month_expense=Sum('expenseMoney')
    )

    # 합계
    expenses2 = Expense.objects.filter(
        Q(expenseStatus='Y') &
        Q(expenseDate__year=todayYear) &
        Q(expenseDept__in=dept)
    ).exclude(
        expenseDept='전사'
    ).values(
        'expenseDate__year'
    ).annotate(
        month1_expense=Sum('expenseMoney', filter=Q(expenseDate__month=1)),
        month2_expense=Sum('expenseMoney', filter=Q(expenseDate__month=2)),
        month3_expense=Sum('expenseMoney', filter=Q(expenseDate__month=3)),
        month4_expense=Sum('expenseMoney', filter=Q(expenseDate__month=4)),
        month5_expense=Sum('expenseMoney', filter=Q(expenseDate__month=5)),
        month6_expense=Sum('expenseMoney', filter=Q(expenseDate__month=6)),
        month7_expense=Sum('expenseMoney', filter=Q(expenseDate__month=7)),
        month8_expense=Sum('expenseMoney', filter=Q(expenseDate__month=8)),
        month9_expense=Sum('expenseMoney', filter=Q(expenseDate__month=9)),
        month10_expense=Sum('expenseMoney', filter=Q(expenseDate__month=10)),
        month11_expense=Sum('expenseMoney', filter=Q(expenseDate__month=11)),
        month12_expense=Sum('expenseMoney', filter=Q(expenseDate__month=12)),
        month_expense=Sum('expenseMoney')
    )

    return expenses1, expenses2

def award(year, empDeptName, table2, goal, empName, incentive, empId):
    revenues = Revenue.objects.filter(Q(contractId__empDeptName=empDeptName) & Q(contractId__contractStep='Firm'))
    revenue1 = revenues.filter(Q(billingDate__gte=year + '-01-01') & Q(billingDate__lt=year + '-04-01'))
    revenue2 = revenues.filter(Q(billingDate__gte=year + '-04-01') & Q(billingDate__lt=year + '-07-01'))
    revenue3 = revenues.filter(Q(billingDate__gte=year + '-07-01') & Q(billingDate__lt=year + '-10-01'))
    revenue4 = revenues.filter(Q(billingDate__gte=year + '-10-01') & Q(billingDate__lte=year + '-12-31'))

    # AWARD BONUS
    skewBonusMoney = 1000000
    newAccountBonusMoney = 500000
    q1Skew, q2Skew, q3Skew, q4Skew = 0, 0, 0, 0
    GPachieve = 0

    # GP achieve
    if (revenues.aggregate(sum=Sum('revenueProfitPrice'))['sum'] or 0) >= goal.yearProfitSum:
        GPachieve = 2000000

    # Skew Bonus
    if (revenue1.aggregate(sum=Sum('revenuePrice'))['sum'] or 0) >= goal.salesq1 and (
            revenue1.aggregate(sum=Sum('revenueProfitPrice'))['sum'] or 0) >= goal.profitq1:
        q1Skew = skewBonusMoney
    if (revenue2.aggregate(sum=Sum('revenuePrice'))['sum'] or 0) >= goal.salesq2 and (
            revenue2.aggregate(sum=Sum('revenueProfitPrice'))['sum'] or 0) >= goal.profitq2:
        q2Skew = skewBonusMoney
    if (revenue3.aggregate(sum=Sum('revenuePrice'))['sum'] or 0) >= goal.salesq3 and (
            revenue3.aggregate(sum=Sum('revenueProfitPrice'))['sum'] or 0) >= goal.profitq3:
        q3Skew = skewBonusMoney
    if (revenue4.aggregate(sum=Sum('revenuePrice'))['sum'] or 0) >= goal.salesq4 and (
            revenue4.aggregate(sum=Sum('revenueProfitPrice'))['sum'] or 0) >= goal.profitq4:
        q4Skew = skewBonusMoney

    # New Account Bonus
    new_standard = 50000000
    new_profitratio = 10

    q1NewCount = revenue1.filter(
        Q(contractId__empName=empName) & Q(contractId__newCompany='Y') & Q(contractId__salePrice__gte=new_standard) & Q(
            contractId__profitRatio__gte=new_profitratio))
    q2NewCount = revenue2.filter(
        Q(contractId__empName=empName) & Q(contractId__newCompany='Y') & Q(contractId__salePrice__gte=new_standard) & Q(
            contractId__profitRatio__gte=new_profitratio))
    q3NewCount = revenue3.filter(
        Q(contractId__empName=empName) & Q(contractId__newCompany='Y') & Q(contractId__salePrice__gte=new_standard) & Q(
            contractId__profitRatio__gte=new_profitratio))
    q4NewCount = revenue4.filter(
        Q(contractId__empName=empName) & Q(contractId__newCompany='Y') & Q(contractId__salePrice__gte=new_standard) & Q(
            contractId__profitRatio__gte=new_profitratio))

    newCount = [q1NewCount or None, q2NewCount or None, q3NewCount or None, q4NewCount or None]

    q1New = (q1NewCount.aggregate(count=Count('revenueId'))['count'] or 0) // 3
    q2New = (q1NewCount.aggregate(count=Count('revenueId'))['count'] or 0 +
             q2NewCount.aggregate(count=Count('revenueId'))['count'] or 0) // 3 - q1New
    q3New = (q1NewCount.aggregate(count=Count('revenueId'))['count'] or 0 +
             q2NewCount.aggregate(count=Count('revenueId'))['count'] or 0 +
             q3NewCount.aggregate(count=Count('revenueId'))[
                 'count'] or 0) // 3 - q2New
    q4New = (q1NewCount.aggregate(count=Count('revenueId'))['count'] or 0 +
             q2NewCount.aggregate(count=Count('revenueId'))['count'] or 0 +
             q3NewCount.aggregate(count=Count('revenueId'))[
                 'count'] or 0 + q4NewCount.aggregate(count=Count('revenueId'))['count'] or 0) // 3 - q3New

    # Over Gp Bonus
    gp_standard = 50000000
    gp_profitratio = 15
    gp_maincategory = '상품'

    q1OverGp = revenue1.filter(
        Q(contractId__empName=empName) & Q(contractId__salePrice__gte=gp_standard) & Q(
            contractId__profitRatio__gte=gp_profitratio) & Q(contractId__mainCategory__icontains=gp_maincategory))
    q2OverGp = revenue2.filter(
        Q(contractId__empName=empName) & Q(contractId__salePrice__gte=gp_standard) & Q(
            contractId__profitRatio__gte=gp_profitratio) & Q(contractId__mainCategory__icontains=gp_maincategory))
    q3OverGp = revenue3.filter(
        Q(contractId__empName=empName) & Q(contractId__salePrice__gte=gp_standard) & Q(
            contractId__profitRatio__gte=gp_profitratio) & Q(contractId__mainCategory__icontains=gp_maincategory))
    q4OverGp = revenue4.filter(
        Q(contractId__empName=empName) & Q(contractId__salePrice__gte=gp_standard) & Q(
            contractId__profitRatio__gte=gp_profitratio) & Q(contractId__mainCategory__icontains=gp_maincategory))

    overGp = [q1OverGp or None, q2OverGp or None, q3OverGp or None, q4OverGp or None]
    if newCount == [None, None, None, None]:
        newCount = ''
    if overGp == [None, None, None, None]:
        overGp = ''

    # constraint
    q1constraint, q2constraint, q3constraint, q4constraint = 'X', 'X', 'X', 'X'
    q1expect, q2expect, q3expect, q4expect = 0, 0, 0, 0
    if table2['achieve']['total']['q1'] >= 80:
        q1constraint = 'O'
        q1expect = int(q1Skew + (cal_over_gp(q1OverGp) or 0) + q1New * newAccountBonusMoney)
    if table2['achieve']['total']['q2'] >= 80:
        q2constraint = 'O'
        q2expect = int(q2Skew + (cal_over_gp(q2OverGp) or 0) + q2New * newAccountBonusMoney)
    if table2['achieve']['total']['q3'] >= 80:
        q3constraint = 'O'
        q3expect = int(q3Skew + (cal_over_gp(q3OverGp) or 0) + q3New * newAccountBonusMoney)
    if table2['achieve']['total']['q4'] >= 80:
        q4constraint = 'O'
        q4expect = int(q4Skew + (cal_over_gp(q4OverGp) or 0) + q4New * newAccountBonusMoney)

    table4 = [
        {
            'name': 'Skew Bonus',
            'condition': '분기 목표 달성 시',
            'for': '팀',
            'id': 'skew',
            'q1': int(q1Skew),
            'q2': int(q2Skew),
            'q3': int(q3Skew),
            'q4': int(q4Skew),
        },
        {
            'name': 'Over GP Bonus',
            'condition': '상품의 마진률 15% 이상 Over 시\n(매출 5천만원 이상 건)',
            'for': '개인',
            'id': 'over',
            'q1': int(cal_over_gp(q1OverGp) or 0),
            'q2': int(cal_over_gp(q2OverGp) or 0),
            'q3': int(cal_over_gp(q3OverGp) or 0),
            'q4': int(cal_over_gp(q4OverGp) or 0),
        },
        {
            'name': 'New Account Bonus',
            'condition': '신규 고객 3개 업체 마진률 10% 이상 계약 시\n(매출 5천만원 이상 건)',
            'for': '개인',
            'id': 'new',
            'q1': q1New * newAccountBonusMoney,
            'q2': q2New * newAccountBonusMoney,
            'q3': q3New * newAccountBonusMoney,
            'q4': q4New * newAccountBonusMoney,
        },
        {
            'name': '제약조건',
            'condition': '누적분기80%이상',
            'for': '',
            'id': 'constraint',
            'q1': q1constraint,
            'q2': q2constraint,
            'q3': q3constraint,
            'q4': q4constraint,
        },
        {
            'name': '합계',
            'condition': '예상분기AWARD',
            'for': '',
            'id': 'expect',
            'q1': q1expect,
            'q2': q2expect,
            'q3': q3expect,
            'q4': q4expect,
        },
        {
            'name': '',
            'condition': '확정지급액',
            'for': '',
            'id': 'acheive',
            'q1': int(incentive.get(quarter=1).achieveAward),
            'q2': int(incentive.get(quarter=2).achieveAward),
            'q3': int(incentive.get(quarter=3).achieveAward),
            'q4': int(incentive.get(quarter=4).achieveAward),
        },
    ]

    # 누적 인센티브&어워드 확정 금액
    incentive = Incentive.objects.filter(Q(empId=empId) & Q(year=year))
    sumachieveIncentive = incentive.aggregate(Sum('achieveIncentive'))
    sumachieveAward = incentive.aggregate(Sum('achieveAward'))

    # 인센티브 실적 상세 내역
    incentiveRevenues = revenues.filter(
        Q(billingDate__isnull=False) &
        (
                ~Q(revenuePrice=F('incentivePrice')) |
                ~Q(revenueProfitPrice=F('incentiveProfitPrice'))
        )
    )
    incentiveRevenues = incentiveRevenues.annotate(
        comparePrice=F('revenuePrice') - F('incentivePrice'),
        compareProfitPrice=F('revenueProfitPrice') - F('incentiveProfitPrice')
    )

    return table4, sumachieveIncentive, sumachieveAward, GPachieve, newCount, overGp, incentiveRevenues


daily_report_sql3 = """
    select
        sum(t.A) as A
        , sum(t.B) as B
        , sum(t.A) - sum(t.B) as AmB
        , sum(t.C) as C
        , sum(t.D) as D
        , sum(t.E) as E
        , sum(t.C) + sum(t.D) as CpD
        , sum(t.B) + sum(t.C) + sum(t.D) as F
        , sum(t.A) - (sum(t.B) + sum(t.C) + sum(t.D)) as AmF
    from (
        select
            c.contractId
            , contractName
            , totalRevenuePrice
            , billingRevenuePrice
            , revenueRatio
            , depositRatio
            , coalesce(totalPurchasePrice, 0) as totalPurchasesPrice
            , coalesce(billingPurchasePrice, 0) as billingPurchasePrice
            , coalesce(purchaseRatio, 0) as purchaseRatio
            , coalesce(withdrawRatio, 0) as withdrawRaio
            , A
            , B
            , case
                when revenueRatio > purchaseRatio then round(totalPurchasePrice * (revenueRatio - purchaseRatio))
                else 0
            end as C
            , case
                when revenueRatio < purchaseRatio then round(totalPurchasePrice * (revenueRatio - purchaseRatio))
                else 0
            end as D
            , case
                when depositRatio < withdrawRatio then round(totalPurchasePrice * (depositRatio - withdrawRatio))
                else 0
            end as E
        from sales_contract c

        left join (
            select 
                r1.contractId
                , r1.totalRevenuePrice
                , r1.billingRevenuePrice
                , case
                    when r1.totalRevenuePrice = 0 then 0
                    else r1.billingRevenuePrice*1.0 / r1.totalRevenuePrice
                end as revenueRatio
                , r1.depositRevenuePrice
                , case
                    when r1.totalRevenuePrice = 0 then 0
                    else r1.depositRevenuePrice*1.0 / r1.totalRevenuePrice
                end as depositRatio
                , r1.A
            from (
                select 
                    contractId_id as contractId
                    , sum(revenuePrice) as totalRevenuePrice
                    , sum(
                        case
                            when billingDate is null then 0
                            else revenuePrice
                        end
                    ) as billingRevenuePrice
                    , sum(
                        case
                            when depositDate is null then 0
                            else revenuePrice
                        end
                    ) as depositRevenuePrice
                    , sum(
                        case
                            when billingDate is not null and depositDate is null
                                then revenuePrice
                            else 0
                        end
                    ) as A
                from sales_revenue
                group by contractId_id
            ) r1
        ) r
        on c.contractId = r.contractId

        left join (
            select
                p1.contractId
                , p1.totalPurchasePrice
                , p1.billingPurchasePrice
                , case
                    when totalPurchasePrice = 0 then 0
                    else p1.billingPurchasePrice*1.0 / p1.totalPurchasePrice 
                end as purchaseRatio
                , p1.withdrawPurchasePrice
                , case
                    when totalPurchasePrice = 0 then 0
                    else p1.withdrawPurchasePrice*1.0 / p1.totalPurchasePrice
                end as withdrawRatio
                , B
            from (
                select 
                    contractId_id as contractId
                    , sum(purchasePrice) as totalPurchasePrice
                    , sum(
                        case
                            when billingDate is null then 0
                            else purchasePrice
                        end
                    ) as billingPurchasePrice
                    , sum(
                        case
                            when withdrawDate is null then 0
                            else purchasePrice
                        end
                    ) as withdrawPurchasePrice
                    , sum(
                        case
                            when billingDate is not null and withdrawDate is null
                                then purchasePrice
                            else 0
                        end
                    ) as B
                from sales_purchase
                group by contractId_id
            ) p1
        ) p
        on c.contractId = p.contractId
        where c.salePrice = r.totalRevenuePrice
    ) t;
"""


def magicsearch():
    costCompany = [
        {'id': '법인카드', 'value': '법인카드'},
        {'id': '프로젝트비용', 'value': '프로젝트비용'},
        {'id': 'OMM', 'value': 'OMM'},
        {'id': '금융이자', 'value': '금융이자'},
        {'id': '이자비용', 'value': '이자비용'},
        {'id': '지원금', 'value': '지원금'},
        {'id': '인건비', 'value': '인건비'},
        {'id': '교육비', 'value': '교육비'},
        {'id': '대손상각비', 'value': '대손상각비'},
        {'id': '미정', 'value': '미정'},
    ]

    classificationB = [
        {'id': '상품_HW', 'value': '상품_HW'},
        {'id': '상품_SW', 'value': '상품_SW'},
        {'id': '유지보수_HW', 'value': '유지보수_HW'},
        {'id': '유지보수_SW', 'value': '유지보수_SW'},
        {'id': 'PM상주', 'value': 'PM상주'},
    ]

    classificationC = [
        {'id': '상품_HW', 'value': '상품_HW'},
        {'id': '상품_SW', 'value': '상품_SW'},
        {'id': '유지보수_HW', 'value': '유지보수_HW'},
        {'id': '유지보수_SW', 'value': '유지보수_SW'},
        {'id': 'PM상주', 'value': 'PM상주'},
        {'id': '프로젝트비용', 'value': '프로젝트비용'},
        {'id': '사업진행비용', 'value': '사업진행비용'},
        {'id': '교육', 'value': '교육'},
        {'id': '교육쿠폰', 'value': '교육쿠폰'},
        {'id': '부자재매입', 'value': '부자재매입'},
        {'id': '기타', 'value': '기타'},
    ]

    return costCompany, classificationB, classificationC


def summaryPurchase(contractId, salePrice):
    # 1. 상품_HW = 상품_HW (1)
    # 2. 상품_SW = 상품_SW, DB COSTS (2, 7)
    # 3. 용역_HW = 유지보수_HW, 인력지원_자사_HW, 인력지원_타사_HW(3, 5, 6) - 상품_HW, 유지보수_HW
    # 4. 용역_SW = 유지보수_SW, 인력지원_자사_SW, 인력지원_타사_SW(4, 5, 6) - 상품_SW, 유지보수_SW, PM_상주
    # 5. 기타 = 기타 (8)
    HW_lst = ['상품HW', '유지보수HW']
    SW_lst = ['상품SW', '유지보수SW', 'PM상주']
    sumType1 = 0
    sumType2 = 0
    sumType3 = 0
    sumType4 = 0
    sumType5 = 0

    sumType1 += Purchasetypea.objects.filter(Q(contractId=contractId) & Q(classNumber=1)).aggregate(Sum('price'))['price__sum'] or 0
    sumType2 += Purchasetypea.objects.filter(Q(contractId=contractId) & Q(classNumber=2)).aggregate(Sum('price'))['price__sum'] or 0
    sumType2 += Purchasetyped.objects.filter(Q(contractId=contractId) & Q(classNumber=7)).aggregate(Sum('price'))['price__sum'] or 0
    sumType3 += Purchasetypea.objects.filter(Q(contractId=contractId) & Q(classNumber=3)).aggregate(Sum('price'))['price__sum'] or 0
    sumType3 += Purchasetypeb.objects.filter(Q(contractId=contractId) & Q(classNumber=5) & Q(classification__in=HW_lst)).aggregate(Sum('price'))['price__sum'] or 0
    sumType3 += Purchasetypec.objects.filter(Q(contractId=contractId) & Q(classNumber=6) & Q(classification__in=HW_lst)).aggregate(Sum('price'))['price__sum'] or 0
    sumType4 += Purchasetypea.objects.filter(Q(contractId=contractId) & Q(classNumber=4)).aggregate(Sum('price'))['price__sum'] or 0
    sumType4 += Purchasetypeb.objects.filter(Q(contractId=contractId) & Q(classNumber=5) & Q(classification__in=SW_lst)).aggregate(Sum('price'))['price__sum'] or 0
    sumType4 += Purchasetypec.objects.filter(Q(contractId=contractId) & Q(classNumber=6) & Q(classification__in=SW_lst)).aggregate(Sum('price'))['price__sum'] or 0
    sumType5 += Purchasetypec.objects.filter(Q(contractId=contractId) & Q(classNumber=8)).aggregate(Sum('price'))['price__sum'] or 0

    sumPurchase = sumType1 + sumType2 + sumType3 + sumType4 + sumType5
    profit = salePrice - sumPurchase
    return {'sumPurchase': sumPurchase, 'profit': profit, 'sumType1': sumType1, 'sumType2': sumType2, 'sumType3': sumType3, 'sumType4': sumType4, 'sumType5': sumType5}


def detailPurchase(contractId, classNumber):
    if classNumber in [1, 2, 3, 4]:
        return (
            Purchasetypea.objects.filter(Q(contractId=contractId) & Q(classNumber=classNumber)),
            Purchasetypea.objects.filter(Q(contractId=contractId) & Q(classNumber=classNumber)).aggregate(Sum('price'))['price__sum'] or 0,
        )
    if classNumber in [5]:
        return (
            Purchasetypeb.objects.filter(Q(contractId=contractId) & Q(classNumber=classNumber)),
            Purchasetypeb.objects.filter(Q(contractId=contractId) & Q(classNumber=classNumber)).aggregate(Sum('price'))['price__sum'] or 0,
        )
    if classNumber in [6, 8]:
        return (
            Purchasetypec.objects.filter(Q(contractId=contractId) & Q(classNumber=classNumber)),
            Purchasetypec.objects.filter(Q(contractId=contractId) & Q(classNumber=classNumber)).aggregate(Sum('price'))['price__sum'] or 0,
        )
    if classNumber in [7]:
        return (
            Purchasetyped.objects.filter(Q(contractId=contractId) & Q(classNumber=classNumber)),
            Purchasetyped.objects.filter(Q(contractId=contractId) & Q(classNumber=classNumber)).aggregate(Sum('price'))['price__sum'] or 0,
        )


def date_list(startDatetime, endDatetime):
    startDate = datetime.datetime(year=int(startDatetime[:4]), month=int(startDatetime[5:7]), day=int(startDatetime[8:10]))
    endDate = datetime.datetime(year=int(endDatetime[:4]), month=int(endDatetime[5:7]), day=int(endDatetime[8:10]))
    dateRange = [(startDate + datetime.timedelta(months=x)).date() for x in range(0, (endDate - startDate).days + 1)]
    return dateRange


def billing_schedule(company, date, times, price, profit):
    billing = []
    if price == 0:
        billing_price = 0
    else:
        billing_price = round(price/times)

    if profit == 0:
        billing_profit = 0
    else:
        billing_profit = round(profit/times)

    date = datetime(year=int(date[:4]), month=int(date[5:7]), day=1)
    for billing_times in range(0, times):
        billing_date = date + relativedelta(months=billing_times)
        schedule = {'company': company, 'date': '{}-{}'.format(billing_date.year, str(billing_date.month).zfill(2)), 'times': billing_times, 'price': billing_price, 'profit': billing_profit}
        billing.append(schedule)

    return billing


def mail_purchaseorder(toEmail, fromEmail, orders, purchaseorderfile, relatedpurchaseestimate):
    # smtp 정보
    email = AdminEmail.objects.filter(Q(smtpStatus='정상')).aggregate(Max('adminId'))
    email = AdminEmail.objects.get(Q(adminId=email['adminId__max']))
    # 매입발주서 메일 전송
    try:
        title = "[{}] 매입발주서".format(orders.contractId.contractName)
        html = purchaseorderhtml(orders)
        toEmail = toEmail
        fromEmail = fromEmail

        msg = MIMEMultipart("alternative")
        msg["From"] = fromEmail
        msg["To"] = toEmail
        msg["Subject"] = Header(s=title, charset="utf-8")
        msg.attach(MIMEText(html, "html", _charset="utf-8"))

        # pdf 첨부
        template_path = 'sales/viewpurchaseorderpdf.html'
        template = loader.get_template(template_path)
        context = {
            'orders': orders,
        }
        html = template.render(context)
        src = BytesIO(html.encode('utf-8'))
        dest = BytesIO()

        pdfStatus = pisa.pisaDocument(src, dest, encoding='utf-8', link_callback=link_callback)
        if not pdfStatus.err:
            pdf = dest.getvalue()
            pdffile = MIMEBase("application/pdf", "application/x-pdf")
            pdffile.set_payload(pdf)
            encoders.encode_base64(pdffile)
            pdffile.add_header("Content-Disposition", "attachment", filename=title + '.pdf')
            msg.attach(pdffile)

        # 첨부파일 첨부
        for file in purchaseorderfile:
            path = r'{}{}'.format('media/', file.file)
            part = MIMEBase("application", "octet-stream")
            part.set_payload(open(path, 'rb').read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=os.path.basename(path))
            msg.attach(part)

        # 매입견적서 첨부
        for estimate in relatedpurchaseestimate:
            path = r'{}{}'.format('media/', estimate.purchaseEstimate.file)
            part = MIMEBase("application", "octet-stream")
            part.set_payload(open(path, 'rb').read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=os.path.basename(path))
            msg.attach(part)

        if email.smtpSecure == 'TLS':
            smtp = smtplib.SMTP(email.smtpServer, email.smtpPort)
            smtp.login(email.smtpEmail, email.smtpPassword)
            smtp.sendmail(fromEmail, toEmail, msg.as_string())
            smtp.close()
        elif email.smtpServer == 'SSL':
            smtp = SMTP_SSL("{}:{}".format(email.smtpServer, email.smtpPort))
            smtp.login(email.smtpEmail, email.smtpPassword)
            smtp.sendmail(fromEmail, toEmail, msg.as_string())
            smtp.close()

        return 'Y'
    except Exception as e:
        print(e)
        return e


def purchaseorderhtml(orders):
    html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
    </head>
    <body>
      <div>
        """+ orders.contentHtml + """
      </div>
      <p style="text-align: center; font-size:12px">
        [ 유니원아이앤씨(주) (Unione I&C) ]&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        대표전화 : 02-780-0039&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        Call Center : 02-780-2502&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        Fax : 02-780-2503&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        HomePage : http://www.unioneinc.co.kr/
      </p>
    </body>
    </html>
    """
    return html





