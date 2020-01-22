from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Case, When, Value, CharField, Min, Max, IntegerField
from django.db.models.functions import Coalesce
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from service.models import Servicereport, Geolocation
from service.functions import dayreport_query2, dayreport_query
from sales.models import Contract, Contractitem, Revenue, Goal, Purchase
from hr.models import Employee
from django.db.models.functions import Coalesce
from usone.security import MAP_KEY, testMAP_KEY


@login_required
def dashboard_service(request):
    template = loader.get_template('dashboard/dashboardservice.html')

    # 기간 설정 했을 경우
    if request.method == "POST":

        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        empDeptName = request.POST['empDeptName']

    # default : 월 단위 (월~일)
    else:
        today = datetime.today()
        startdate = datetime(today.year, today.month, 1).date()
        enddate = startdate + relativedelta(months=1) - relativedelta(days=1)
        empDeptName = ''

    all_support_data = Servicereport.objects.filter(Q(serviceStatus='Y')).exclude(serviceType__dashboardStatus='N').exclude(empDeptName__icontains='영업')

    if startdate:
        all_support_data = all_support_data.filter(Q(serviceDate__gte=startdate))

    if enddate:
        all_support_data = all_support_data.filter(Q(serviceDate__lte=enddate))

    if empDeptName:
        all_support_data = all_support_data.filter(Q(empDeptName__icontains=empDeptName))

    all_support_time = all_support_data.aggregate(Sum('serviceHour'), Count('serviceHour'))

    all_support_Overtime = all_support_data.aggregate(Sum('serviceOverHour'))

    # 고객사별 지원통계
    customer_support_time = all_support_data.values('companyName').annotate(sum_supportTime=Sum('serviceHour')).order_by('-sum_supportTime')

    # 엔지니어별 지원통계
    emp_support_time = all_support_data.values('empName').annotate(sum_supportTime=Sum('serviceHour'))\
                                                        .annotate(sum_supportCount=Count('empName'))\
                                                        .annotate(sum_overTime=Sum('serviceOverHour'))
    # 타입별 지원통계
    type_support_time = all_support_data.values('serviceType__typeName').annotate(sum_supportTime=Sum('serviceHour')).order_by('serviceType__typeName')


    type_count = [i for i in range(len(type_support_time))]
    multi_type = zip(type_support_time, type_count)

    context = {
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
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
    if request.method == 'POST':
        todayYear = int(request.POST['searchYear'])
        todayMonth = 12
        if todayYear == datetime.today().year:
            todayYear = datetime.today().year
            todayMonth = datetime.today().month
    else:
        todayYear = datetime.today().year
        todayMonth = datetime.today().month

    # 전체 목표
    goals = Goal.objects.filter(Q(year=todayYear) & Q(empName='전체'))
    sumGoals = goals.aggregate(
        yearSalesSum=Sum('yearSalesSum'), yearProfitSum=Sum('yearProfitSum'),
        salesq1=Sum('salesq1'), salesq2=Sum('salesq2'), salesq3=Sum('salesq3'), salesq4=Sum('salesq4'),
        profitq1=Sum('profitq1'), profitq2=Sum('profitq2'), profitq3=Sum('profitq3'), profitq4=Sum('profitq4'),
        sales1=Sum('sales1'), sales2=Sum('sales2'), sales3=Sum('sales3'), sales4=Sum('sales4'), sales5=Sum('sales5'), sales6=Sum('sales6'),
        sales7=Sum('sales7'), sales8=Sum('sales8'), sales9=Sum('sales9'), sales10=Sum('sales10'), sales11=Sum('sales11'), sales12=Sum('sales12'),
        profit1=Sum('profit1'), profit2=Sum('profit2'), profit3=Sum('profit3'), profit4=Sum('profit4'), profit5=Sum('profit5'), profit6=Sum('profit6'),
        profit7=Sum('profit7'), profit8=Sum('profit8'), profit9=Sum('profit9'), profit10=Sum('profit10'), profit11=Sum('profit11'), profit12=Sum('profit12'),
    )
    cumulativeGoalSalePrice = 0
    cumulativeGoalProfitPrice = 0
    # 해당 분기 월 리스트
    monthList = []
    # 연도, 월, 분기
    if todayMonth in [1, 2, 3]:
        todayQuarter = 1
        monthList = [1, 2, 3]
        if sumGoals['yearSalesSum'] or sumGoals['yearProfitSum']:
            cumulativeGoalSalePrice = sumGoals['salesq1']
            cumulativeGoalProfitPrice = sumGoals['profitq1']
    elif todayMonth in [4, 5, 6]:
        todayQuarter = 2
        monthList = [1, 2, 3, 4, 5, 6]
        if sumGoals['yearSalesSum'] or sumGoals['yearProfitSum']:
            cumulativeGoalSalePrice = sumGoals['salesq1'] + sumGoals['salesq2']
            cumulativeGoalProfitPrice = sumGoals['profitq1'] + sumGoals['profitq2']
    elif todayMonth in [7, 8, 9]:
        todayQuarter = 3
        monthList = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        if sumGoals['yearSalesSum'] or sumGoals['yearProfitSum']:
            cumulativeGoalSalePrice = sumGoals['salesq1'] + sumGoals['salesq2'] + sumGoals['salesq3']
            cumulativeGoalProfitPrice = sumGoals['profitq1'] + sumGoals['profitq2'] + sumGoals['profitq3']
    elif todayMonth in [10, 11, 12]:
        todayQuarter = 4
        monthList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        if sumGoals['yearSalesSum'] or sumGoals['yearProfitSum']:
            cumulativeGoalSalePrice = sumGoals['yearSalesSum']
            cumulativeGoalProfitPrice = sumGoals['yearProfitSum']

    dict_quarter = {"q1_start": "{}-01-01".format(todayYear),
                    "q1_end": "{}-04-01".format(todayYear),
                    "q2_end": "{}-07-01".format(todayYear),
                    "q3_end": "{}-10-01".format(todayYear),
                    "q4_end": "{}-01-01".format(todayYear + 1)}
    revenues = Revenue.objects.filter(Q(predictBillingDate__year=todayYear))
    revenuesFirm = revenues.filter(Q(contractId__contractStep='Firm'))
    revenuesOppty = revenues.filter(Q(contractId__contractStep='Opportunity'))

    # 해당 분기 누적 목표 매출, 이익
    cumulativeGoal = {'cumulativeGoalSalePrice': cumulativeGoalSalePrice, 'cumulativeGoalProfitPrice': cumulativeGoalProfitPrice}
    # 매출, 이익 (전체/Oppty/Firm)
    sumRevenues = revenues.aggregate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))
    sumRevenuesFirm = revenuesFirm.aggregate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))
    sumRevenuesOppty = revenuesOppty.aggregate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))

    # 분기별 매출/이익 분석 (Firm)
    quarterFirm = revenuesFirm.annotate(
        quarter=Case(
            When(predictBillingDate__month__in=[1, 2, 3], then=Value("1분기")),
            When(predictBillingDate__month__in=[4, 5, 6], then=Value("2분기")),
            When(predictBillingDate__month__in=[7, 8, 9], then=Value("3분기")),
            When(predictBillingDate__month__in=[10, 11, 12], then=Value("4분기")),
            output_field=CharField()
        )
    )
    quarterOppty = revenuesOppty.annotate(
        quarter=Case(
            When(predictBillingDate__month__in=[1, 2, 3], then=Value("1분기")),
            When(predictBillingDate__month__in=[4, 5, 6], then=Value("2분기")),
            When(predictBillingDate__month__in=[7, 8, 9], then=Value("3분기")),
            When(predictBillingDate__month__in=[10, 11, 12], then=Value("4분기")),
            output_field=CharField()
        )
    )
    quarterFirmRevenues = quarterFirm.values('quarter').annotate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))
    quarterOpptyRevenues = quarterOppty.values('quarter').annotate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))

    # 해당 분기 누적 매출, 이익 (전체/Oppty/Firm)
    cumulative = revenues.annotate(
        cumulative=Case(
                When(predictBillingDate__month__in=monthList, then=Value("Y")),
                default=Value("N"),
                output_field=CharField()
        )
    )
    cumulativeRevenues = cumulative.filter(Q(cumulative='Y')).aggregate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))
    cumulativeFirm = revenuesFirm.annotate(
        cumulative=Case(
                When(predictBillingDate__month__in=monthList, then=Value("Y")),
                default=Value("N"),
                output_field=CharField()
        )
    )
    cumulativeFirmRevenues = cumulativeFirm.filter(Q(cumulative='Y')).aggregate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))
    cumulativeOppty = revenuesOppty.annotate(
        cumulative=Case(
                When(predictBillingDate__month__in=monthList, then=Value("Y")),
                default=Value("N"),
                output_field=CharField()
        )
    )
    cumulativeOpptyRevenues = cumulativeOppty.filter(Q(cumulative='Y')).aggregate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))

    # 대분류별 매출(Firm)
    maincategoryRevenuePrice = revenuesFirm.values('contractId__mainCategory').annotate(sumMainPrice=Sum('revenuePrice'), sumMainProfitPrice=Sum('revenueProfitPrice'))

    # 산업군별 & 판매유형별 매출(Firm)
    salesindustryRevenuePrice = revenuesFirm.values('contractId__saleIndustry').annotate(sumIndustryPrice=Sum('revenuePrice'), sumIndustryProfitPrice=Sum('revenueProfitPrice'))
    salestypeRevenuePrice = revenuesFirm.values('contractId__saleType').annotate(sumTypePrice=Sum('revenuePrice'), sumTypeProfitPrice=Sum('revenueProfitPrice'))

    # 달성률 [전체/Firm]
    # Firm
    if sumGoals['yearSalesSum'] or sumGoals['yearProfitSum']:
        salePricePercent = round(sumRevenuesFirm['revenuePrice'] / sumGoals['yearSalesSum'] * 100, 2)
        profitPricePercent = round(sumRevenuesFirm['revenueProfitPrice'] / sumGoals['yearProfitSum'] * 100, 2)
        cumulativeSalePricePercent = round(cumulativeFirmRevenues['revenuePrice'] / cumulativeGoal['cumulativeGoalSalePrice'] * 100, 2)
        cumulativeProfitPricePercent = round(cumulativeFirmRevenues['revenueProfitPrice'] / cumulativeGoal['cumulativeGoalProfitPrice'] * 100, 2)
        firmPercent = {'salePricePercent': salePricePercent, 'profitPricePercent': profitPricePercent,
                       'cumulativeSalePricePercent': cumulativeSalePricePercent, 'cumulativeProfitPricePercent': cumulativeProfitPricePercent}
        # 전체
        salePricePercent = round(sumRevenues['revenuePrice'] / sumGoals['yearSalesSum'] * 100, 2)
        profitPricePercent = round(sumRevenues['revenueProfitPrice'] / sumGoals['yearProfitSum'] * 100, 2)
        cumulativeSalePricePercent = round(cumulativeRevenues['revenuePrice'] / cumulativeGoal['cumulativeGoalSalePrice'] * 100, 2)
        cumulativeProfitPricePercent = round(cumulativeRevenues['revenueProfitPrice'] / cumulativeGoal['cumulativeGoalProfitPrice'] * 100, 2)
        allPercent = {'salePricePercent': salePricePercent, 'profitPricePercent': profitPricePercent,
                       'cumulativeSalePricePercent': cumulativeSalePricePercent, 'cumulativeProfitPricePercent': cumulativeProfitPricePercent}
    else:
        firmPercent = None
        allPercent = None

    print(firmPercent, allPercent)
    context = {
        "todayYear": todayYear,
        "todayQuarter": todayQuarter,
        "sumGoals": sumGoals,
        "cumulativeGoal": cumulativeGoal,
        'sumRevenues': sumRevenues,
        'sumRevenuesFirm': sumRevenuesFirm,
        'sumRevenuesOppty': sumRevenuesOppty,
        'firmPercent': firmPercent,
        'allPercent': allPercent,
        'quarterFirmRevenues': quarterFirmRevenues,
        'quarterOpptyRevenues': quarterOpptyRevenues,
        'cumulativeRevenues': cumulativeRevenues,
        'cumulativeFirmRevenues': cumulativeFirmRevenues,
        'cumulativeOpptyRevenues': cumulativeOpptyRevenues,
        'maincategoryRevenuePrice': maincategoryRevenuePrice,
        'salesindustryRevenuePrice': salesindustryRevenuePrice,
        'salestypeRevenuePrice': salestypeRevenuePrice,
    }

    # # 해당 분기 목표 누적 매출금액 & 이익금액
    # goal = Goal.objects.filter(year=todayYear)
    # salesTarget = goal.aggregate(sum=Sum('yearSalesSum'))['sum']
    # profitTarget = goal.aggregate(sum=Sum('yearProfitSum'))['sum']
    #
    # salesQuarterTarget = goal.aggregate(sum=Coalesce(Sum('salesq1'), 0))['sum']
    # profitQuarterTarget = goal.aggregate(sum=Coalesce(Sum('profitq1'), 0))['sum']
    #
    # if todayQuarter >= 2:
    #     salesQuarterTarget += goal.aggregate(sum=Coalesce(Sum('salesq2'), 0))['sum']
    #     profitQuarterTarget += goal.aggregate(sum=Coalesce(Sum('profitq2'), 0))['sum']
    # if todayQuarter >= 3:
    #     salesQuarterTarget += goal.aggregate(sum=Coalesce(Sum('salesq3'), 0))['sum']
    #     profitQuarterTarget += goal.aggregate(sum=Coalesce(Sum('profitq3'), 0))['sum']
    # if todayQuarter >= 4:
    #     salesQuarterTarget += goal.aggregate(sum=Coalesce(Sum('salesq4'), 0))['sum']
    #     profitQuarterTarget += goal.aggregate(sum=Coalesce(Sum('profitq4'), 0))['sum']
    #
    # # 분기별/월별 목표 매출&이익 금액
    # goalsSum = goal.aggregate(sum_yearSales=Sum('yearSalesSum'), sum_yearProfit=Sum('yearProfitSum'), sum_salesq1=Sum('salesq1'), sum_salesq2=Sum('salesq2'), sum_salesq3=Sum('salesq3'),
    #                           sum_salesq4=Sum('salesq3'), sum_profitq1=Sum('profitq1'), sum_profitq2=Sum('profitq2'), sum_profitq3=Sum('profitq4'), sum_profitq4=Sum('profitq4'),
    #                           sum_sales1=Sum('sales1'), sum_sales2=Sum('sales2'), sum_sales3=Sum('sales3'), sum_sales4=Sum('sales4'), sum_sales5=Sum('sales5'), sum_sales6=Sum('sales6'),
    #                           sum_sales7=Sum('sales7'), sum_sales8=Sum('sales8'), sum_sales9=Sum('sales9'), sum_sales10=Sum('sales10'), sum_sales11=Sum('sales11'), sum_sales12=Sum('sales12'),
    #                           sum_profit1=Sum('profit1'), sum_profit2=Sum('profit2'), sum_profit3=Sum('profit3'), sum_profit4=Sum('profit4'), sum_profit5=Sum('profit5'), sum_profit6=Sum('profit6'),
    #                           sum_profit7=Sum('profit7'), sum_profit8=Sum('profit8'), sum_profit9=Sum('profit9'), sum_profit10=Sum('profit10'), sum_profit11=Sum('profit11'),
    #                           sum_profit12=Sum('profit12'),)
    #
    #
    # # 매출
    # revenues = Revenue.objects.all()
    # firmRevenuePrice = revenues.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q4_end']) & Q(contractId__contractStep='Firm'))
    # oppRevenuePrice = revenues.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q4_end']) & Q(contractId__contractStep='Opportunity'))
    #
    # if todayQuarter == 1:
    #     revenuesAccumulate = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end']))
    #     revenuesQuarter = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end']))
    # elif todayQuarter == 2:
    #     revenuesAccumulate = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q2_end']))
    #     revenuesQuarter = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_end']) & Q(predictBillingDate__lt=dict_quarter['q2_end']))
    # elif todayQuarter == 3:
    #     revenuesAccumulate = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q3_end']))
    #     revenuesQuarter = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q2_end']) & Q(predictBillingDate__lt=dict_quarter['q3_end']))
    # elif todayQuarter == 4:
    #     revenuesAccumulate = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q4_end']))
    #     revenuesQuarter = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q3_end']) & Q(predictBillingDate__lt=dict_quarter['q4_end']))
    #
    # # 메인카테고리
    # maincategoryRevenuePrice = firmRevenuePrice.values('contractId__mainCategory').annotate(sumMainPrice=Sum('revenuePrice'), sumMainProfitPrice=Sum('revenueProfitPrice'))
    #
    # # 산업군별 & 판매유형별
    # salesindustryRevenuePrice = firmRevenuePrice.values('contractId__saleIndustry').annotate(sumIndustryPrice=Sum('revenuePrice'), sumIndustryProfitPrice=Sum('revenueProfitPrice'))
    # salestypeRevenuePrice = firmRevenuePrice.values('contractId__saleType').annotate(sumTypePrice=Sum('revenuePrice'), sumTypeProfitPrice=Sum('revenueProfitPrice'))
    #
    # # 누적매출금액 & 이익 금액
    # cumulativeSalesAmount = firmRevenuePrice.aggregate(sum=Sum('revenuePrice'))['sum']
    # cumulativeProfitAmount = firmRevenuePrice.aggregate(cumulative_profit_amount=Sum('revenueProfitPrice') or 0)
    #
    # # 현재 분기까지 누적매출금액 & 이익 금액
    # quarterlyCumulativeSales = revenuesAccumulate.aggregate(quarterly_cumulative_sales=Sum('revenuePrice'))
    # quarterlyCumulativeProfit = revenuesAccumulate.aggregate(quarterly_cumulative_profit=Sum('revenueProfitPrice'))
    #
    # # 현재 분기 매출금액 & 이익 금액
    # quarterlySales = revenuesQuarter.aggregate(quarterly_sales=Sum('revenuePrice'))
    # quarterlyProfit = revenuesQuarter.aggregate(quarterly_profit=Sum('revenueProfitPrice'))
    #
    # # 분기별 opportunity & Firm
    # # 분기 opp
    # quarter1Oppty = oppRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end'])).aggregate(sum=Sum('revenuePrice'),
    #                                                                                                                                                          sum_profit=Sum('revenueProfitPrice'))
    # quarter2Oppty = oppRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_end']) & Q(predictBillingDate__lt=dict_quarter['q2_end'])).aggregate(sum=Sum('revenuePrice'),
    #                                                                                                                                                        sum_profit=Sum('revenueProfitPrice'))
    # quarter3Oppty = oppRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q2_end']) & Q(predictBillingDate__lt=dict_quarter['q3_end'])).aggregate(sum=Sum('revenuePrice'),
    #                                                                                                                                                        sum_profit=Sum('revenueProfitPrice'))
    # quarter4Oppty = oppRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q3_end']) & Q(predictBillingDate__lt=dict_quarter['q4_end'])).aggregate(sum=Sum('revenuePrice'),
    #                                                                                                                                                        sum_profit=Sum('revenueProfitPrice'))
    # quarterOpptySum = [quarter1Oppty['sum'], quarter2Oppty['sum'], quarter3Oppty['sum'], quarter4Oppty['sum']]
    # quarterOpptyProfitSum = [quarter1Oppty['sum_profit'], quarter2Oppty['sum_profit'], quarter3Oppty['sum_profit'], quarter4Oppty['sum_profit']]
    # quarterOppty = [0 if quarterOpptySum[i] == None else quarterOpptySum[i] for i in range(len(quarterOpptySum))]
    # quarterOpptyProfit = [0 if quarterOpptyProfitSum[i] == None else quarterOpptyProfitSum[i] for i in range(len(quarterOpptyProfitSum))]
    #
    # # 분기 Firm
    # quarter1Firm = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_start']) & Q(predictBillingDate__lt=dict_quarter['q1_end'])).aggregate(sum=Sum('revenuePrice'),
    #                                                                                                                                                          sum_profit=Sum('revenueProfitPrice'))
    # quarter2Firm = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q1_end']) & Q(predictBillingDate__lt=dict_quarter['q2_end'])).aggregate(sum=Sum('revenuePrice'),
    #                                                                                                                                                        sum_profit=Sum('revenueProfitPrice'))
    # quarter3Firm = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q2_end']) & Q(predictBillingDate__lt=dict_quarter['q3_end'])).aggregate(sum=Sum('revenuePrice'),
    #                                                                                                                                                        sum_profit=Sum('revenueProfitPrice'))
    # quarter4Firm = firmRevenuePrice.filter(Q(predictBillingDate__gte=dict_quarter['q3_end']) & Q(predictBillingDate__lt=dict_quarter['q4_end'])).aggregate(sum=Sum('revenuePrice'),
    #                                                                                                                                                        sum_profit=Sum('revenueProfitPrice'))
    # quarterFirmSum = [quarter1Firm['sum'], quarter2Firm['sum'], quarter3Firm['sum'], quarter4Firm['sum']]
    # quarterFirmProfitSum = [quarter1Firm['sum_profit'], quarter2Firm['sum_profit'], quarter3Firm['sum_profit'], quarter4Firm['sum_profit']]
    # quarterFirm = [0 if quarterFirmSum[i] == None else quarterFirmSum[i] for i in range(len(quarterFirmSum))]
    #
    # # 해당 분기 누적 opp&firm
    # quarterOpptyFirm = [sum(quarterOppty[0:todayQuarter]), sum(quarterFirm[0:todayQuarter])]
    #
    # # 월별 팀 매출 금액
    # salesteamList = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    # salesteamList = [x['empDeptName'] for x in salesteamList if "영업" in x['empDeptName']]
    #
    # # 월별 팀 매출 금액
    # teamRevenues = firmRevenuePrice.values('predictBillingDate__month', 'contractId__empDeptName'
    #                                        ).annotate(Sum('revenuePrice')).order_by('contractId__empDeptName', 'predictBillingDate__month')
    # teamRevenues = list(teamRevenues)
    #
    # # 월별 매출금액 & 이익금액
    #
    # monthRevenues = firmRevenuePrice.values('predictBillingDate__month').annotate(sumPrice=Sum('revenuePrice')).annotate(sumProfitPrice=Sum('revenueProfitPrice')).order_by('predictBillingDate__month')
    #
    # for i in salesteamList:
    #     monthList = [i for i in range(1, 13)]
    #     for j in teamRevenues:
    #         if j['contractId__empDeptName'] == i:
    #             monthList.remove(j['predictBillingDate__month'])
    #     for m in monthList:
    #         teamRevenues.append({'predictBillingDate__month': m, 'contractId__empDeptName': i, 'revenuePrice__sum': 0})
    #
    # teamRevenues.sort(key=lambda x: x['contractId__empDeptName'], reverse=False)
    # teamRevenues.sort(key=lambda x: x['predictBillingDate__month'], reverse=False)
    #
    # ###전체 매출/이익 금액(opp&firm)
    # opptyFirmSales = cumulativeSalesAmount + sum(quarterOppty)
    # opptyFirmProfits = cumulativeProfitAmount['cumulative_profit_amount'] + sum(quarterOpptyProfit)
    #
    # ###분기 누적 매출/이익  금액(opp&firm)
    # quarterOpptyFirmSales = quarterlyCumulativeSales['quarterly_cumulative_sales'] + sum(quarterOppty[0:todayQuarter])
    # quarterOpptyFirmProfits = quarterlyCumulativeProfit['quarterly_cumulative_profit'] + sum(quarterOpptyProfit[0:todayQuarter])
    #
    # # 목표 입력 전,
    # if salesTarget:
    #     Sales_rate = round(cumulativeSalesAmount / salesTarget * 100, 2)
    #     opp_firm_sales_rate = round(opptyFirmSales / salesTarget * 100, 2)
    # else:
    #     Sales_rate = '-'
    #     opp_firm_sales_rate = '-'
    # if profitTarget:
    #     Profit_rate = round(cumulativeProfitAmount['cumulative_profit_amount'] / profitTarget * 100, 2)
    #     opp_firm_profits_rate = round(opptyFirmProfits / profitTarget * 100, 2)
    # else:
    #     Profit_rate = '-'
    #     opp_firm_profits_rate = '-'
    # if salesQuarterTarget:
    #     Salesquater_rate = round(quarterlyCumulativeSales['quarterly_cumulative_sales'] / salesQuarterTarget * 100, 2)
    #     quarter_opp_firm_sales_rate  = round(quarterOpptyFirmSales / salesQuarterTarget * 100, 2),
    # else:
    #     Salesquater_rate = '-'
    #     quarter_opp_firm_sales_rate = '-'
    # if profitQuarterTarget:
    #     Profitquater_rate = round(quarterlyCumulativeProfit['quarterly_cumulative_profit'] / profitQuarterTarget * 100, 2)
    #     quarter_opp_firm_profits_rate = round(quarterOpptyFirmProfits / profitQuarterTarget * 100, 2)
    # else:
    #     Profitquater_rate = '_'
    #     quarter_opp_firm_profits_rate = '-'
    #
    #
    # context = {
    #     "todayYear": todayYear,
    #     "todayQuarter": todayQuarter,
    #     "salesTarget": salesTarget,
    #     "profitTarget": profitTarget,
    #     "salesQuarterTarget": salesQuarterTarget,
    #     "profitQuarterTarget": profitQuarterTarget,
    #     "Sales_rate": Sales_rate,
    #     "Profit_rate": Profit_rate,
    #     "Salesquater_rate": Salesquater_rate,
    #     "Profitquater_rate": Profitquater_rate,
    #     "cumulative_sales_amount": cumulativeSalesAmount,
    #     "cumulative_profit_amount": cumulativeProfitAmount['cumulative_profit_amount'],
    #     "quarterly_cumulative_sales": quarterlyCumulativeSales['quarterly_cumulative_sales'],
    #     "quarterly_cumulative_profit": quarterlyCumulativeProfit['quarterly_cumulative_profit'],
    #     "quarterly_sales": quarterlySales['quarterly_sales'],
    #     "quarterly_profit": quarterlyProfit['quarterly_profit'],
    #     "opp_firm_sales": opptyFirmSales,
    #     "opp_firm_profits": opptyFirmProfits,
    #     "opp_firm_sales_rate": opp_firm_sales_rate,
    #     "opp_firm_profits_rate": opp_firm_profits_rate,
    #     "quarter_opp_firm_sales": quarterOpptyFirmSales,
    #     "quarter_opp_firm_profits": quarterOpptyFirmProfits,
    #     "quarter_opp_firm_sales_rate": quarter_opp_firm_sales_rate,
    #     "quarter_opp_firm_profits_rate": quarter_opp_firm_profits_rate,
    #     "quarter_opp": quarterOppty,
    #     "quarter_firm": quarterFirm,
    #     "quarterFirmProfitSum":quarterFirmProfitSum,
    #     "team_revenues": teamRevenues,
    #     "quarter_opp_Firm": quarterOpptyFirm,
    #     'maincategoryRevenuePrice': maincategoryRevenuePrice,
    #     'salesindustryRevenuePrice': salesindustryRevenuePrice,
    #     'salestypeRevenuePrice': salestypeRevenuePrice,
    #     'monthRevenues': monthRevenues,
    #     'goalsSum': goalsSum,
    # }

    return HttpResponse(template.render(context, request))


