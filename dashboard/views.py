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
from sales.models import Contract, Category, Contractitem



@login_required
def dashboard_service(request):
    template = loader.get_template('dashboard/dashboardservice.html')

    # 기간 설정 했을 경우
    if request.method == "POST":

        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        print(startdate, enddate)

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
    context = {
    }
    return HttpResponse(template.render(context, request))


@login_required
def dashboard_sales(request):
    template = loader.get_template('dashboard/dashboardsales.html')
    context = {
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
def opportunity_asjson(request):
    step = request.POST['step']
    category = request.POST['category']
    emp = request.POST['emp']
    print (step,category,emp)

    dataStep = Contract.objects.all()
    dataCategory = Contractitem.objects.all()
    dataEmp = Contract.objects.all()

    if step:
        dataStep = dataStep.filter(contractStep=step)
        dataCategory = dataCategory.filter(contractId__contractStep=step)
        dataEmp = dataEmp.filter(contractStep=step)

    if category:
        dataStep = dataStep.filter(contractitem__mainCategory=category)
        dataCategory = dataCategory.filter(mainCategory=category)
        dataEmp = dataEmp.filter(contractitem__mainCategory=category)

    if emp:
        dataStep = dataStep.filter(empDeptName=emp)
        dataCategory = dataCategory.filter(contractId__empDeptName=emp)
        dataEmp = dataStep.filter(empDeptName=emp)

    dataStep_opp = dataStep.values('contractStep').filter(contractStep='Opportunity').annotate(sum_price=Sum('predictSalePrice'))
    dataStep_firm = dataStep.values('contractStep').filter(contractStep='Firm').annotate(sum_price=Sum('salePrice'))
    dataCategory_main = dataCategory.values('mainCategory').annotate(count_main=Count('mainCategory'))
    dataCategory_sub = dataCategory.values('subCategory').annotate(sub_category=Count('subCategory'))
    dataEmp_opp = dataEmp.values('empDeptName').filter(contractStep='Opportunity').annotate(sum_price=Sum('predictSalePrice')).annotate(sum_=Sum('predictProfitPrice')).order_by('empDeptName')
    dataEmp_firm = dataEmp.values('empDeptName').filter(contractStep='Firm').annotate(sum_price=Sum('salePrice')).annotate(sum_profit=Sum('profitPrice')).order_by('empDeptName')

    # dataStep = list(dataStep_opp)
    # dataStep.extend(list(dataStep_firm))
    # dataCategory = list(dataCategory_main)
    # dataCategory.extend(list(dataCategory_sub))
    # dataEmp = list(dataEmp_opp)
    # dataEmp.extend(list(dataEmp_firm))
    dataStep = list(dataStep_opp)
    dataStep.extend(list(dataStep_firm))
    dataStep.extend(list(dataCategory_main))
    dataStep.extend(list(dataCategory_sub))
    dataStep.extend(list(dataEmp_opp))
    dataStep.extend(list(dataEmp_firm))

    structureStep = json.dumps(dataStep, cls=DjangoJSONEncoder)
    # structureCategory = json.dumps(dataCategory, cls=DjangoJSONEncoder)
    # structureEmp = json.dumps(dataEmp, cls=DjangoJSONEncoder)
    print(structureStep)
    # print(structureCategory)
    # print(structureEmp)
    return HttpResponse(structureStep, content_type='application/json')
