# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from service.models import Servicereport
from sales.models import Contract, Category, Contractitem, Revenue, Goal, Purchase
from hr.models import Employee
from django.db.models import functions
from django.db.models.functions import Coalesce


@login_required
def dashboard_service(request):
    template = loader.get_template('dashboard/dashboardservice.html')

    # 기간 설정 했을 경우
    if request.method == "POST":

        startdate = request.POST['startdate']
        enddate = request.POST['enddate']

    # default : 주 단위 (월~일)
    else:
        today = datetime.today()
        startdate = (today - timedelta(days=today.weekday())).date()
        enddate = startdate + timedelta(days=6)

    if request.user.employee.empDeptName == "임원":
        all_support_data = Servicereport.objects.filter((Q(serviceDate__gte=startdate) &
                                                         Q(serviceDate__lte=enddate)) & (Q(empDeptName='DB지원팀') | Q(empDeptName='솔루션지원팀'))).exclude(serviceType="교육")

        all_support_time = all_support_data.aggregate(Sum('serviceHour'), Count('serviceHour'))

        all_support_Overtime = all_support_data.aggregate(Sum('serviceOverHour'))

        # 고객사별 지원통계
        customer_support_time = Servicereport.objects.values('companyName') \
            .filter(Q(serviceDate__gte=startdate) &
                    Q(serviceDate__lte=enddate)).exclude(serviceType="교육") \
            .annotate(sum_supportTime=Sum('serviceHour'))

        # 엔지니어별 지원통계
        emp_support_time = Servicereport.objects.values('empName') \
            .filter(Q(serviceDate__gte=startdate) &
                    Q(serviceDate__lte=enddate)).exclude(serviceType="교육") \
            .annotate(sum_supportTime=Sum('serviceHour')).annotate(sum_supportCount=Count('empName')).annotate(sum_overTime=Sum('serviceOverHour'))

        # 타입별 지원통계
        type_support_time = Servicereport.objects.values('serviceType') \
            .filter(Q(serviceDate__gte=startdate) &
                    Q(serviceDate__lte=enddate)).exclude(serviceType="교육") \
            .annotate(sum_supportTime=Sum('serviceHour')).order_by('serviceType')

    else:
        # 전체 지원 통계
        all_support_data = Servicereport.objects.filter(Q(serviceDate__gte=startdate) &
                                                        Q(serviceDate__lte=enddate) &
                                                        Q(empDeptName=request.user.employee.empDeptName)).exclude(serviceType="교육")

        all_support_time = all_support_data.aggregate(Sum('serviceHour'), Count('serviceHour'))

        all_support_Overtime = all_support_data.aggregate(Sum('serviceOverHour'))

        # 고객사별 지원통계
        customer_support_time = Servicereport.objects.values('companyName') \
            .filter(Q(serviceDate__gte=startdate) &
                    Q(serviceDate__lte=enddate) &
                    Q(empDeptName=request.user.employee.empDeptName)).exclude(serviceType="교육") \
            .annotate(sum_supportTime=Sum('serviceHour'))

        # 엔지니어별 지원통계
        emp_support_time = Servicereport.objects.values('empName') \
            .filter(Q(serviceDate__gte=startdate) &
                    Q(serviceDate__lte=enddate) &
                    Q(empDeptName=request.user.employee.empDeptName)).exclude(serviceType="교육") \
            .annotate(sum_supportTime=Sum('serviceHour')).annotate(sum_supportCount=Count('empName')).annotate(sum_overTime=Sum('serviceOverHour'))

        # 타입별 지원통계
        type_support_time = Servicereport.objects.values('serviceType') \
            .filter(Q(serviceDate__gte=startdate) &
                    Q(serviceDate__lte=enddate) &
                    Q(empDeptName=request.user.employee.empDeptName)).exclude(serviceType="교육") \
            .annotate(sum_supportTime=Sum('serviceHour')).order_by('serviceType')

    type_count = [i for i in range(len(type_support_time))]
    multi_type = zip(type_support_time, type_count)

    context = {
        'startdate': startdate,
        'enddate': enddate,
        'customer_support_time': customer_support_time,
        'emp_support_time': emp_support_time,
        'type_support_time': type_support_time,
        'multi_type': multi_type,
        'all_support_data': all_support_data,
        'all_support_time': all_support_time,
        'all_support_Overtime': all_support_Overtime
    }
    return HttpResponse(template.render(context, request))


