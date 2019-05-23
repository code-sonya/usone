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
from sales.models import Contract, Category, Contractitem, Revenue, Goal
from hr.models import Employee
from django.db.models import functions


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
        all_support_data = Servicereport.objects.filter(Q(serviceDate__gte=startdate) &
                                                        Q(serviceDate__lte=enddate)).exclude(serviceType="교육")

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

        context = {
            'filter': "Y",
            'startdate': startdate,
            'enddate': enddate,
        }

    else:
        context = {
            'filter': 'N',
        }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def over_asjson(request):
    overHour = Servicereport.objects.filter(serviceOverHour__gt=0)
    overHourlist = overHour.values('serviceStartDatetime', 'serviceEndDatetime', 'empId__empName', 'empId__empDeptName', 'companyName', 'serviceOverHour', 'serviceId')
    structure = json.dumps(list(overHourlist), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def filter_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    overHour = Servicereport.objects.filter(Q(serviceOverHour__gt=0) & Q(serviceDate__gte=startdate) & Q(serviceDate__lte=enddate))
    overHourlist = overHour.values('serviceStartDatetime', 'serviceEndDatetime', 'empId__empName', 'empId__empDeptName', 'companyName', 'serviceOverHour')
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
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))

    # 년도,월,분기
    today_year = datetime.today().year
    today_month = datetime.today().month
    if today_month in [1, 2, 3]:
        quarter = 1
    elif today_month in [4, 5, 6]:
        quarter = 2
    elif today_month in [7, 8, 9]:
        quarter = 3
    elif today_month in [10, 11, 12]:
        quarter = 4

    revenues = Revenue.objects.all()
    contract = Contract.objects.all()

    dict_quarter = {"q1_start": "{}-01-01".format(today_year),
                    "q1_end": "{}-04-01".format(today_year),
                    "q2_end": "{}-07-01".format(today_year),
                    "q3_end": "{}-10-01".format(today_year),
                    "q4_end": "{}-01-01".format(today_year + 1)}

    total_sales = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q4_end']))

    if quarter == 1:
        revenues_accumulate = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q1_end']))
        revenues_quarter = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q1_end']))
    elif quarter == 2:
        revenues_accumulate = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q2_end']))
        revenues_quarter = revenues.filter(Q(billingDate__gte=dict_quarter['q1_end']) & Q(billingDate__lt=dict_quarter['q2_end']))
    elif quarter == 3:
        revenues_accumulate = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q3_end']))
        revenues_quarter = revenues.filter(Q(billingDate__gte=dict_quarter['q2_end']) & Q(billingDate__lt=dict_quarter['q3_end']))
    elif quarter == 4:
        revenues_accumulate = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q4_end']))
        revenues_quarter = revenues.filter(Q(billingDate__gte=dict_quarter['q3_end']) & Q(billingDate__lt=dict_quarter['q4_end']))

    ###목표매출금액 & 이익 금액
    goal = Goal.objects.filter(year=today_year)
    Target_sales = goal.aggregate(sum=Sum('yearSalesSum'))
    Target_profit = goal.aggregate(sum=Sum('yearProfitSum'))
    Target_sales = Target_sales['sum']
    Target_profit = Target_profit['sum']
    Target_salesq1 = goal.aggregate(sum=Sum('salesq1'))
    Target_profitq1 = goal.aggregate(sum=Sum('profitq1'))
    Target_salesq2 = goal.aggregate(sum=Sum('salesq2'))
    Target_profitq2 = goal.aggregate(sum=Sum('profitq2'))
    Target_salesq3 = goal.aggregate(sum=Sum('salesq3'))
    Target_profitq3 = goal.aggregate(sum=Sum('profitq3'))
    if quarter == 1:
        Target_quatersales = Target_salesq1['sum']
        Target_quaterprofit = Target_profitq1['sum']
    elif quarter == 2:
        Target_quatersales = Target_salesq1['sum'] + Target_salesq2['sum']
        Target_quaterprofit = Target_profitq1['sum'] + Target_profitq2['sum']
    elif quarter == 3:
        Target_quatersales = Target_salesq1['sum'] + Target_salesq2['sum'] + Target_salesq3['sum']
        Target_quaterprofit = Target_profitq1['sum'] + Target_profitq2['sum'] + Target_profitq3['sum']
    elif quarter == 4:
        Target_quatersales = Target_sales
        Target_quaterprofit = Target_profit

    ###누적매출금액 & 이익 금액
    cumulative_sales_amount = total_sales.aggregate(cumulative_sales_amount=Sum('revenuePrice'))
    cumulative_profit_amount = total_sales.aggregate(cumulative_profit_amount=Sum('revenueProfitPrice'))

    ###현재 분기까지 누적매출금액 & 이익 금액
    quarterly_cumulative_sales = revenues_accumulate.aggregate(quarterly_cumulative_sales=Sum('revenuePrice'))
    quarterly_cumulative_profit = revenues_accumulate.aggregate(quarterly_cumulative_profit=Sum('revenueProfitPrice'))

    ###현재 분기 매출금액 & 이익 금액
    quarterly_sales = revenues_quarter.aggregate(quarterly_sales=Sum('revenuePrice'))
    quarterly_profit = revenues_quarter.aggregate(quarterly_profit=Sum('revenueProfitPrice'))

    ###분기별 opportunity&Firm
    # 분기 opp
    quarter1_opp = contract.filter(Q(contractStep='Opportunity') & Q(contractDate__gte=dict_quarter['q1_start']) & Q(contractDate__lt=dict_quarter['q1_end'])) \
        .aggregate(sum=Sum('salePrice'), sum_profit=Sum('profitPrice'))
    quarter2_opp = contract.filter(Q(contractStep='Opportunity') & Q(contractDate__gte=dict_quarter['q1_end']) & Q(contractDate__lt=dict_quarter['q2_end'])) \
        .aggregate(sum=Sum('salePrice'), sum_profit=Sum('profitPrice'))
    quarter3_opp = contract.filter(Q(contractStep='Opportunity') & Q(contractDate__gte=dict_quarter['q2_end']) & Q(contractDate__lt=dict_quarter['q3_end'])) \
        .aggregate(sum=Sum('salePrice'), sum_profit=Sum('profitPrice'))
    quarter4_opp = contract.filter(Q(contractStep='Opportunity') & Q(contractDate__gte=dict_quarter['q3_end']) & Q(contractDate__lt=dict_quarter['q4_end'])) \
        .aggregate(sum=Sum('salePrice'), sum_profit=Sum('profitPrice'))
    quarter_opp_sum = [quarter1_opp['sum'], quarter2_opp['sum'], quarter3_opp['sum'], quarter4_opp['sum']]
    quarter_opp_profitsum = [quarter1_opp['sum_profit'], quarter2_opp['sum_profit'], quarter3_opp['sum_profit'], quarter4_opp['sum_profit']]
    quarter_opp = [0 if quarter_opp_sum[i] == None else quarter_opp_sum[i] for i in range(len(quarter_opp_sum))]
    quarter_oppprofit = [0 if quarter_opp_profitsum[i] == None else quarter_opp_profitsum[i] for i in range(len(quarter_opp_profitsum))]
    print("quarter_oppprofit:", quarter_oppprofit)

    # 분기 Firm
    quarter1_revenues = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q1_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter2_revenues = revenues.filter(Q(billingDate__gte=dict_quarter['q1_end']) & Q(billingDate__lt=dict_quarter['q2_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter3_revenues = revenues.filter(Q(billingDate__gte=dict_quarter['q2_end']) & Q(billingDate__lt=dict_quarter['q3_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter4_revenues = revenues.filter(Q(billingDate__gte=dict_quarter['q3_end']) & Q(billingDate__lt=dict_quarter['q4_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter_firm_sum = [quarter1_revenues['sum'], quarter2_revenues['sum'], quarter3_revenues['sum'], quarter4_revenues['sum']]
    quarter_firm = [0 if quarter_firm_sum[i] == None else quarter_firm_sum[i] for i in range(len(quarter_firm_sum))]

    ### 해당 분기 누적 opp&firm
    quarter_opp_Firm = [sum(quarter_opp[0:quarter]), sum(quarter_firm[0:quarter])]

    ###월별 팀 매출 금액
    salesteam_lst = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    salesteam_lst = [x['empDeptName'] for x in salesteam_lst if "영업" in x['empDeptName']]
    ###월별 팀 매출 금액
    team_revenues = total_sales.values('billingDate__month', 'contractId__empDeptName'
                                       ).annotate(Sum('revenuePrice')).order_by('contractId__empDeptName', 'billingDate__month')

    team_revenues = list(team_revenues)
    for i in salesteam_lst:
        month_lst = [i for i in range(1, 13)]
        for j in team_revenues:
            if j['contractId__empDeptName'] == i:
                month_lst.remove(j['billingDate__month'])
        for m in month_lst:
            team_revenues.append({'billingDate__month': m, 'contractId__empDeptName': i, 'revenuePrice__sum': 0})

    team_revenues.sort(key=lambda x: x['contractId__empDeptName'], reverse=False)
    team_revenues.sort(key=lambda x: x['billingDate__month'], reverse=False)

    ###전체 매출/이익 금액(opp&firm)
    opp_firm_sales = cumulative_sales_amount['cumulative_sales_amount'] + sum(quarter_opp)
    opp_firm_profits = cumulative_profit_amount['cumulative_profit_amount'] + sum(quarter_oppprofit)

    ###분기 누적 매출/이익  금액(opp&firm)
    quarter_opp_firm_sales = quarterly_cumulative_sales['quarterly_cumulative_sales'] + sum(quarter_opp[0:quarter])
    quarter_opp_firm_profits = quarterly_cumulative_profit['quarterly_cumulative_profit'] + sum(quarter_oppprofit[0:quarter])

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
        "quarter": quarter,
        "Target_sales": Target_sales,
        "Target_profit": Target_profit,
        "Target_quatersales": Target_quatersales,
        "Target_quaterprofit": Target_quaterprofit,
        "Sales_rate": round(cumulative_sales_amount['cumulative_sales_amount'] / Target_sales * 100, 2),
        "Profit_rate": round(cumulative_profit_amount['cumulative_profit_amount'] / Target_profit * 100, 2),
        "Salesquater_rate": round(quarterly_cumulative_sales['quarterly_cumulative_sales'] / Target_quatersales * 100, 2),
        "Profitquater_rate": round(quarterly_cumulative_profit['quarterly_cumulative_profit'] / Target_quaterprofit * 100, 2),
        "cumulative_sales_amount": cumulative_sales_amount['cumulative_sales_amount'],
        "cumulative_profit_amount": cumulative_profit_amount['cumulative_profit_amount'],
        "quarterly_cumulative_sales": quarterly_cumulative_sales['quarterly_cumulative_sales'],
        "quarterly_cumulative_profit": quarterly_cumulative_profit['quarterly_cumulative_profit'],
        "quarterly_sales": quarterly_sales['quarterly_sales'],
        "quarterly_profit": quarterly_profit['quarterly_profit'],
        "opp_firm_sales": opp_firm_sales,
        "opp_firm_profits": opp_firm_profits,
        "opp_firm_sales_rate": round(opp_firm_sales / Target_sales * 100, 2),
        "opp_firm_profits_rate": round(opp_firm_profits / Target_profit * 100, 2),
        "quarter_opp_firm_sales": quarter_opp_firm_sales,
        "quarter_opp_firm_profits": quarter_opp_firm_profits,
        "quarter_opp_firm_sales_rate": round(quarter_opp_firm_sales / Target_quatersales * 100, 2),
        "quarter_opp_firm_profits_rate": round(quarter_opp_firm_profits / Target_quaterprofit * 100, 2),
        "quarter_opp": quarter_opp,
        "quarter_firm": quarter_firm,
        "team_revenues": team_revenues,
        "quarter_opp_Firm": quarter_opp_Firm,
        "employees": employees,
        'startdate': startdate,
        'enddate': enddate,
        'contractStep': contractStep,
        'empDeptName': empDeptName,
        'empName': empName,
        'saleCompanyName': saleCompanyName,
        'endCompanyName': endCompanyName,
        'contractName': contractName,
    }
    return HttpResponse(template.render(context, request))


@login_required
def dashboard_goal(request):
    template = loader.get_template('dashboard/dashboardgoal.html')
    today_year = datetime.today().year
    dict_quarter = {"q1_start": "{}-01-01".format(today_year),
                    "q1_end": "{}-04-01".format(today_year),
                    "q2_end": "{}-07-01".format(today_year),
                    "q3_end": "{}-10-01".format(today_year),
                    "q4_end": "{}-01-01".format(today_year + 1)}
    salesteam_lst = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    salesteam_lst = [x['empDeptName'] for x in salesteam_lst if "영업" in x['empDeptName']]
    revenues = Revenue.objects.filter(Q(billingDate__year=today_year))

    ## 팀별 목표 & 전체 매출 금액
    data_team_goals = Goal.objects.filter(Q(empDeptName__icontains='영업') & Q(year=today_year))
    data_team_sales = []
    for i in salesteam_lst:
        sales = revenues.filter(Q(contractId__empDeptName=i) & Q(billingDate__year=today_year)).values('contractId__empDeptName').aggregate(sum_sales=Sum('revenuePrice'),
                                                                                                                                            sum_profits=Sum('revenueProfitPrice'))
        data_team_sales.append({i: sales})

    for i in salesteam_lst:
        # 분기 Firm
        if i == '영업1팀':
            team1_revenues = revenues.filter(Q(contractId__empDeptName=i)).values('billingDate__month', 'contractId__empDeptName'
                                             ).annotate(Sum('revenuePrice')).order_by('contractId__empDeptName', 'billingDate__month')
            quarter1_revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q1_end'])) \
                .aggregate(sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter2_revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(billingDate__gte=dict_quarter['q1_end']) & Q(billingDate__lt=dict_quarter['q2_end'])) \
                .aggregate(sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter3_revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(billingDate__gte=dict_quarter['q2_end']) & Q(billingDate__lt=dict_quarter['q3_end'])) \
                .aggregate(sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter4_revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(billingDate__gte=dict_quarter['q3_end']) & Q(billingDate__lt=dict_quarter['q4_end'])) \
                .aggregate(sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter_firm_team1_revenuePrice = [quarter1_revenues['sum_sales'], quarter2_revenues['sum_sales'], quarter3_revenues['sum_sales'], quarter4_revenues['sum_sales']]
            quarter_firm_team1_revenueProfitPrice = [quarter1_revenues['sum_profits'], quarter2_revenues['sum_profits'], quarter3_revenues['sum_profits'], quarter4_revenues['sum_profits']]
            quarter_firm_team1_sales = [0 if quarter_firm_team1_revenuePrice[i] == None else quarter_firm_team1_revenuePrice[i] for i in range(len(quarter_firm_team1_revenuePrice))]
            quarter_firm_team1_profits = [0 if quarter_firm_team1_revenueProfitPrice[i] == None else quarter_firm_team1_revenueProfitPrice[i] for i in
                                          range(len(quarter_firm_team1_revenueProfitPrice))]

        elif i == '영업2팀':
            team2_revenues = revenues.filter(Q(contractId__empDeptName=i)).values('billingDate__month', 'contractId__empDeptName'
                                                                                  ).annotate(Sum('revenuePrice')).order_by('contractId__empDeptName', 'billingDate__month')
            quarter1_revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q1_end'])) \
                .aggregate(
                sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter2_revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(billingDate__gte=dict_quarter['q1_end']) & Q(billingDate__lt=dict_quarter['q2_end'])) \
                .aggregate(
                sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter3_revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(billingDate__gte=dict_quarter['q2_end']) & Q(billingDate__lt=dict_quarter['q3_end'])) \
                .aggregate(
                sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter4_revenues = revenues.filter(Q(contractId__empDeptName=i) & Q(billingDate__gte=dict_quarter['q3_end']) & Q(billingDate__lt=dict_quarter['q4_end'])) \
                .aggregate(
                sum_sales=Sum('revenuePrice'), sum_profits=Sum('revenueProfitPrice'))
            quarter_firm_team2_revenuePrice = [quarter1_revenues['sum_sales'], quarter2_revenues['sum_sales'], quarter3_revenues['sum_sales'], quarter4_revenues['sum_sales']]
            quarter_firm_team2_revenueProfitPrice = [quarter1_revenues['sum_profits'], quarter2_revenues['sum_profits'], quarter3_revenues['sum_profits'], quarter4_revenues['sum_profits']]
            quarter_firm_team2_sales = [0 if quarter_firm_team2_revenuePrice[i] == None else quarter_firm_team2_revenuePrice[i] for i in range(len(quarter_firm_team2_revenuePrice))]
            quarter_firm_team2_profits = [0 if quarter_firm_team1_revenueProfitPrice[i] == None else quarter_firm_team2_revenueProfitPrice[i] for i in
                                          range(len(quarter_firm_team2_revenueProfitPrice))]

    ###월별 팀 매출 금액
    team1_revenues = list(team1_revenues)
    team2_revenues = list(team2_revenues)
    team1_month_lst = [i for i in range(1, 13)]
    team2_month_lst = [i for i in range(1, 13)]
    for j in team1_revenues:
        team1_month_lst.remove(j['billingDate__month'])
    for m in team1_month_lst:
        team1_revenues.append({'billingDate__month': m, 'revenuePrice__sum': 0})
    for j in team2_revenues:
        team2_month_lst.remove(j['billingDate__month'])
    for m in team2_month_lst:
        team2_revenues.append({'billingDate__month': m, 'revenuePrice__sum': 0})

    team1_revenues.sort(key=lambda x: x['billingDate__month'], reverse=False)
    team2_revenues.sort(key=lambda x: x['billingDate__month'], reverse=False)

    context = {
        "year": today_year,
        "data_team_goals": data_team_goals,
        "data_team_sales": data_team_sales,
        "quarter_firm_team1_sales": quarter_firm_team1_sales,
        "quarter_firm_team1_profits": quarter_firm_team1_profits,
        "quarter_firm_team2_sales": quarter_firm_team2_sales,
        "quarter_firm_team2_profits": quarter_firm_team2_profits,
        "team1_revenues":team1_revenues,
        "team2_revenues":team2_revenues

    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def opportunity_graph(request):
    step = request.POST['step']
    maincategory = request.POST['maincategory']
    subcategory = request.POST['subcategory']
    emp = request.POST['emp']
    customer = request.POST['customer']

    dataStep = Contract.objects.all()
    dataCategory = Contractitem.objects.all()

    if step:
        dataStep = dataStep.filter(contractStep=step)
        dataCategory = dataCategory.filter(contractId__contractStep=step)

    if maincategory:
        dataStep = dataStep.filter(contractitem__mainCategory=maincategory)
        dataCategory = dataCategory.filter(mainCategory=maincategory)

    if subcategory:
        dataStep = dataStep.filter(contractitem__subCategory=subcategory)
        dataCategory = dataCategory.filter(subCategory=subcategory)

    if emp:
        dataStep = dataStep.filter(empDeptName=emp)
        dataCategory = dataCategory.filter(contractId__empDeptName=emp)

    if customer:
        dataStep = dataStep.filter(endCompanyName=customer)
        dataCategory = dataCategory.filter(contractId__endCompanyName=customer)

    Step = dataStep.values('contractStep').annotate(sum_price=Sum('salePrice'))
    Category_main = dataCategory.values('mainCategory').annotate(sum_main=Sum('itemPrice'))
    Category_sub = dataCategory.values('subCategory').annotate(sum_sub=Sum('itemPrice'))
    Emp = dataStep.values('empDeptName').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice')).order_by('empDeptName')
    Company = dataStep.values('endCompanyName').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice'))

    dataStep = list(Step)
    dataStep.extend(list(Category_main))
    dataStep.extend(list(Category_sub))
    dataStep.extend(list(Emp))
    dataStep.extend(list(Company))

    structureStep = json.dumps(dataStep, cls=DjangoJSONEncoder)

    return HttpResponse(structureStep, content_type='application/json')


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
def quarter_opp_asjson(request):
    today_year = datetime.today().year
    dict_quarter = {"q1_start": "{}-01-01".format(today_year),
                    "q1_end": "{}-04-01".format(today_year),
                    "q2_end": "{}-07-01".format(today_year),
                    "q3_end": "{}-10-01".format(today_year),
                    "q4_end": "{}-01-01".format(today_year + 1)}
    step = request.POST['step']
    team = request.POST['team']
    if team == '합계':
        team = ''
    month = request.POST['month']
    month = month.replace('월', '')
    cumulative = request.POST['cumulative']
    quarter = request.POST['quarter']

    dataOpp = Contract.objects.filter(Q(contractStep='Opportunity')&Q(contractDate__year=today_year))

    if quarter:
        if cumulative == 'Y':
            if quarter == '1분기':
                dataOpp = dataOpp.filter(Q(contractDate__gte=dict_quarter['q1_start']) & Q(contractDate__lt=dict_quarter['q1_end']))
            elif quarter == '2분기':
                dataOpp = dataOpp.filter(Q(contractDate__gte=dict_quarter['q1_start']) & Q(contractDate__lt=dict_quarter['q2_end']))
            elif quarter == '3분기':
                dataOpp = dataOpp.filter(Q(contractDate__gte=dict_quarter['q1_start']) & Q(contractDate__lt=dict_quarter['q3_end']))
            elif quarter == '4분기':
                dataOpp = dataOpp.filter(Q(contractDate__gte=dict_quarter['q1_start']) & Q(contractDate__lt=dict_quarter['q4_end']))
        elif cumulative == 'N':
            if quarter == '1분기':
                dataOpp = dataOpp.filter(Q(contractDate__gte=dict_quarter['q1_start']) & Q(contractDate__lt=dict_quarter['q1_end']))
            elif quarter == '2분기':
                dataOpp = dataOpp.filter(Q(contractDate__gte=dict_quarter['q1_end']) & Q(contractDate__lt=dict_quarter['q2_end']))
            elif quarter == '3분기':
                dataOpp = dataOpp.filter(Q(contractDate__gte=dict_quarter['q2_end']) & Q(contractDate__lt=dict_quarter['q3_end']))
            elif quarter == '4분기':
                dataOpp = dataOpp.filter(Q(contractDate__gte=dict_quarter['q3_end']) & Q(contractDate__lt=dict_quarter['q4_end']))

    if team:
        dataOpp = dataOpp.filter(Q(empDeptName=team))

    if month:
        dataOpp = dataOpp.filter(Q(contractDate__month=month))

    dataOpp = dataOpp.values('contractStep', 'empDeptName', 'empName', 'contractCode', 'contractName', 'saleCompanyName', 'salePrice', 'profitPrice', 'contractDate', 'contractId')
    structureStep = json.dumps(list(dataOpp), cls=DjangoJSONEncoder)
    return HttpResponse(structureStep, content_type='application/json')


@login_required
@csrf_exempt
def quarter_firm_asjson(request):
    today_year = datetime.today().year
    dict_quarter = {"q1_start": "{}-01-01".format(today_year),
                    "q1_end": "{}-04-01".format(today_year),
                    "q2_end": "{}-07-01".format(today_year),
                    "q3_end": "{}-10-01".format(today_year),
                    "q4_end": "{}-01-01".format(today_year + 1)}
    step = request.POST['step']
    team = request.POST['team']
    if team == '합계':
        team = ''
    month = request.POST['month']
    month = month.replace('월', '')
    cumulative = request.POST['cumulative']
    quarter = request.POST['quarter']

    dataFirm = Revenue.objects.filter(Q(billingDate__year=today_year))

    if quarter:
        if cumulative == 'Y':
            if quarter == '1분기':
                dataFirm = dataFirm.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q1_end']))
            elif quarter == '2분기':
                dataFirm = dataFirm.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q2_end']))
            elif quarter == '3분기':
                dataFirm = dataFirm.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q3_end']))
            elif quarter == '4분기':
                dataFirm = dataFirm.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q4_end']))
        elif cumulative == 'N':
            if quarter == '1분기':
                dataFirm = dataFirm.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q1_end']))
            elif quarter == '2분기':
                dataFirm = dataFirm.filter(Q(billingDate__gte=dict_quarter['q1_end']) & Q(billingDate__lt=dict_quarter['q2_end']))
            elif quarter == '3분기':
                dataFirm = dataFirm.filter(Q(billingDate__gte=dict_quarter['q2_end']) & Q(billingDate__lt=dict_quarter['q3_end']))
            elif quarter == '4분기':
                dataFirm = dataFirm.filter(Q(billingDate__gte=dict_quarter['q3_end']) & Q(billingDate__lt=dict_quarter['q4_end']))

    if team:
        dataFirm = dataFirm.filter(Q(contractId__empDeptName=team))

    if month:
        dataFirm = dataFirm.filter(Q(billingDate__month=month))

    dataFirm = dataFirm.values('billingDate', 'contractId__contractCode', 'contractId__contractName', 'contractId__saleCompanyName__companyName', 'revenuePrice', 'revenueProfitPrice',
                               'contractId__empName', 'contractId__empDeptName', 'revenueId')

    structureStep = json.dumps(list(dataFirm), cls=DjangoJSONEncoder)
    return HttpResponse(structureStep, content_type='application/json')
