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
from sales.models import Contract, Category, Contractitem, Revenue
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
    overHourlist = overHour.values('serviceStartDatetime', 'serviceEndDatetime', 'empId__empName', 'empId__empDeptName', 'companyName','serviceOverHour','serviceId')
    structure = json.dumps(list(overHourlist), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def filter_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    overHour = Servicereport.objects.filter(Q(serviceOverHour__gt=0)&Q(serviceDate__gte=startdate)&Q(serviceDate__lte=enddate))
    overHourlist = overHour.values('serviceStartDatetime', 'serviceEndDatetime', 'empId__empName', 'empId__empDeptName', 'companyName','serviceOverHour')
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
        # contract = Contract.objects.filter(Q(contractDate__gte=startdate) & Q(contractDate__lte=enddate))
        contract = Contract.objects.all()
        contract_opp = contract.values('contractStep').filter(contractStep='Opportunity').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice'))
        contract_firm = contract.values('contractStep').filter(contractStep='Firm').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice'))
        contract_company = contract.values('endCompanyName')
        allsalePrice = 0
        allprofitPrice = 0

        for i in contract_firm:
            allsalePrice+=i['sum_price']
            allprofitPrice+=i['sum_profit']
        for i in contract_opp:
            allsalePrice+=i['sum_price']
            allprofitPrice+=i['sum_profit']
        context = {
            "startdate": startdate,
            "enddate": enddate,
            "contract_company": contract_company,
            "contract_count": contract.count(),
            "allsalePrice" :allsalePrice,
            "allprofitPrice":allprofitPrice,
            'filter': 'N',
        }
    return HttpResponse(template.render(context, request))


@login_required
def dashboard_quarter(request):
    template = loader.get_template('dashboard/dashboardquarter.html')
    employees = Employee.objects.filter(Q(empDeptName='영업1팀') | Q(empDeptName='영업2팀') | Q(empDeptName='영업3팀') & Q(empStatus='Y'))

    #년도,월,분기
    today_year = datetime.today().year
    today_month = datetime.today().month
    if today_month in [1,2,3]:
        quarter = 1
    elif today_month in [4,5,6]:
        quarter = 2
    elif today_month in [7,8,9]:
        quarter = 3
    elif today_month in [10,11,12]:
        quarter = 4

    revenues = Revenue.objects.all()
    contract = Contract.objects.all()

    dict_quarter = {"q1_start":"{}-01-01".format(today_year),
                    "q1_end":"{}-04-01".format(today_year),
                    "q2_end":"{}-07-01".format(today_year),
                    "q3_end":"{}-10-01".format(today_year),
                    "q4_end":"{}-01-01".format(today_year+1)}


    total_sales = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q4_end']))

    if quarter == 1:
        revenues_accumulate = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start'])&Q(billingDate__lt=dict_quarter['q1_end']))
        revenues_quarter = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start'])&Q(billingDate__lt=dict_quarter['q1_end']))
    elif quarter == 2:
        revenues_accumulate = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start'])&Q(billingDate__lt=dict_quarter['q2_end']))
        revenues_quarter = revenues.filter(Q(billingDate__gte=dict_quarter['q1_end']) & Q(billingDate__lt=dict_quarter['q2_end']))
    elif quarter == 3:
        revenues_accumulate = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start'])&Q(billingDate__lt=dict_quarter['q3_end']))
        revenues_quarter = revenues.filter(Q(billingDate__gte=dict_quarter['q2_end']) & Q(billingDate__lt=dict_quarter['q3_end']))
    elif quarter == 4:
        revenues_accumulate = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start'])&Q(billingDate__lt=dict_quarter['q4_end']))
        revenues_quarter = revenues.filter(Q(billingDate__gte=dict_quarter['q3_end']) & Q(billingDate__lt=dict_quarter['q4_end']))

    ###목표매출금액 & 이익 금액
    ## 목표테이블 생성후 수정 필요
    Target_sales = 30000000000
    Target_profit = 4500000000

    ###누적매출금액 & 이익 금액
    cumulative_sales_amount = total_sales.aggregate(cumulative_sales_amount = Sum('revenuePrice'))
    cumulative_profit_amount = total_sales.aggregate(cumulative_profit_amount=Sum('revenueProfitPrice'))

    ###현재 분기까지 누적매출금액 & 이익 금액
    quarterly_cumulative_sales = revenues_accumulate.aggregate(quarterly_cumulative_sales=Sum('revenuePrice'))
    quarterly_cumulative_profit = revenues_accumulate.aggregate(quarterly_cumulative_profit=Sum('revenueProfitPrice'))

    ###현재 분기 매출금액 & 이익 금액
    quarterly_sales = revenues_quarter.aggregate(quarterly_sales=Sum('revenuePrice'))
    quarterly_profit = revenues_quarter.aggregate(quarterly_profit=Sum('revenueProfitPrice'))

    ###분기별 opportunity&Firm
    #분기 opp
    quarter1_opp = contract.filter(Q(contractDate__gte=dict_quarter['q1_start'])&Q(contractDate__lt=dict_quarter['q1_end'])).aggregate(sum=Sum('salePrice'))
    quarter2_opp = contract.filter(Q(contractDate__gte=dict_quarter['q1_end']) & Q(contractDate__lt=dict_quarter['q2_end'])).aggregate(sum=Sum('salePrice'))
    quarter3_opp = contract.filter(Q(contractDate__gte=dict_quarter['q2_end']) & Q(contractDate__lt=dict_quarter['q3_end'])).aggregate(sum=Sum('salePrice'))
    quarter4_opp = contract.filter(Q(contractDate__gte=dict_quarter['q3_end']) & Q(contractDate__lt=dict_quarter['q4_end'])).aggregate(sum=Sum('salePrice'))
    quarter_opp = [quarter1_opp['sum'],quarter2_opp['sum'],quarter3_opp['sum'],quarter4_opp['sum']]
    for i in range(len(quarter_opp)):
        if quarter_opp[i] == None:
            quarter_opp[i] = 0
    # 분기 Firm
    quarter1_revenues = revenues.filter(Q(billingDate__gte=dict_quarter['q1_start']) & Q(billingDate__lt=dict_quarter['q1_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter2_revenues = revenues.filter(Q(billingDate__gte=dict_quarter['q1_end']) & Q(billingDate__lt=dict_quarter['q2_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter3_revenues = revenues.filter(Q(billingDate__gte=dict_quarter['q2_end']) & Q(billingDate__lt=dict_quarter['q3_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter4_revenues = revenues.filter(Q(billingDate__gte=dict_quarter['q3_end']) & Q(billingDate__lt=dict_quarter['q4_end'])).aggregate(sum=Sum('revenuePrice'))
    quarter_firm = [quarter1_revenues['sum'],quarter2_revenues['sum'],quarter3_revenues['sum'],quarter4_revenues['sum']]
    for i in range(len(quarter_firm)):
        if quarter_firm[i] == None:
            quarter_firm[i] = 0

    ###월별 팀 매출 금액
    salesteam_lst = Employee.objects.values('empDeptName').filter(Q(empStatus='Y')).distinct()
    salesteam_lst = [x['empDeptName'] for x in salesteam_lst if "영업" in x['empDeptName'] ]
    ###월별 팀 매출 금액
    team_revenues = total_sales.values('billingDate__month', 'contractId__empDeptName'
                                       ).annotate(Sum('revenuePrice')).order_by('contractId__empDeptName', 'billingDate__month')

    team_revenues = list(team_revenues)
    for i in salesteam_lst:
        month_lst = [i for i in range(1,13)]
        for j in team_revenues:
            if j['contractId__empDeptName']==i:
                month_lst.remove(j['billingDate__month'] )
        for m in month_lst:
            team_revenues.append({'billingDate__month': m, 'contractId__empDeptName': i, 'revenuePrice__sum': 0})

    team_revenues.sort(key=lambda x: x['contractId__empDeptName'], reverse=False)
    team_revenues.sort(key=lambda x: x['billingDate__month'], reverse=False)

    quarter_opp_Firm = [quarter_opp[quarter-1],quarter_firm[quarter-1]]

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
        "quarter" : quarter,
        "Target_sales" : Target_sales,
        "Target_profit": Target_profit,
        "Sales_rate": round(cumulative_sales_amount['cumulative_sales_amount']/Target_sales*100,2),
        "Profit_rate": round(cumulative_profit_amount['cumulative_profit_amount']/Target_profit*100,2),
        "cumulative_sales_amount" :cumulative_sales_amount['cumulative_sales_amount'],
        "cumulative_profit_amount":cumulative_profit_amount['cumulative_profit_amount'],
        "quarterly_cumulative_sales":quarterly_cumulative_sales['quarterly_cumulative_sales'],
        "quarterly_cumulative_profit":quarterly_cumulative_profit['quarterly_cumulative_profit'],
        "quarterly_sales":quarterly_sales['quarterly_sales'],
        "quarterly_profit":quarterly_profit['quarterly_profit'],
        "quarter_opp":quarter_opp,
        "quarter_firm":quarter_firm,
        "team_revenues":team_revenues,
        "quarter_opp_Firm":quarter_opp_Firm,
        "employees":employees,
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
def dashboard_contract(request):
    template = loader.get_template('dashboard/dashboardcontract.html')
    context = {
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
    dataEmp = Contract.objects.all()

    if step:
        dataStep = dataStep.filter(contractStep=step)
        dataCategory = dataCategory.filter(contractId__contractStep=step)
        dataEmp = dataEmp.filter(contractStep=step)

    if maincategory:
        dataStep = dataStep.filter(contractitem__mainCategory=maincategory)
        dataCategory = dataCategory.filter(mainCategory=maincategory)
        dataEmp = dataEmp.filter(contractitem__mainCategory=maincategory)

    if subcategory:
        dataStep = dataStep.filter(contractitem__subCategory=subcategory)
        dataCategory = dataCategory.filter(subCategory=subcategory)
        dataEmp = dataEmp.filter(contractitem__subCategory=subcategory)

    if emp:
        dataStep = dataStep.filter(empDeptName=emp)
        dataCategory = dataCategory.filter(contractId__empDeptName=emp)
        dataEmp = dataStep.filter(empDeptName=emp)

    if customer:
        dataStep = dataStep.filter(endCompanyName=customer)
        dataCategory = dataCategory.filter(contractId__endCompanyName=customer)
        dataEmp = dataStep.filter(endCompanyName=customer)

    dataStep_opp = dataStep.values('contractStep').filter(contractStep='Opportunity').annotate(sum_price=Sum('salePrice'))
    dataStep_firm = dataStep.values('contractStep').filter(contractStep='Firm').annotate(sum_price=Sum('salePrice'))
    dataCategory_main = dataCategory.values('mainCategory').annotate(sum_main=Sum('itemPrice'))
    dataCategory_sub = dataCategory.values('subCategory').annotate(sum_sub=Sum('itemPrice'))
    dataEmp_opp = dataEmp.values('empDeptName').filter(contractStep='Opportunity').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice')).order_by('empDeptName')
    dataEmp_firm = dataEmp.values('empDeptName').filter(contractStep='Firm').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice')).order_by('empDeptName')
    dataCompany_opp = dataEmp.values('endCompanyName').filter(contractStep='Opportunity').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice'))
    dataCompany_firm = dataEmp.values('endCompanyName').filter(contractStep='Firm').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice'))

    dataStep = list(dataStep_opp)
    dataStep.extend(list(dataStep_firm))
    dataStep.extend(list(dataCategory_main))
    dataStep.extend(list(dataCategory_sub))
    dataStep.extend(list(dataEmp_opp))
    dataStep.extend(list(dataEmp_firm))
    dataStep.extend(list(dataCompany_opp))
    dataStep.extend(list(dataCompany_firm))

    structureStep = json.dumps(dataStep, cls=DjangoJSONEncoder)

    return HttpResponse(structureStep, content_type='application/json')


@login_required
@csrf_exempt
def opportunity_asjson(request):

    step = request.POST['step']
    maincategory = request.POST['maincategory']
    subcategory = request.POST['subcategory']
    emp = request.POST['emp']
    customer = request.POST['customer']


    contract = Contract.objects.all()
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