@login_required
def over_hour(request):
    template = loader.get_template('dashboard/overhourlist.html')

    if request.method == "POST":
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        filter = 'Y'


    else:
        startdate = ''
        enddate = ''
        filter = 'N'

    context = {
        'filter': filter,
        'startdate': startdate,
        'enddate': enddate,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def over_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    overHour = Servicereport.objects.filter(Q(serviceOverHour__gt=0) & Q(serviceStatus='Y') & (Q(empDeptName='DB지원팀') | Q(empDeptName='솔루션지원팀')))
    if startdate:
        overHour = overHour.filter(Q(serviceDate__gte=startdate))
    if enddate:
        overHour = overHour.filter(Q(serviceDate__lte=enddate))

    overHourlist = overHour.values('serviceStartDatetime', 'serviceEndDatetime', 'empName', 'empDeptName', 'companyName', 'serviceOverHour', 'serviceId')
    structure = json.dumps(list(overHourlist), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def dashboard_opportunity(request):
    template = loader.get_template('dashboard/dashboardopportunity.html')
    if request.method == "POST":
        startdate = "{}-01-01".format(datetime.today().year)
        enddate = "{}-12-31".format(datetime.today().year)
        contract = Contract.objects.filter(Q(contractDate__gte=startdate) & Q(contractDate__lte=enddate))
        context = {
            "startdate": startdate,
            "enddate": enddate,
            "contract": contract,
            'filter': 'Y',
        }
    else:
        startdate = "{}-01-01".format(datetime.today().year)
        enddate = "{}-12-31".format(datetime.today().year)
        contract = Contract.objects.all()
        contract_opp = contract.values('contractStep').filter(contractStep='Opportunity').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice'))
        contract_firm = contract.values('contractStep').filter(contractStep='Firm').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice'))
        contract_company = contract.values('endCompanyName')
        allsalePrice = 0
        allprofitPrice = 0

        for i in contract_firm:
            allsalePrice += i['sum_price']
            allprofitPrice += i['sum_profit']
        for i in contract_opp:
            allsalePrice += i['sum_price']
            allprofitPrice += i['sum_profit']
        context = {
            "startdate": startdate,
            "enddate": enddate,
            "contract_company": contract_company,
            "contract_count": contract.count(),
            "allsalePrice": allsalePrice,
            "allprofitPrice": allprofitPrice,
            'filter': 'N',
        }
    return HttpResponse(template.render(context, request))


@login_required
def dashboard_quarter(request):
    template = loader.get_template('dashboard/dashboardquarter.html')

    # 연도, 월, 분기
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

    dict_quarter = {"q1_start": "{}-01-01".format(todayYear),
                    "q1_end": "{}-04-01".format(todayYear),
                    "q2_end": "{}-07-01".format(todayYear),
                    "q3_end": "{}-10-01".format(todayYear),
                    "q4_end": "{}-01-01".format(todayYear + 1)}

    # 목표 매출금액 & 이익금액
    goal = Goal.objects.filter(year=todayYear)
    salesTarget = goal.aggregate(sum=Sum('yearSalesSum'))['sum']
    profitTarget = goal.aggregate(sum=Sum('yearProfitSum'))['sum']

    salesQuarterTarget = goal.aggregate(sum=Sum('salesq1'))['sum']
    profitQuarterTarget = goal.aggregate(sum=Sum('profitq1'))['sum']
    if todayQuarter >= 2:
        salesQuarterTarget += goal.aggregate(sum=Sum('salesq2'))['sum']
        profitQuarterTarget += goal.aggregate(sum=Sum('profitq2'))['sum']
    if todayQuarter >= 3:
        salesQuarterTarget += goal.aggregate(sum=Sum('salesq3'))['sum']
        profitQuarterTarget += goal.aggregate(sum=Sum('profitq3'))['sum']
    if todayQuarter >= 4:
        salesQuarterTarget += goal.aggregate(sum=Sum('salesq4'))['sum']
        profitQuarterTarget += goal.aggregate(sum=Sum('profitq4'))['sum']

    # 매출
    contract = Contract.objects.all()
    revenues = Revenue.objects.all()

    firmRevenuePrice = revenues.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q4_end']) & Q(contractId__contractStep='Firm'))
    oppRevenuePrice = revenues.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q4_end']) & Q(contractId__contractStep='Opportunity'))

    if todayQuarter == 1:
        revenuesAccumulate = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end']))
        revenuesQuarter = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end']))
    elif todayQuarter == 2:
        revenuesAccumulate = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q2_end']))
        revenuesQuarter = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_end']) & Q(predictBillingDate__lt=dict_quarter['q2_end']))
    elif todayQuarter == 3:
        revenuesAccumulate = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q3_end']))
        revenuesQuarter = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q2_end']) & Q(predictBillingDate__lt=dict_quarter['q3_end']))
    elif todayQuarter == 4:
        revenuesAccumulate = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q4_end']))
        revenuesQuarter = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q3_end']) & Q(predictBillingDate__lt=dict_quarter['q4_end']))

    # 메인카테고리&서브카테고리
    maincategoryRevenuePrice = firmRevenuePrice.values('contractId__mainCategory').annotate(sumMainPrice=Sum('revenuePrice'), sumMainProfitPrice=Sum('revenueProfitPrice'))

    # 누적매출금액 & 이익 금액
    cumulativeSalesAmount = firmRevenuePrice.aggregate(sum=Sum('revenuePrice'))['sum']
    cumulativeProfitAmount = firmRevenuePrice.aggregate(cumulative_profit_amount=Sum('revenueProfitPrice') or 0)

    # 현재 분기까지 누적매출금액 & 이익 금액
    quarterlyCumulativeSales = revenuesAccumulate.aggregate(quarterly_cumulative_sales=Sum('revenuePrice'))
    quarterlyCumulativeProfit = revenuesAccumulate.aggregate(quarterly_cumulative_profit=Sum('revenueProfitPrice'))

    # 현재 분기 매출금액 & 이익 금액
    quarterlySales = revenuesQuarter.aggregate(quarterly_sales=Sum('revenuePrice'))
    quarterlyProfit = revenuesQuarter.aggregate(quarterly_profit=Sum('revenueProfitPrice'))

    # 분기별 opportunity & Firm
    # 분기 opp
    quarter1Oppty = oppRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end'])).aggregate(sum=Sum('revenuePrice'),
                                                                                                                                                             sum_profit=Sum('revenueProfitPrice'))
    quarter2Oppty = oppRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_end']) & Q(predictBillingDate__lt=dict_quarter['q2_end'])).aggregate(sum=Sum('revenuePrice'),
                                                                                                                                                           sum_profit=Sum('revenueProfitPrice'))
    quarter3Oppty = oppRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q2_end']) & Q(predictBillingDate__lt=dict_quarter['q3_end'])).aggregate(sum=Sum('revenuePrice'),
                                                                                                                                                           sum_profit=Sum('revenueProfitPrice'))
    quarter4Oppty = oppRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q3_end']) & Q(predictBillingDate__lt=dict_quarter['q4_end'])).aggregate(sum=Sum('revenuePrice'),
                                                                                                                                                           sum_profit=Sum('revenueProfitPrice'))
    quarterOpptySum = [quarter1Oppty['sum'], quarter2Oppty['sum'], quarter3Oppty['sum'], quarter4Oppty['sum']]
    quarterOpptyProfitSum = [quarter1Oppty['sum_profit'], quarter2Oppty['sum_profit'], quarter3Oppty['sum_profit'], quarter4Oppty['sum_profit']]
    quarterOppty = [0 if quarterOpptySum[i] == None else quarterOpptySum[i] for i in range(len(quarterOpptySum))]
    quarterOpptyProfit = [0 if quarterOpptyProfitSum[i] == None else quarterOpptyProfitSum[i] for i in range(len(quarterOpptyProfitSum))]

    # 분기 Firm
    quarter1Firm = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter2Firm = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_end']) & Q(predictBillingDate__lt=dict_quarter['q2_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter3Firm = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q2_end']) & Q(predictBillingDate__lt=dict_quarter['q3_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter4Firm = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q3_end']) & Q(predictBillingDate__lt=dict_quarter['q4_end'])).aggregate(sum=Sum('revenuePrice'))
    quarterFirmSum = [quarter1Firm['sum'], quarter2Firm['sum'], quarter3Firm['sum'], quarter4Firm['sum']]
    quarterFirm = [0 if quarterFirmSum[i] == None else quarterFirmSum[i] for i in range(len(quarterFirmSum))]

    ### 해당 분기 누적 opp&firm
    quarterOpptyFirm = [sum(quarterOppty[0:todayQuarter]), sum(quarterFirm[0:todayQuarter])]

    ###월별 팀 매출 금액
    salesteamList = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    salesteamList = [x['empDeptName'] for x in salesteamList if "영업" in x['empDeptName']]

    ###월별 팀 매출 금액
    teamRevenues = firmRevenuePrice.values('predictBillingDate__month', 'contractId__empDeptName'
                                           ).annotate(Sum('revenuePrice')).order_by('contractId__empDeptName', 'predictBillingDate__month')
    teamRevenues = list(teamRevenues)

    for i in salesteamList:
        monthList = [i for i in range(1, 13)]
        for j in teamRevenues:
            if j['contractId__empDeptName'] == i:
                monthList.remove(j['predictBillingDate__month'])
        for m in monthList:
            teamRevenues.append({'predictBillingDate__month': m, 'contractId__empDeptName': i, 'revenuePrice__sum': 0})

    teamRevenues.sort(key=lambda x: x['contractId__empDeptName'], reverse=False)
    teamRevenues.sort(key=lambda x: x['predictBillingDate__month'], reverse=False)

    ###전체 매출/이익 금액(opp&firm)
    opptyFirmSales = cumulativeSalesAmount + sum(quarterOppty)
    opptyFirmProfits = cumulativeProfitAmount['cumulative_profit_amount'] + sum(quarterOpptyProfit)

    ###분기 누적 매출/이익  금액(opp&firm)
    quarterOpptyFirmSales = quarterlyCumulativeSales['quarterly_cumulative_sales'] + sum(quarterOppty[0:todayQuarter])
    quarterOpptyFirmProfits = quarterlyCumulativeProfit['quarterly_cumulative_profit'] + sum(quarterOpptyProfit[0:todayQuarter])

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
        startdate = dict_quarter['q1_start']
        enddate = dict_quarter['q4_end']
        contractStep = ''
        empDeptName = ''
        empName = ''
        saleCompanyName = ''
        endCompanyName = ''
        contractName = ''

    context = {
        "todayYear": todayYear,
        "todayQuarter": todayQuarter,
        "salesTarget": salesTarget,
        "profitTarget": profitTarget,
        "salesQuarterTarget": salesQuarterTarget,
        "profitQuarterTarget": profitQuarterTarget,
        "Sales_rate": round(cumulativeSalesAmount / salesTarget * 100, 2),
        "Profit_rate": round(cumulativeProfitAmount['cumulative_profit_amount'] / profitTarget * 100, 2),
        "Salesquater_rate": round(quarterlyCumulativeSales['quarterly_cumulative_sales'] / salesQuarterTarget * 100, 2),
        "Profitquater_rate": round(quarterlyCumulativeProfit['quarterly_cumulative_profit'] / profitQuarterTarget * 100, 2),
        "cumulative_sales_amount": cumulativeSalesAmount,
        "cumulative_profit_amount": cumulativeProfitAmount['cumulative_profit_amount'],
        "quarterly_cumulative_sales": quarterlyCumulativeSales['quarterly_cumulative_sales'],
        "quarterly_cumulative_profit": quarterlyCumulativeProfit['quarterly_cumulative_profit'],
        "quarterly_sales": quarterlySales['quarterly_sales'],
        "quarterly_profit": quarterlyProfit['quarterly_profit'],
        "opp_firm_sales": opptyFirmSales,
        "opp_firm_profits": opptyFirmProfits,
        "opp_firm_sales_rate": round(opptyFirmSales / salesTarget * 100, 2),
        "opp_firm_profits_rate": round(opptyFirmProfits / profitTarget * 100, 2),
        "quarter_opp_firm_sales": quarterOpptyFirmSales,
        "quarter_opp_firm_profits": quarterOpptyFirmProfits,
        "quarter_opp_firm_sales_rate": round(quarterOpptyFirmSales / salesQuarterTarget * 100, 2),
        "quarter_opp_firm_profits_rate": round(quarterOpptyFirmProfits / profitQuarterTarget * 100, 2),
        "quarter_opp": quarterOppty,
        "quarter_firm": quarterFirm,
        "team_revenues": teamRevenues,
        "quarter_opp_Firm": quarterOpptyFirm,
        'startdate': startdate,
        'enddate': enddate,
        'contractStep': contractStep,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'endCompanyName': endCompanyName,
        'contractName': contractName,
        'maincategoryRevenuePrice': maincategoryRevenuePrice,

    }
    return HttpResponse(template.render(context, request))