@login_required
def dashboard_goal(request):
    template = loader.get_template('dashboard/dashboardgoal.html')
    if request.method == 'POST':
        todayYear = int(request.POST['searchYear'])
    else:
        todayYear = datetime.today().year

    revenues = Revenue.objects.filter(Q(predictBillingDate__year=todayYear) & Q(contractId__contractStep='Firm'))
    goals = Goal.objects.filter(Q(year=todayYear) & Q(empName='전체'))

    # 전체 목표 매출/이익 분석
    sumGoals = goals.aggregate(
                yearSalesSum=Sum('yearSalesSum'), yearProfitSum=Sum('yearProfitSum'),
                salesq1=Sum('salesq1'), salesq2=Sum('salesq2'), salesq3=Sum('salesq3'), salesq4=Sum('salesq4'),
                profitq1=Sum('profitq1'), profitq2=Sum('profitq2'), profitq3=Sum('profitq3'), profitq4=Sum('profitq4'),
                sales1=Sum('sales1'), sales2=Sum('sales2'), sales3=Sum('sales3'), sales4=Sum('sales4'), sales5=Sum('sales5'), sales6=Sum('sales6'),
                sales7=Sum('sales7'), sales8=Sum('sales8'), sales9=Sum('sales9'), sales10=Sum('sales10'), sales11=Sum('sales11'), sales12=Sum('sales12'),
                profit1=Sum('profit1'), profit2=Sum('profit2'), profit3=Sum('profit3'), profit4=Sum('profit4'), profit5=Sum('profit5'), profit6=Sum('profit6'),
                profit7=Sum('profit7'), profit8=Sum('profit8'), profit9=Sum('profit9'),  profit10=Sum('profit10'), profit11=Sum('profit11'), profit12=Sum('profit12'),
            )
    sumRevenues = revenues.aggregate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))

    # 분기별 매출/이익 분석
    quarter = revenues.annotate(
        quarter=Case(
            When(predictBillingDate__month__in=[1, 2, 3], then=Value("1분기")),
            When(predictBillingDate__month__in=[4, 5, 6], then=Value("2분기")),
            When(predictBillingDate__month__in=[7, 8, 9], then=Value("3분기")),
            When(predictBillingDate__month__in=[10, 11, 12], then=Value("4분기")),
            output_field=CharField()
        )
    )
    quarterRevenues = quarter.values('quarter').annotate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))

    # 월별 매출/이익 분석
    monthRevenues = revenues.values('predictBillingDate__month').annotate(revenuePrice=Sum('revenuePrice'), revenueProfitPrice=Sum('revenueProfitPrice'))

    context = {
        "todayYear": todayYear,
        "sumGoals": sumGoals,
        "sumRevenues": sumRevenues,
        "quarterRevenues": quarterRevenues,
        "monthRevenues": monthRevenues,
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
    step = request.POST['step']
    month = request.POST['month'].replace('월', '')
    cumulative = request.POST['cumulative']
    quarter = request.POST['quarter']
    maincategory = request.POST['maincategory']
    subcategory = request.POST['subcategory']
    industry = request.POST['industry']
    salestype = request.POST['salestype']

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

    if month:
        dataFirm = dataFirm.filter(Q(predictBillingDate__month=month))

    if maincategory:
        if subcategory:
            dataFirm = dataFirm.filter(Q(contractId__mainCategory=maincategory) & Q(contractId__subCategory=subcategory))
        else:
            dataFirm = dataFirm.filter(Q(contractId__mainCategory=maincategory))

    if industry:
        dataFirm = dataFirm.filter(Q(contractId__saleIndustry=industry))

    if salestype:
        dataFirm = dataFirm.filter(Q(contractId__saleType=salestype))

    dataFirm = dataFirm.values('predictBillingDate', 'billingDate', 'contractId__contractCode', 'contractId__contractName', 'contractId__saleCompanyName__companyName', 'revenuePrice', 'revenueProfitPrice',
                               'contractId__empName', 'contractId__empDeptName', 'revenueId')

    structureStep = json.dumps(list(dataFirm), cls=DjangoJSONEncoder)
    return HttpResponse(structureStep, content_type='application/json')


def dashboard_credit(request):
    template = loader.get_template('dashboard/dashboardcredit.html')
    today = datetime.today()
    warningDate = datetime.today() - relativedelta(months=3)

    # totalNotDeposit: 총 미수금
    totalNotDeposit = Revenue.objects.filter(billingDate__isnull=False, depositDate__isnull=True)
    totalNotDepositMoney = totalNotDeposit.aggregate(Sum('revenuePrice'))['revenuePrice__sum']

    # normalNotDeposit: 정상 미수금 (수금예정일이 오늘보다 크거나 같거나 없는 경우)
    normalNotDeposit = totalNotDeposit.filter(Q(predictDepositDate__gte=today) | Q(predictDepositDate__isnull=True))
    normalNotDepositMoney = normalNotDeposit.aggregate(Sum('revenuePrice'))['revenuePrice__sum']

    # warningNotDeposit: 경고 미수금 (수금예정일이 3개월 미만으로 지난 경우)
    warningNotDeposit = totalNotDeposit.filter(predictDepositDate__lt=today, predictDepositDate__gte=warningDate)
    warningNotDepositMoney = warningNotDeposit.aggregate(Sum('revenuePrice'))['revenuePrice__sum']

    # dangerNotDeposit: 위험 미수금 (수금예정일이 3개월 이상 지난 경우)
    dangerNotDeposit = totalNotDeposit.filter(predictDepositDate__lt=warningDate)
    dangerNotDepositMoney = dangerNotDeposit.aggregate(Sum('revenuePrice'))['revenuePrice__sum']

    # totalNotWithdraw: 총 미지급
    totalNotWithdraw = Purchase.objects.filter(billingDate__isnull=False, withdrawDate__isnull=True)
    totalNotWithdrawMoney = totalNotWithdraw.aggregate(Sum('purchasePrice'))['purchasePrice__sum']

    # normalNotWithdraw: 정상 미지급 (지급예정일이 오늘보다 크거나 같거나 없는 경우)
    normalNotWithdraw = totalNotWithdraw.filter(Q(predictWithdrawDate__gte=today) | Q(predictWithdrawDate__isnull=True))
    normalNotWithdrawMoney = normalNotWithdraw.aggregate(Sum('purchasePrice'))['purchasePrice__sum']

    # warningNotWithdraw: 경고 미지급 (지급예정일이 3개월 미만으로 지난 경우)
    warningNotWithdraw = totalNotWithdraw.filter(predictWithdrawDate__lt=today, predictWithdrawDate__gte=warningDate)
    warningNotWithdrawMoney = warningNotWithdraw.aggregate(Sum('purchasePrice'))['purchasePrice__sum']

    # dangerNotWithdraw: 위험 미지급 (수금예정일이 3개월 이상 지난 경우)
    dangerNotWithdraw = totalNotWithdraw.filter(predictWithdrawDate__lt=warningDate)
    dangerNotWithdrawMoney = dangerNotWithdraw.aggregate(Sum('purchasePrice'))['purchasePrice__sum']

    # pieNotDeposit: 기간별 미수금액 차트 데이터
    pieNotDepositLabel = ['정상', '3개월미만', '3개월이상']
    pieNotDepositData = [normalNotDepositMoney, warningNotDepositMoney, dangerNotDepositMoney]

    # barNotDeposit: 고객사별 미수금액 차트 데이터
    barNotDepositLabel = []
    barNotDepositData = []
    companyNotDeposit = totalNotDeposit.values('revenueCompany').annotate(
        companyRevenuePrice=Sum('revenuePrice')
    ).order_by('-companyRevenuePrice')

    maxBarSize = 5
    loopCount = 0
    for revenue in companyNotDeposit:
        if loopCount < maxBarSize:
            barNotDepositLabel.append(revenue['revenueCompany'])
            barNotDepositData.append(revenue['companyRevenuePrice'])
            loopCount += 1
        else:
            break

    # pieNotWithdraw: 기간별 미지급액 차트 데이터
    pieNotWithdrawLabel = ['정상', '3개월미만', '3개월이상']
    pieNotWithdrawData = [normalNotWithdrawMoney, warningNotWithdrawMoney, dangerNotWithdrawMoney]

    # barNotDeposit: 고객사별 미수금액 차트 데이터
    barNotWithdrawLabel = []
    barNotWithdrawData = []
    companyNotWithdraw = totalNotWithdraw.values('purchaseCompany').annotate(
        companyPurchasePrice=Sum('purchasePrice')
    ).order_by('-companyPurchasePrice')

    maxBarSize = 5
    loopCount = 0
    for purchase in companyNotWithdraw:
        if loopCount < maxBarSize:
            barNotWithdrawLabel.append(purchase['purchaseCompany'])
            barNotWithdrawData.append(purchase['companyPurchasePrice'])
            loopCount += 1
        else:
            break

    context = {
        # 미수금
        'totalNotDepositMoney': totalNotDepositMoney,
        'normalNotDepositMoney': normalNotDepositMoney,
        'warningNotDepositMoney': warningNotDepositMoney,
        'dangerNotDepositMoney': dangerNotDepositMoney,
        # 미지급
        'totalNotWithdrawMoney': totalNotWithdrawMoney,
        'normalNotWithdrawMoney': normalNotWithdrawMoney,
        'warningNotWithdrawMoney': warningNotWithdrawMoney,
        'dangerNotWithdrawMoney': dangerNotWithdrawMoney,
        # 차트 데이터
        'pieNotDepositLabel': pieNotDepositLabel,
        'pieNotDepositData': pieNotDepositData,
        'barNotDepositLabel': barNotDepositLabel,
        'barNotDepositData': barNotDepositData,
        'pieNotWithdrawLabel': pieNotWithdrawLabel,
        'pieNotWithdrawData': pieNotWithdrawData,
        'barNotWithdrawLabel': barNotWithdrawLabel,
        'barNotWithdrawData': barNotWithdrawData,
        # 날짜
        'today': today,
        'warningDate': warningDate,
    }
    return HttpResponse(template.render(context, request))


def not_deposit_asjson(request):
    today = datetime.today()
    warningDate = datetime.today() - relativedelta(months=3)
    label = request.GET['label']

    totalNotDeposit = Revenue.objects.filter(billingDate__isnull=False, depositDate__isnull=True)
    if label == '정상':
        normalNotDeposit = totalNotDeposit.filter(Q(predictDepositDate__gte=today) | Q(predictDepositDate__isnull=True))
        queryset = normalNotDeposit.annotate(
            contractStep=F('contractId__contractStep'),
            contractCode=F('contractId__contractCode'),
            empDeptName=F('contractId__empDeptName'),
            empName=F('contractId__empName'),
            contractName=F('contractId__contractName'),
            companyNameKo=F('revenueCompany__companyNameKo'),
        ).values(
            'contractStep', 'contractCode', 'empDeptName', 'empName', 'contractName', 'companyNameKo',
            'predictDepositDate', 'revenuePrice', 'revenueProfitPrice', 'comment', 'revenueId',
        )
        structure = json.dumps(list(queryset), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')
    elif label == '3개월미만':
        warningNotDeposit = totalNotDeposit.filter(predictDepositDate__lt=today, predictDepositDate__gte=warningDate)
        queryset = warningNotDeposit.annotate(
            contractStep=F('contractId__contractStep'),
            contractCode=F('contractId__contractCode'),
            empDeptName=F('contractId__empDeptName'),
            empName=F('contractId__empName'),
            contractName=F('contractId__contractName'),
            companyNameKo=F('revenueCompany__companyNameKo'),
        ).values(
            'contractStep', 'contractCode', 'empDeptName', 'empName', 'contractName', 'companyNameKo',
            'predictDepositDate', 'revenuePrice', 'revenueProfitPrice', 'comment', 'revenueId',
        )
        structure = json.dumps(list(queryset), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')
    elif label == '3개월이상':
        dangerNotDeposit = totalNotDeposit.filter(predictDepositDate__lt=warningDate)
        queryset = dangerNotDeposit.annotate(
            contractStep=F('contractId__contractStep'),
            contractCode=F('contractId__contractCode'),
            empDeptName=F('contractId__empDeptName'),
            empName=F('contractId__empName'),
            contractName=F('contractId__contractName'),
            companyNameKo=F('revenueCompany__companyNameKo'),
        ).values(
            'contractStep', 'contractCode', 'empDeptName', 'empName', 'contractName', 'companyNameKo',
            'predictDepositDate', 'revenuePrice', 'revenueProfitPrice', 'comment', 'revenueId',
        )
        structure = json.dumps(list(queryset), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')
    else:
        companyNotDeposit = totalNotDeposit.filter(revenueCompany=request.GET['label'])
        queryset = companyNotDeposit.annotate(
            contractStep=F('contractId__contractStep'),
            contractCode=F('contractId__contractCode'),
            empDeptName=F('contractId__empDeptName'),
            empName=F('contractId__empName'),
            contractName=F('contractId__contractName'),
            companyNameKo=F('revenueCompany__companyNameKo'),
        ).values(
            'contractStep', 'contractCode', 'empDeptName', 'empName', 'contractName', 'companyNameKo',
            'predictDepositDate', 'revenuePrice', 'revenueProfitPrice', 'comment', 'revenueId',
        )
        structure = json.dumps(list(queryset), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


def not_withdraw_asjson(request):
    today = datetime.today()
    warningDate = datetime.today() - relativedelta(months=3)
    label = request.GET['label']

    totalNotWithdraw = Purchase.objects.filter(billingDate__isnull=False, withdrawDate__isnull=True)
    if label == '정상':
        normalNotWithdraw = totalNotWithdraw.filter(Q(predictWithdrawDate__gte=today) | Q(predictWithdrawDate__isnull=True))
        queryset = normalNotWithdraw.annotate(
            contractStep=F('contractId__contractStep'),
            contractCode=F('contractId__contractCode'),
            empDeptName=F('contractId__empDeptName'),
            empName=F('contractId__empName'),
            contractName=F('contractId__contractName'),
            companyNameKo=F('purchaseCompany__companyNameKo'),
        ).values(
            'contractStep', 'contractCode', 'empDeptName', 'empName', 'contractName', 'companyNameKo',
            'predictWithdrawDate', 'purchasePrice', 'comment', 'purchaseId',
        )
        structure = json.dumps(list(queryset), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')
    elif label == '3개월미만':
        warningNotWithdraw = totalNotWithdraw.filter(predictWithdrawDate__lt=today, predictWithdrawDate__gte=warningDate)
        queryset = warningNotWithdraw.annotate(
            contractStep=F('contractId__contractStep'),
            contractCode=F('contractId__contractCode'),
            empDeptName=F('contractId__empDeptName'),
            empName=F('contractId__empName'),
            contractName=F('contractId__contractName'),
            companyNameKo=F('purchaseCompany__companyNameKo'),
        ).values(
            'contractStep', 'contractCode', 'empDeptName', 'empName', 'contractName', 'companyNameKo',
            'predictWithdrawDate', 'purchasePrice', 'comment', 'purchaseId',
        )
        structure = json.dumps(list(queryset), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')
    elif label == '3개월이상':
        dangerNotWithdraw = totalNotWithdraw.filter(predictWithdrawDate__lt=warningDate)
        queryset = dangerNotWithdraw.annotate(
            contractStep=F('contractId__contractStep'),
            contractCode=F('contractId__contractCode'),
            empDeptName=F('contractId__empDeptName'),
            empName=F('contractId__empName'),
            contractName=F('contractId__contractName'),
            companyNameKo=F('purchaseCompany__companyNameKo'),
        ).values(
            'contractStep', 'contractCode', 'empDeptName', 'empName', 'contractName', 'companyNameKo',
            'predictWithdrawDate', 'purchasePrice', 'comment', 'purchaseId',
        )
        structure = json.dumps(list(queryset), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')
    else:
        companyNotWithdraw = totalNotWithdraw.filter(purchaseCompany=request.GET['label'])
        queryset = companyNotWithdraw.annotate(
            contractStep=F('contractId__contractStep'),
            contractCode=F('contractId__contractCode'),
            empDeptName=F('contractId__empDeptName'),
            empName=F('contractId__empName'),
            contractName=F('contractId__contractName'),
            companyNameKo=F('purchaseCompany__companyNameKo'),
        ).values(
            'contractStep', 'contractCode', 'empDeptName', 'empName', 'contractName', 'companyNameKo',
            'predictWithdrawDate', 'purchasePrice', 'comment', 'purchaseId',
        )
        structure = json.dumps(list(queryset), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def cashflow_asjson(request):
    todayYear = datetime.today().year
    outstandingCollections = request.POST['outstandingCollections']
    accountsPayables = request.POST['accountsPayables']
    month = request.POST['month'][:-1]

    if outstandingCollections:
        cashflow = Revenue.objects.filter(Q(predictBillingDate__year=todayYear) & Q(predictDepositDate__month=month) & Q(billingDate__isnull=False) & Q(depositDate__isnull=True))
        cashflow = cashflow.values('billingDate', 'contractId__contractCode', 'contractId__contractName', 'contractId__saleCompanyName__companyName', 'revenuePrice', 'revenueProfitPrice',
                                   'contractId__empName', 'contractId__empDeptName', 'revenueId', 'predictBillingDate', 'predictDepositDate', 'depositDate', 'contractId__contractStep',
                                   'contractId__depositCondition', 'contractId__depositConditionDay', 'comment')

    if accountsPayables:
        cashflow = Purchase.objects.filter(Q(predictBillingDate__year=todayYear) & Q(predictWithdrawDate__month=month) & Q(billingDate__isnull=False) & Q(withdrawDate__isnull=True))
        cashflow = cashflow.values('contractId__contractName', 'purchaseCompany', 'contractId__contractCode', 'predictBillingDate', 'billingDate', 'purchasePrice',
                                   'predictWithdrawDate', 'withdrawDate', 'purchaseId', 'contractId__empDeptName', 'contractId__empName', 'contractId__contractStep', 'comment')

    structureStep = json.dumps(list(cashflow), cls=DjangoJSONEncoder)
    return HttpResponse(structureStep, content_type='application/json')


@login_required
@csrf_exempt
def service_asjson(request):
    startdate = request.POST['startdate'].replace('.', '-')
    enddate = request.POST['enddate'].replace('.', '-')
    empDeptName = request.POST['empDeptName']
    company = request.POST['company']
    empname = request.POST['empname']
    servicetype = request.POST['servicetype']
    overhour = request.POST['overhour']
    services = Servicereport.objects.filter(Q(serviceStatus='Y')).exclude(serviceType__typeName='').exclude(serviceType__typeName='내근').exclude(empDeptName__icontains='영업')

    if startdate:
        services = services.filter(Q(serviceDate__gte=startdate))

    if enddate:
        services = services.filter(Q(serviceDate__lte=enddate))

    if empDeptName:
        services = services.filter(Q(empDeptName__icontains=empDeptName))

    if company:
        services = services.filter(Q(companyName=company))

    if company:
        services = services.filter(Q(companyName=company))

    if empname:
        services = services.filter(Q(empName=empname))

    if servicetype:
        services = services.filter(Q(serviceType__typeName=servicetype))

    if overhour:
        services = services.exclude(serviceOverHour=0)

    services = services.values('serviceId', 'serviceDate', 'empId_id', 'empName', 'empDeptName', 'companyName_id', 'serviceHour', 'serviceOverHour',
                               'serviceRegHour', 'serviceTitle', 'serviceDetails', 'serviceType__typeName')

    structureStep = json.dumps(list(services), cls=DjangoJSONEncoder)
    return HttpResponse(structureStep, content_type='application/json')

@login_required
@csrf_exempt
def dashboard_location(request):
    template = loader.get_template('dashboard/dashboardlocation.html')
    today = datetime.today()
    day = str(today)[:10]
    location = Geolocation.objects.filter(Q(startLatitude__isnull=False) & Q(endLatitude__isnull=True)).select_related('serviceId')
    services = location.annotate(
        flag=Case(
            When(serviceId__serviceType__typeName=Value('상주'), then=Value('상주')),
            When(serviceId__serviceType__typeName=Value('프로젝트상주'), then=Value('상주')),
            When(serviceId__directgo=Value('Y'), then=Value('직출')),
            default=Value(''),
            output_field=CharField()
        ),
        empName=F('serviceId__empName'),
        empDeptName=F('serviceId__empDeptName'),
        serviceStartDatetime=F('serviceId__serviceStartDatetime'),
        serviceEndDatetime=F('serviceId__serviceEndDatetime'),
        serviceStatus=F('serviceId__serviceStatus'),
        companyName=F('serviceId__companyName__companyName'),
        serviceType=F('serviceId__serviceType__typeName'),
        serviceTitle=F('serviceId__serviceTitle'),
    )
    tables = [
        {
            'team': '영업1팀',
            'services': services.filter(empDeptName='영업1팀')
        },
        {
            'team': '영업2팀',
            'services': services.filter(empDeptName='영업2팀')
        },
        {
            'team': '인프라서비스사업팀',
            'services': services.filter(empDeptName='인프라서비스사업팀')
        },
        {
            'team': '솔루션지원팀',
            'services': services.filter(empDeptName='솔루션지원팀')
        },
        {
            'team': 'DB지원팀',
            'services': services.filter(empDeptName='DB지원팀')
        },
    ]

    # 20년 2월 1일 이전
    Date = datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))

    solution = dayreport_query2(empDeptName="솔루션지원팀", day=day)
    db = dayreport_query2(empDeptName="DB지원팀", day=day)
    sales1 = dayreport_query2(empDeptName="영업1팀", day=day)
    sales2 = dayreport_query2(empDeptName="영업2팀", day=day)
    infra = dayreport_query2(empDeptName="인프라서비스사업팀", day=day)

    dept = request.user.employee.empDeptName

    rows = []
    if dept == '영업2팀':
        rows.append([
            {'title': '영업2팀', 'service': sales2[0], 'education': sales2[1], 'vacation': sales2[2]},
            {'title': '영업1팀', 'service': sales1[0], 'education': sales1[1], 'vacation': sales1[2]},
        ])
        rows.append([
            {'title': '솔루션지원팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
            {'title': 'DB지원팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
        ])
        rows.append([
            {'title': '인프라서비스사업팀', 'service': infra[0], 'education': infra[1], 'vacation': infra[2]},
            {'title': '', 'service': '', 'education': '', 'vacation': ''},
        ])
    elif dept == '솔루션지원팀':
        rows.append([
            {'title': '솔루션지원팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
            {'title': 'DB지원팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
        ])
        rows.append([
            {'title': '영업1팀', 'service': sales1[0], 'education': sales1[1], 'vacation': sales1[2]},
            {'title': '영업2팀', 'service': sales2[0], 'education': sales2[1], 'vacation': sales2[2]},
        ])
        rows.append([
            {'title': '인프라서비스사업팀', 'service': infra[0], 'education': infra[1], 'vacation': infra[2]},
            {'title': '', 'service': '', 'education': '', 'vacation': ''},
        ])
    elif dept == 'DB지원팀':
        rows.append([
            {'title': 'DB지원팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
            {'title': '솔루션지원팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
        ])
        rows.append([
            {'title': '영업1팀', 'service': sales1[0], 'education': sales1[1], 'vacation': sales1[2]},
            {'title': '영업2팀', 'service': sales2[0], 'education': sales2[1], 'vacation': sales2[2]},
        ])
        rows.append([
            {'title': '인프라서비스사업팀', 'service': infra[0], 'education': infra[1], 'vacation': infra[2]},
            {'title': '', 'service': '', 'education': '', 'vacation': ''},
        ])
    elif dept == '인프라서비스사업팀':
        rows.append([
            {'title': '인프라서비스사업팀', 'service': infra[0], 'education': infra[1], 'vacation': infra[2]},
            {'title': '', 'service': '', 'education': '', 'vacation': ''},
        ])
        rows.append([
            {'title': '영업1팀', 'service': sales1[0], 'education': sales1[1], 'vacation': sales1[2]},
            {'title': '영업2팀', 'service': sales2[0], 'education': sales2[1], 'vacation': sales2[2]},
        ])
        rows.append([
            {'title': '솔루션지원팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
            {'title': 'DB지원팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
        ])
    else:
        rows.append([
            {'title': '영업1팀', 'service': sales1[0], 'education': sales1[1], 'vacation': sales1[2]},
            {'title': '영업2팀', 'service': sales2[0], 'education': sales2[1], 'vacation': sales2[2]},
        ])
        rows.append([
            {'title': '솔루션지원팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
            {'title': 'DB지원팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
        ])
        rows.append([
            {'title': '인프라서비스사업팀', 'service': infra[0], 'education': infra[1], 'vacation': infra[2]},
            {'title': '', 'service': '', 'education': '', 'vacation': ''},
        ])

    # # 20년 2월 1일 부터
    # Date = datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    #
    # sales = dayreport_query(empDeptName=["영업팀"], day=day)
    # rnd = dayreport_query(empDeptName=["Technical Architecture팀", "AI Platform Labs"], day=day)
    # db = dayreport_query(empDeptName=["DB Expert팀"], day=day)
    # solution = dayreport_query(empDeptName=["솔루션팀"], day=day)
    # rows = [
    #     [
    #         {'title': '영업팀', 'service': sales[0], 'education': sales[1], 'vacation': sales[2]},
    #         {'title': 'R&D 전략사업부', 'service': rnd[0], 'education': rnd[1], 'vacation': rnd[2]},
    #     ],
    #     [
    #         {'title': '솔루션팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
    #         {'title': 'DB Expert팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
    #     ]
    # ]

    context = {
        'today': today,
        'day': day,
        'location': location,
        'tables': tables,
        'Date': Date,
        'rows': rows,
        'MAP_KEY': MAP_KEY,
        'testMAP_KEY': testMAP_KEY,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def dashboard_client(request):
    template = loader.get_template('dashboard/dashboardclient.html')
    contracts = Contract.objects.filter(Q(contractStep='Firm'))
    services = Servicereport.objects.filter(serviceStatus='Y')
    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        endCompanyName = request.POST['endCompanyName']
        if startdate:
            contracts = contracts.filter(Q(contractDate__gte=startdate))
            services = services.filter(Q(contractId__contractDate__gte=startdate))
        if enddate:
            contracts = contracts.filter(Q(contractDate__lte=enddate))
            services = services.filter(Q(contractId__contractDate__lte=enddate))
        if endCompanyName:
            contracts = contracts.filter(Q(endCompanyName__companyName__icontains=endCompanyName) | Q(endCompanyName__companyNameKo__icontains=endCompanyName))
            services = services.filter(Q(contractId__endCompanyName__companyName__icontains=endCompanyName) | Q(contractId__endCompanyName__companyNameKo__icontains=endCompanyName))
        priceSummary = contracts.aggregate(price=Sum('salePrice'), profit=Sum('profitPrice'))
        serviceSummary = services.aggregate(serviceHour=Sum('serviceHour'), serviceOverHour=Sum('serviceOverHour'))
        companySummary = contracts.values('endCompanyName__companyNameKo').annotate(price=Sum('salePrice'), profit=Sum('profitPrice'), count=Count('salePrice'))
        overhourSummary = services.aggregate(servicehour=Sum('serviceHour'), overhour=Sum('serviceOverHour'))

    else:
        startdate = contracts.aggregate(startdate=Min('contractDate'))['startdate']
        enddate = contracts.aggregate(enddate=Max('contractDate'))['enddate']
        endCompanyName = ''
        services = services.filter(Q(contractId__contractDate__gte=startdate) & Q(contractId__contractDate__lte=enddate))
        priceSummary = contracts.aggregate(price=Sum('salePrice'), profit=Sum('profitPrice'))
        serviceSummary = services.aggregate(serviceHour=Sum('serviceHour'), serviceOverHour=Sum('serviceOverHour'))
        companySummary = contracts.values('endCompanyName__companyNameKo').annotate(price=Sum('salePrice'), profit=Sum('profitPrice')).order_by('-price')
        overhourSummary = services.aggregate(servicehour=Sum('serviceHour'), overhour=Sum('serviceOverHour'))

    context = {
        'startdate': startdate,
        'enddate': enddate,
        'endCompanyName': endCompanyName,
        'priceSummary': priceSummary,
        'serviceSummary': serviceSummary,
        'companySummary': companySummary,
        'overhourSummary': overhourSummary,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def client_graph(request):
    todayYear = datetime.today().year
    companyName = request.POST['companyName']
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']

    contracts = Contract.objects.filter(Q(contractStep='Firm'))
    services = Servicereport.objects.filter(serviceStatus='Y')
    if startdate:
        contracts = contracts.filter(Q(contractDate__gte=startdate))
        services = services.filter(Q(contractId__contractDate__gte=startdate))
    if enddate:
        contracts = contracts.filter(Q(contractDate__lte=enddate))
        services = services.filter(Q(contractId__contractDate__lte=enddate))

    companySummary = contracts.filter(endCompanyName__companyNameKo=companyName).aggregate(price=Sum('salePrice'), profit=Sum('profitPrice'))
    overhourSummary = services.filter(contractId__endCompanyName__companyNameKo=companyName).aggregate(servicehour=Sum('serviceHour'), overhour=Sum('serviceOverHour'))

    structure = json.dumps([companySummary, overhourSummary], cls=DjangoJSONEncoder)

    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def services_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    companyName = request.POST['companyName']

    services = Servicereport.objects.filter(Q(serviceStatus='Y'))
    if startdate:
        services = services.filter(Q(contractId__contractDate__gte=startdate))
    if enddate:
        services = services.filter(Q(contractId__contractDate__lte=enddate))
    if companyName:
        services = services.filter(contractId__endCompanyName__companyNameKo=companyName)

    services = services.values(
        'serviceDate', 'companyName__companyName', 'serviceTitle', 'empName', 'directgo', 'serviceType',
        'serviceBeginDatetime', 'serviceStartDatetime', 'serviceEndDatetime', 'serviceFinishDatetime',
        'serviceHour', 'serviceOverHour', 'serviceDetails', 'contractId__contractCode',
        'serviceStatus', 'contractId__contractName', 'serviceId'
    )

    structure = json.dumps(list(services), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def contracts_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    companyName = request.POST['companyName']

    contracts = Contract.objects.filter(Q(contractStep='Firm'))
    if startdate:
        contracts = contracts.filter(Q(contractDate__gte=startdate))
    if enddate:
        contracts = contracts.filter(Q(contractDate__lte=enddate))
    if companyName:
        contracts = contracts.filter(endCompanyName__companyNameKo=companyName)

    contracts = contracts.values('contractStep', 'empDeptName', 'empName', 'contractCode', 'contractName', 'saleCompanyName__companyNameKo', 'endCompanyName__companyNameKo',
                                 'contractDate', 'contractId', 'salePrice', 'profitPrice', 'mainCategory', 'subCategory', 'saleIndustry', 'saleType', 'comment',
                                 'contractStartDate', 'contractEndDate', 'depositCondition', 'depositConditionDay')
    structure = json.dumps(list(contracts), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')