@login_required
def dashboard_goal(request):
    template = loader.get_template('dashboard/dashboardgoal.html')
    todayYear = datetime.today().year
    dictQuarter = {"q1_start": "{}-01-01".format(todayYear),
                   "q1_end": "{}-04-01".format(todayYear),
                   "q2_end": "{}-07-01".format(todayYear),
                   "q3_end": "{}-10-01".format(todayYear),
                   "q4_end": "{}-01-01".format(todayYear + 1)}
    salesteamList = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    salesteamList = [x['empDeptName'] for x in salesteamList if "영업" in x['empDeptName']]
    revenues = Revenue.objects.filter(Q(predictBillingDate__year=todayYear) & Q(contractId__contractStep='Firm'))

    ## 팀별 목표 & 전체 매출 금액
    # teamGoals = Goal.objects.filter(Q(empDeptName__icontains='영업') & Q(year=todayYear))
    teamGoals = Goal.objects.filter(Q(year=todayYear))
    teamGoalsSum = teamGoals.aggregate(sum_yearSales=Sum('yearSalesSum'), sum_yearProfit=Sum('yearProfitSum'), sum_salesq1=Sum('salesq1'), sum_salesq2=Sum('salesq2'),
                                       sum_salesq3=Sum('salesq3'), sum_salesq4=Sum('salesq3'), sum_profitq1=Sum('profitq1'), sum_profitq2=Sum('profitq2'),
                                       sum_profitq3=Sum('profitq4'), sum_profitq4=Sum('profitq4'))
    teamSales = []
    for i in salesteamList:
        sales = revenues.filter(Q(contractId__empDeptName=i) & Q(predictBillingDate__year=todayYear)).values('contractId__empDeptName').aggregate(sum_sales=Sum('revenuePrice'),
                                                                                                                                                  sum_profits=Sum('revenueProfitPrice'))
        teamSales.append({i: sales})

    for i in salesteamList:
        # 분기 Firm
        if i == '영업1팀':
            team1Revenues = revenues.filter(Q(contractId__empDeptName=i)).values('predictBillingDate__month', 'contractId__empDeptName'
                                                                                 ).annotate(Sum('revenuePrice')).order_by('contractId__empDeptName', 'predictBillingDate__month')
            quarter1Revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(predictBillingDate__gte=dictQuarter['q1_start']) & Q(predictBillingDate__lt=dictQuarter['q1_end'])) \
                .aggregate(sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter2Revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(predictBillingDate__gte=dictQuarter['q1_end']) & Q(predictBillingDate__lt=dictQuarter['q2_end'])) \
                .aggregate(sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter3Revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(predictBillingDate__gte=dictQuarter['q2_end']) & Q(predictBillingDate__lt=dictQuarter['q3_end'])) \
                .aggregate(sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter4Revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(predictBillingDate__gte=dictQuarter['q3_end']) & Q(predictBillingDate__lt=dictQuarter['q4_end'])) \
                .aggregate(sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarterFirmTeam1RevenuePrice = [quarter1Revenues['sum_sales'], quarter2Revenues['sum_sales'], quarter3Revenues['sum_sales'], quarter4Revenues['sum_sales']]
            quarterFirmTeam1RevenueProfitPrice = [quarter1Revenues['sum_profits'], quarter2Revenues['sum_profits'], quarter3Revenues['sum_profits'], quarter4Revenues['sum_profits']]
            quarterFirmTeam1Sales = [0 if quarterFirmTeam1RevenuePrice[i] == None else quarterFirmTeam1RevenuePrice[i] for i in range(len(quarterFirmTeam1RevenuePrice))]
            quarterFirmTeam1Profits = [0 if quarterFirmTeam1RevenueProfitPrice[i] == None else quarterFirmTeam1RevenueProfitPrice[i] for i in
                                       range(len(quarterFirmTeam1RevenueProfitPrice))]

        elif i == '영업2팀':
            team2Revenues = revenues.filter(Q(contractId__empDeptName=i)).values('predictBillingDate__month', 'contractId__empDeptName'
                                                                                 ).annotate(Sum('revenuePrice')).order_by('contractId__empDeptName', 'predictBillingDate__month')
            quarter1Revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(predictBillingDate__gte=dictQuarter['q1_start']) & Q(predictBillingDate__lt=dictQuarter['q1_end'])) \
                .aggregate(
                sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter2Revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(predictBillingDate__gte=dictQuarter['q1_end']) & Q(predictBillingDate__lt=dictQuarter['q2_end'])) \
                .aggregate(
                sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter3Revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(predictBillingDate__gte=dictQuarter['q2_end']) & Q(predictBillingDate__lt=dictQuarter['q3_end'])) \
                .aggregate(
                sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter4Revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(predictBillingDate__gte=dictQuarter['q3_end']) & Q(predictBillingDate__lt=dictQuarter['q4_end'])) \
                .aggregate(
                sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarterFirmTeam2RevenuePrice = [quarter1Revenues['sum_sales'], quarter2Revenues['sum_sales'], quarter3Revenues['sum_sales'], quarter4Revenues['sum_sales']]
            quarterFirmTeam2RevenueProfitPrice = [quarter1Revenues['sum_profits'], quarter2Revenues['sum_profits'], quarter3Revenues['sum_profits'], quarter4Revenues['sum_profits']]
            quarterFirmTeam2Sales = [0 if quarterFirmTeam2RevenuePrice[i] == None else quarterFirmTeam2RevenuePrice[i] for i in range(len(quarterFirmTeam2RevenuePrice))]
            quarterFirmTeam2Profits = [0 if quarterFirmTeam1RevenueProfitPrice[i] == None else quarterFirmTeam2RevenueProfitPrice[i] for i in
                                       range(len(quarterFirmTeam2RevenueProfitPrice))]

    ###월별 팀 매출 금액
    team1Revenues = list(team1Revenues)
    team2Revenues = list(team2Revenues)
    team1MonthList = [i for i in range(1, 13)]
    team2MonthList = [i for i in range(1, 13)]
    for j in team1Revenues:
        team1MonthList.remove(j['predictBillingDate__month'])
    for m in team1MonthList:
        team1Revenues.append({'predictBillingDate__month': m, 'revenuePrice__sum': 0})
    for j in team2Revenues:
        team2MonthList.remove(j['predictBillingDate__month'])
    for m in team2MonthList:
        team2Revenues.append({'predictBillingDate__month': m, 'revenuePrice__sum': 0})

    team1Revenues.sort(key=lambda x: x['predictBillingDate__month'], reverse=False)
    team2Revenues.sort(key=lambda x: x['predictBillingDate__month'], reverse=False)
    context = {
        "year": todayYear,
        "teamGoals": teamGoals,
        "teamSales": teamSales,
        "quarterFirmTeam1Sales": quarterFirmTeam1Sales,
        "quarterFirmTeam1Profits": quarterFirmTeam1Profits,
        "quarterFirmTeam2Sales": quarterFirmTeam2Sales,
        "quarterFirmTeam2Profits": quarterFirmTeam2Profits,
        "team1Revenues": team1Revenues,
        "team2Revenues": team2Revenues,
        "teamGoalsSum": teamGoalsSum
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def opportunity_graph(request):
    todayYear = datetime.today().year
    step = request.POST['step']
    maincategory = request.POST['maincategory']

    dataFirm = Revenue.objects.filter(Q(predictBillingDate__year=todayYear) & Q(contractId__contractStep=step) & Q(contractId__mainCategory=maincategory))

    subCategory = dataFirm.values('contractId__subCategory').annotate(sum_sub=Sum('revenuePrice'))

    structure = json.dumps(list(subCategory), cls=DjangoJSONEncoder)

    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def opportunity_asjson(request):
    today_year = datetime.today().year
    step = request.POST['step']
    maincategory = request.POST['maincategory']
    subcategory = request.POST['subcategory']
    emp = request.POST['emp']
    customer = request.POST['customer']

    contract = Contract.objects.filter(Q(contractDate__year=today_year))
    contractitem = Contractitem.objects.all()

    if step:
        contract = contract.filter(contractStep=step)
        contractitem = contractitem.filter(contractId__contractStep=step)

    if maincategory:
        contract = contract.filter(contractitem__mainCategory=maincategory)
        contractitem = contractitem.filter(mainCategory=maincategory)

    if subcategory:
        contract = contract.filter(contractitem__subCategory=subcategory)
        contractitem = contractitem.filter(subCategory=subcategory)

    if emp:
        contract = contract.filter(empDeptName=emp)
        contractitem = contractitem.filter(contractId__empDeptName=emp)

    if customer:
        contract = contract.filter(endCompanyName=customer)
        contractitem = contractitem.filter(contractId__endCompanyName=customer)

    json = serializers.serialize('json', contract)

    return HttpResponse(json, content_type='application/json')


@login_required
@csrf_exempt
def quarter_asjson(request):
    todayYear = datetime.today().year
    dict_quarter = {"q1_start": "{}-01-01".format(todayYear),
                    "q1_end": "{}-04-01".format(todayYear),
                    "q2_end": "{}-07-01".format(todayYear),
                    "q3_end": "{}-10-01".format(todayYear),
                    "q4_end": "{}-01-01".format(todayYear + 1)}
    print(request.POST)
    step = request.POST['step']
    team = request.POST['team']
    if team == '합계':
        team = ''
    month = request.POST['month'].replace('월', '')
    cumulative = request.POST['cumulative']
    quarter = request.POST['quarter']
    maincategory = request.POST['maincategory']
    subcategory = request.POST['subcategory']

    dataFirm = Revenue.objects.filter(Q(predictBillingDate__year=todayYear) & Q(contractId__contractStep=step))

    if quarter:
        if cumulative == 'Y':
            if quarter == '1분기':
                dataFirm = dataFirm.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end']))
            elif quarter == '2분기':
                dataFirm = dataFirm.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q2_end']))
            elif quarter == '3분기':
                dataFirm = dataFirm.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q3_end']))
            elif quarter == '4분기':
                dataFirm = dataFirm.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q4_end']))
        elif cumulative == 'N':
            if quarter == '1분기':
                dataFirm = dataFirm.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end']))
            elif quarter == '2분기':
                dataFirm = dataFirm.filter(Q(predictBillingDate__gte=dict_quarter['q1_end']) & Q(predictBillingDate__lt=dict_quarter['q2_end']))
            elif quarter == '3분기':
                dataFirm = dataFirm.filter(Q(predictBillingDate__gte=dict_quarter['q2_end']) & Q(predictBillingDate__lt=dict_quarter['q3_end']))
            elif quarter == '4분기':
                dataFirm = dataFirm.filter(Q(predictBillingDate__gte=dict_quarter['q3_end']) & Q(predictBillingDate__lt=dict_quarter['q4_end']))

    if team:
        dataFirm = dataFirm.filter(Q(contractId__empDeptName=team))

    if month:
        dataFirm = dataFirm.filter(Q(predictBillingDate__month=month))

    if maincategory:
        if subcategory:
            dataFirm = dataFirm.filter(Q(contractId__mainCategory=maincategory) & Q(contractId__subCategory=subcategory))
        else:
            dataFirm = dataFirm.filter(Q(contractId__mainCategory=maincategory))

    dataFirm = dataFirm.values('predictBillingDate', 'contractId__contractCode', 'contractId__contractName', 'contractId__saleCompanyName__companyName', 'revenuePrice', 'revenueProfitPrice',
                               'contractId__empName', 'contractId__empDeptName', 'revenueId')

    print(dataFirm)
    structureStep = json.dumps(list(dataFirm), cls=DjangoJSONEncoder)
    return HttpResponse(structureStep, content_type='application/json')


def dashboard_credit(request):
    template = loader.get_template('dashboard/dashboardcredit.html')
    todayYear = datetime.today().year
    # 해당 년도 매출
    revenues = Revenue.objects.filter(Q(predictBillingDate__year=todayYear) & Q(billingDate__isnull=False))
    # 월별 미수금액 / 수금액
    revenuesMonth = revenues.values('predictBillingDate__month') \
        .annotate(outstandingCollectionsMonth=Coalesce(Sum('revenuePrice', filter=Q(billingDate__isnull=False) & Q(depositDate__isnull=True)), 0)
                  , collectionofMoneyMonth=Coalesce(Sum('revenuePrice', filter=Q(depositDate__isnull=False)), 0)).order_by('predictBillingDate__month')
    # 총 미수금액 / 수금액
    revenuesTotal = revenuesMonth.aggregate(outstandingCollectionsTotal=Sum('outstandingCollectionsMonth')
                                            , collectionofMoneyTotal=Sum('collectionofMoneyMonth'))
    # 해당 년도 매입
    purchases = Purchase.objects.filter(Q(predictBillingDate__year=todayYear) & Q(billingDate__isnull=False))
    # 월별 미지급액 / 지급액
    purchasesMonth = purchases.values('predictBillingDate__month').annotate(accountsPayablesMonth=Coalesce(Sum('purchasePrice', filter=Q(billingDate__isnull=False) & Q(withdrawDate__isnull=True)), 0)
                                                                            , amountPaidMonth=Coalesce(Sum('purchasePrice', filter=Q(withdrawDate__isnull=False)), 0)).order_by('predictBillingDate__month')
    # 총 미지급액
    purchasesTotal = purchasesMonth.aggregate(accountsPayablesTotal=Sum('accountsPayablesMonth')
                                              , amountPaidTotal=Sum('amountPaidMonth'))
    context = {
        'revenuesTotal': revenuesTotal,
        'revenuesMonth': revenuesMonth,
        'purchasesTotal': purchasesTotal,
        'purchasesMonth': purchasesMonth,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def cashflow_asjson(request):
    todayYear = datetime.today().year
    outstandingCollections = request.POST['outstandingCollections']
    accountsPayables = request.POST['accountsPayables']
    month = request.POST['month'][:-1]

    if outstandingCollections:
        cashflow = Revenue.objects.filter(Q(predictBillingDate__year=todayYear) & Q(predictBillingDate__month=month) & Q(billingDate__isnull=False) & Q(depositDate__isnull=True))
        cashflow = cashflow.values('billingDate', 'contractId__contractCode', 'contractId__contractName', 'contractId__saleCompanyName__companyName', 'revenuePrice', 'revenueProfitPrice',
                                   'contractId__empName', 'contractId__empDeptName', 'revenueId', 'predictBillingDate', 'predictDepositDate', 'depositDate', 'contractId__contractStep',
                                   'contractId__depositCondition', 'contractId__depositConditionDay', 'comment')

    if accountsPayables:
        cashflow = Purchase.objects.filter(Q(predictBillingDate__year=todayYear) & Q(predictBillingDate__month=month) & Q(billingDate__isnull=False) & Q(withdrawDate__isnull=True))
        cashflow = cashflow.values('contractId__contractName', 'purchaseCompany', 'contractId__contractCode', 'predictBillingDate', 'billingDate', 'purchasePrice',
                                   'predictWithdrawDate', 'withdrawDate', 'purchaseId', 'contractId__empDeptName', 'contractId__empName', 'contractId__contractStep', 'comment')

    structureStep = json.dumps(list(cashflow), cls=DjangoJSONEncoder)
    return HttpResponse(structureStep, content_type='application/json')


@login_required
@csrf_exempt
def service_asjson(request):
    startdate = request.POST['startdate'].replace('.', '-')
    enddate = request.POST['enddate'].replace('.', '-')
    company = request.POST['company']
    empname = request.POST['empname']
    servicetype = request.POST['servicetype']
    overhour = request.POST['overhour']

    services = Servicereport.objects.filter(Q(serviceDate__gte=startdate) & Q(serviceDate__lte=enddate))

    if company:
        services = services.filter(Q(companyName=company))

    if company:
        services = services.filter(Q(companyName=company))

    if empname:
        services = services.filter(Q(empName=empname))

    if servicetype:
        services = services.filter(Q(serviceType=servicetype))

    if overhour:
        services = services.exclude(serviceOverHour=0)

    services = services.values()

    structureStep = json.dumps(list(services), cls=DjangoJSONEncoder)
    return HttpResponse(structureStep, content_type='application/json')
