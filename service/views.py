# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Sum, Max, F, Value, FloatField
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from xhtml2pdf import pisa
import json
import datetime
from dateutil.relativedelta import relativedelta

from hr.models import Employee
from client.models import Company
from noticeboard.models import Board
from sales.models import Contract
from .forms import ServicereportForm, ServiceformForm
from .functions import *
from .models import Serviceform, Geolocation, Car, Oil, Fuel


@login_required
@csrf_exempt
def service_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    empDeptName = request.POST['empDeptName']
    empName = request.POST['empName']
    companyName = request.POST['companyName']
    serviceType = request.POST['serviceType']
    contractName = request.POST['contractName']
    if 'contractCheck' not in request.POST.keys():
        contractCheck = 0
    else:
        contractCheck = int(request.POST['contractCheck'])
    selectType = request.POST['selectType']
    serviceTitle = request.POST['serviceTitle']

    if selectType == 'show':
        if startdate or enddate or empDeptName or empName or companyName or serviceType or serviceTitle:
            services = Servicereport.objects.all()
            if startdate:
                services = services.filter(serviceDate__gte=startdate)
            if enddate:
                services = services.filter(serviceDate__lte=enddate)
            if empDeptName:
                services = services.filter(empDeptName__icontains=empDeptName)
            if empName:
                services = services.filter(empName__icontains=empName)
            if companyName:
                services = services.filter(companyName__companyName__icontains=companyName)
            if serviceType:
                services = services.filter(serviceType__icontains=serviceType)
            if contractCheck == 0:
                if contractName:
                    services = services.filter(contractId__contractName__icontains=contractName)
            elif contractCheck == 1:
                services = services.filter(contractId__isnull=True)
            if serviceTitle:
                services = services.filter(Q(serviceTitle__icontains=serviceTitle) | Q(serviceDetails__icontains=serviceTitle))
        else:
            services = Servicereport.objects.filter(empId=request.user.employee.empId)
            if contractCheck == 1:
                services = services.filter(contractId__isnull=True)

    elif selectType == 'change':
        services = Servicereport.objects.filter(empId=request.user.employee.empId)
        if companyName:
            services = services.filter(companyName__companyName__icontains=companyName)
        if contractCheck == 1:
            services = services.filter(contractId__isnull=True)

    services = services.values(
        'serviceDate', 'companyName__companyName', 'serviceTitle', 'empName', 'directgo', 'serviceType',
        'serviceStartDatetime', 'serviceEndDatetime', 'serviceHour', 'serviceOverHour', 'serviceDetails',
        'serviceStatus', 'contractId__contractName', 'serviceId'
    )

    structure = json.dumps(list(services), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_service(request, postdate):
    # 로그인 사용자 정보
    empId = Employee(empId=request.user.employee.empId)
    empName = request.user.employee.empName
    empDeptName = request.user.employee.empDeptName

    if request.method == "POST":
        form = ServicereportForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            if request.POST['contractId']:
                post.contractId = Contract.objects.get(contractId=request.POST['contractId'])
            else:
                post.contractId = None
            post.empId = empId
            post.empName = empName
            post.empDeptName = empDeptName
            post.coWorker = request.POST['coWorkerId']
            for_status = request.POST['for']

            # 기본등록
            if for_status == 'for_n':
                post.serviceBeginDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
                post.serviceStartDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
                post.serviceEndDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
                post.serviceFinishDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
                post.serviceDate = str(post.serviceBeginDatetime)[:10]
                post.serviceHour = str_to_timedelta_hour(post.serviceFinishDatetime, post.serviceBeginDatetime)
                post.serviceOverHour = overtime(post.serviceBeginDatetime, post.serviceFinishDatetime)
                post.serviceRegHour = post.serviceHour - post.serviceOverHour
                post.save()
                return redirect('scheduler', str(post.serviceBeginDatetime)[:10])

            # 매월반복
            elif for_status == 'for_my':
                dateRange = month_list(form.clean()['startdate'], form.clean()['enddate'])
                firstDate = str(dateRange[0])[:10]
                timeCalculateFlag = True
                for date in dateRange:
                    post.serviceBeginDatetime = str(date) + ' ' + form.clean()['starttime']
                    post.serviceStartDatetime = str(date) + ' ' + form.clean()['starttime']
                    post.serviceEndDatetime = str(date) + ' ' + form.clean()['endtime']
                    post.serviceFinishDatetime = str(date) + ' ' + form.clean()['endtime']
                    post.serviceDate = str(post.serviceBeginDatetime)[:10]
                    if timeCalculateFlag:
                        post.serviceHour = str_to_timedelta_hour(post.serviceFinishDatetime, post.serviceBeginDatetime)
                        post.serviceOverHour = overtime(post.serviceBeginDatetime, post.serviceFinishDatetime)
                        post.serviceRegHour = post.serviceHour - post.serviceOverHour
                        timeCalculateFlag = False
                    Servicereport.objects.create(
                        contractId=post.contractId,
                        serviceDate=post.serviceDate,
                        empId=post.empId,
                        empName=post.empName,
                        empDeptName=post.empDeptName,
                        companyName=post.companyName,
                        serviceType=post.serviceType,
                        serviceBeginDatetime=post.serviceBeginDatetime,
                        serviceStartDatetime=post.serviceStartDatetime,
                        serviceEndDatetime=post.serviceEndDatetime,
                        serviceFinishDatetime=post.serviceFinishDatetime,
                        serviceHour=post.serviceHour,
                        serviceOverHour=post.serviceOverHour,
                        serviceRegHour=post.serviceRegHour,
                        serviceLocation=post.serviceLocation,
                        directgo=post.directgo,
                        coWorker=post.coWorker,
                        serviceTitle=post.serviceTitle,
                        serviceDetails=post.serviceDetails,
                        serviceStatus=post.serviceStatus,
                    )
                return redirect('scheduler', firstDate)

            # 기간(휴일제외)
            elif for_status == 'for_hn':
                dateRange = date_list(form.clean()['startdate'], form.clean()['enddate'])
                firstDate = str(dateRange[0])[:10]
                timeCalculateFlag = True
                for date in dateRange:
                    if not Eventday.objects.filter(Q(eventDate=date) & Q(eventType='휴일')) \
                            and date.weekday() != 5 and date.weekday() != 6:
                        post.serviceBeginDatetime = str(date) + ' ' + form.clean()['starttime']
                        post.serviceStartDatetime = str(date) + ' ' + form.clean()['starttime']
                        post.serviceEndDatetime = str(date) + ' ' + form.clean()['endtime']
                        post.serviceFinishDatetime = str(date) + ' ' + form.clean()['endtime']
                        post.serviceDate = str(post.serviceBeginDatetime)[:10]
                        if timeCalculateFlag:
                            post.serviceHour = str_to_timedelta_hour(post.serviceFinishDatetime, post.serviceBeginDatetime)
                            post.serviceOverHour = overtime(post.serviceBeginDatetime, post.serviceFinishDatetime)
                            post.serviceRegHour = post.serviceHour - post.serviceOverHour
                            timeCalculateFlag = False
                        Servicereport.objects.create(
                            contractId=post.contractId,
                            serviceDate=post.serviceDate,
                            empId=post.empId,
                            empName=post.empName,
                            empDeptName=post.empDeptName,
                            companyName=post.companyName,
                            serviceType=post.serviceType,
                            serviceBeginDatetime=post.serviceBeginDatetime,
                            serviceStartDatetime=post.serviceStartDatetime,
                            serviceEndDatetime=post.serviceEndDatetime,
                            serviceFinishDatetime=post.serviceFinishDatetime,
                            serviceHour=post.serviceHour,
                            serviceOverHour=post.serviceOverHour,
                            serviceRegHour=post.serviceRegHour,
                            serviceLocation=post.serviceLocation,
                            directgo=post.directgo,
                            coWorker=post.coWorker,
                            serviceTitle=post.serviceTitle,
                            serviceDetails=post.serviceDetails,
                            serviceStatus=post.serviceStatus,
                        )
                return redirect('scheduler', firstDate)

            # 기간(휴일포함)
            elif for_status == 'for_hy':
                dateRange = date_list(form.clean()['startdate'], form.clean()['enddate'])
                firstDate = str(dateRange[0])[:10]
                timeCalculateFlag = True
                for date in dateRange:
                    post.serviceBeginDatetime = str(date) + ' ' + form.clean()['starttime']
                    post.serviceStartDatetime = str(date) + ' ' + form.clean()['starttime']
                    post.serviceEndDatetime = str(date) + ' ' + form.clean()['endtime']
                    post.serviceFinishDatetime = str(date) + ' ' + form.clean()['endtime']
                    post.serviceDate = str(post.serviceBeginDatetime)[:10]
                    if timeCalculateFlag:
                        post.serviceHour = str_to_timedelta_hour(post.serviceFinishDatetime, post.serviceBeginDatetime)
                        post.serviceOverHour = overtime(post.serviceBeginDatetime, post.serviceFinishDatetime)
                        post.serviceRegHour = post.serviceHour - post.serviceOverHour
                        timeCalculateFlag = False
                    Servicereport.objects.create(
                        contractId=post.contractId,
                        serviceDate=post.serviceDate,
                        empId=post.empId,
                        empName=post.empName,
                        empDeptName=post.empDeptName,
                        companyName=post.companyName,
                        serviceType=post.serviceType,
                        serviceBeginDatetime=post.serviceBeginDatetime,
                        serviceStartDatetime=post.serviceStartDatetime,
                        serviceEndDatetime=post.serviceEndDatetime,
                        serviceFinishDatetime=post.serviceFinishDatetime,
                        serviceHour=post.serviceHour,
                        serviceOverHour=post.serviceOverHour,
                        serviceRegHour=post.serviceRegHour,
                        serviceLocation=post.serviceLocation,
                        directgo=post.directgo,
                        coWorker=post.coWorker,
                        serviceTitle=post.serviceTitle,
                        serviceDetails=post.serviceDetails,
                        serviceStatus=post.serviceStatus,
                    )
                return redirect('scheduler', firstDate)

    else:
        form = ServicereportForm()
        form.fields['startdate'].initial = postdate
        form.fields['starttime'].initial = "09:00"
        form.fields['enddate'].initial = postdate
        form.fields['endtime'].initial = "18:00"
        serviceforms = Serviceform.objects.filter(empId=empId)

        # 계약명 자동완성
        contractList = Contract.objects.filter(
            Q(endCompanyName__isnull=False)
            # & Q(contractStartDate__lte=datetime.datetime.today()) & Q(contractEndDate__gte=datetime.datetime.today())
        )
        contracts = []
        for contract in contractList:
            temp = {
                'id': contract.pk,
                'value': '[' + contract.endCompanyName.pk + '] ' + contract.contractName + ' (' +
                         str(contract.contractStartDate)[2:].replace('-', '.') + ' ~ ' +
                         str(contract.contractEndDate)[2:].replace('-', '.') + ')',
                'company': contract.endCompanyName.pk
            }
            contracts.append(temp)

        # 고객사명 자동완성
        companyList = Company.objects.filter(Q(companyStatus='Y')).order_by('companyNameKo')
        companyNames = []
        for company in companyList:
            temp = {'id': company.pk, 'value': company.pk}
            companyNames.append(temp)

        # 동행자 자동완성
        empList = Employee.objects.filter(Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {'id': emp.empId, 'value': emp.empName}
            empNames.append(temp)

        context = {
            'form': form,
            'postdate': postdate,
            'serviceforms': serviceforms,
            'contracts': contracts,
            'companyNames': companyNames,
            'empNames': empNames,
        }
        return render(request, 'service/postservice.html', context)


@login_required
def post_vacation(request):
    # 로그인 사용자 정보
    empId = Employee(empId=request.user.employee.empId)
    empName = request.user.employee.empName
    empDeptName = request.user.employee.empDeptName

    if request.method == "POST":
        vacationTypeDict = request.POST
        dateArray = list(request.POST.keys())[1:]

        for vacationDate in dateArray:
            if vacationTypeDict[vacationDate] == 'all':
                vacationType = "일차"
            elif vacationTypeDict[vacationDate] == 'am':
                vacationType = "오전반차"
            elif vacationTypeDict[vacationDate] == 'pm':
                vacationType = "오후반차"
            else:
                vacationType = ""

            Vacation.objects.create(
                empId=empId,
                empName=empName,
                empDeptName=empDeptName,
                vacationDate=vacationDate,
                vacationType=vacationType
            )
        return redirect('scheduler', dateArray[0])

    else:
        context = {}
        return render(request, 'service/postvacation.html', context)


@login_required
def post_serviceform(request):
    empId = Employee(empId=request.user.employee.empId)

    if request.method == "POST":
        form = ServiceformForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.empId = empId
            post.save()
            return redirect('service:postservice', str(datetime.date.today()))

    else:
        form = ServiceformForm()
        form.fields['serviceStartTime'].initial = "09:00"
        form.fields['serviceEndTime'].initial = "18:00"
        context = {
            'form': form,
        }
        return render(request, 'service/postserviceform.html', context)


@login_required
def show_services(request):
    if request.method == "POST":
        # filter values
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName'] or request.user.employee.empName
        companyName = request.POST['companyName']
        serviceType = request.POST['serviceType']
        contractName = request.POST['contractName']
        if 'contractCheck' not in request.POST.keys():
            contractCheck = 0
        else:
            contractCheck = 1
        serviceTitle = request.POST['serviceTitle']

        services = Servicereport.objects.all()
        if startdate:
            services = services.filter(serviceDate__gte=startdate)
        if enddate:
            services = services.filter(serviceDate__lte=enddate)
        if empDeptName:
            services = services.filter(empDeptName__icontains=empDeptName)
        if empName:
            services = services.filter(empName__icontains=empName)
        if companyName:
            services = services.filter(companyName__companyName__icontains=companyName)
        if serviceType:
            services = services.filter(serviceType__icontains=serviceType)
        if contractCheck == 0:
            if contractName:
                services = services.filter(contractId__contractName__icontains=contractName)
        elif contractCheck == 1:
            services = services.filter(contractId__isnull=True)
        if serviceTitle:
            services = services.filter(Q(serviceTitle__icontains=serviceTitle) | Q(serviceDetails__icontains=serviceTitle))

    else:
        empId = Employee(empId=request.user.employee.empId)
        services = Servicereport.objects.filter(empId=empId)

        # filter values
        startdate = ""
        enddate = ""
        empDeptName = ""
        empName = request.user.employee.empName
        companyName = ""
        serviceType = ""
        contractName = ""
        contractCheck = 0
        serviceTitle = ""

    # 계약명 자동완성
    contractList = Contract.objects.filter(
        Q(endCompanyName__isnull=False)
        # & Q(contractStartDate__lte=datetime.datetime.today()) & Q(contractEndDate__gte=datetime.datetime.today())
    )
    contracts = []
    for contract in contractList:
        temp = {
            'id': contract.pk,
            'value': '[' + contract.endCompanyName.pk + '] ' + contract.contractName + ' (' +
                     str(contract.contractStartDate)[2:].replace('-', '.') + ' ~ ' +
                     str(contract.contractEndDate)[2:].replace('-', '.') + ')',
            'company': contract.endCompanyName.pk
        }
        contracts.append(temp)

    context = {
        'today': datetime.datetime.today(),
        'countServices': services.count() or 0,
        'sumHour': services.aggregate(Sum('serviceHour'))['serviceHour__sum'] or 0,
        'sumOverHour': services.aggregate(Sum('serviceOverHour'))['serviceOverHour__sum'] or 0,
        # filter values
        'startdate': startdate,
        'enddate': enddate,
        'empDeptName': empDeptName,
        'empName': empName,
        'companyName': companyName,
        'serviceType': serviceType,
        'contractName': contractName,
        'contractCheck': contractCheck,
        'serviceTitle': serviceTitle,
        # contracts
        'contracts': contracts,
    }
    return render(request, 'service/showservices.html', context)


@login_required
def view_service(request, serviceId):
    service = Servicereport.objects.get(serviceId=serviceId)

    if service.contractId:
        contractName = service.contractId.contractName\
                       + ' (' + str(service.contractId.contractStartDate)[2:].replace('-', '.')\
                       + ' ~ ' + str(service.contractId.contractEndDate)[2:].replace('-', '.') + ')'
        if contractName.split(' ')[0] == service.companyName.companyName:
            contractName = ' '.join(contractName.split(' ')[1:])
    else:
        contractName = ''

    if service.coWorker:
        coWorker = []
        for coWorkerId in service.coWorker.split(','):
            coWorker.append(str(Employee.objects.get(empId=coWorkerId).empName))
    else:
        coWorker = ''

    try:
        board = Board.objects.get(serviceId__serviceId=serviceId)
    except:
        board = None

    context = {
        'service': service,
        'contractName': contractName,
        'board': board,
        'coWorker': coWorker,
    }

    if service.serviceStatus == "Y":
        return render(request, 'service/viewserviceY.html', context)
    else:
        return render(request, 'service/viewserviceN.html', context)


@login_required
def save_service(request, serviceId):
    service = Servicereport.objects.get(serviceId=serviceId)
    service.serviceStatus = 'Y'
    service.serviceFinishDatetime = datetime.datetime.now()
    service.save()
    return redirect('scheduler', str(datetime.datetime.today())[:10])


@login_required
def delete_service(request, serviceId):
    Servicereport.objects.filter(serviceId=serviceId).delete()
    return redirect('scheduler', str(datetime.datetime.today())[:10])


@login_required
def modify_service(request, serviceId):
    # 로그인 사용자 정보
    instance = Servicereport.objects.get(serviceId=serviceId)
    empId = Employee(empId=request.user.employee.empId)
    empName = request.user.employee.empName
    empDeptName = request.user.employee.empDeptName

    if request.method == "POST":
        form = ServicereportForm(request.POST, instance=instance)

        if form.is_valid():
            post = form.save(commit=False)
            if request.POST['contractId']:
                post.contractId = Contract.objects.get(contractId=request.POST['contractId'])
            else:
                post.contractId = None
            post.empId = empId
            post.empName = empName
            post.empDeptName = empDeptName
            post.serviceBeginDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
            post.serviceStartDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
            post.serviceEndDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
            post.serviceFinishDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
            post.serviceDate = str(post.serviceBeginDatetime)[:10]
            post.serviceHour = str_to_timedelta_hour(post.serviceFinishDatetime, post.serviceBeginDatetime)
            post.serviceOverHour = overtime(post.serviceBeginDatetime, post.serviceFinishDatetime)
            post.serviceRegHour = post.serviceHour - post.serviceOverHour
            post.coWorker = request.POST['coWorkerId']
            post.save()
            return redirect('scheduler', str(post.serviceBeginDatetime)[:10])
    else:
        form = ServicereportForm(instance=instance)
        form.fields['startdate'].initial = str(instance.serviceBeginDatetime)[:10]
        form.fields['starttime'].initial = str(instance.serviceBeginDatetime)[11:16]
        form.fields['enddate'].initial = str(instance.serviceFinishDatetime)[:10]
        form.fields['endtime'].initial = str(instance.serviceFinishDatetime)[11:16]

        # 계약명 자동완성
        contractList = Contract.objects.filter(
            Q(endCompanyName__isnull=False)
            # & Q(contractStartDate__lte=datetime.datetime.today()) & Q(contractEndDate__gte=datetime.datetime.today())
        )
        contracts = []
        for contract in contractList:
            temp = {
                'id': contract.pk,
                'value': '[' + contract.endCompanyName.pk + '] ' + contract.contractName + ' (' +
                         str(contract.contractStartDate)[2:].replace('-', '.') + ' ~ ' +
                         str(contract.contractEndDate)[2:].replace('-', '.') + ')',
                'company': contract.endCompanyName.pk
            }
            contracts.append(temp)

        if Servicereport.objects.get(serviceId=serviceId).contractId:
            contractId = Servicereport.objects.get(serviceId=serviceId).contractId.contractId
        else:
            contractId = ''

        # 고객사명 자동완성
        companyList = Company.objects.filter(Q(companyStatus='Y')).order_by('companyNameKo')
        companyNames = []
        for company in companyList:
            temp = {'id': company.pk, 'value': company.pk}
            companyNames.append(temp)

        companyName = Servicereport.objects.get(serviceId=serviceId).companyName

        # 동행자 자동완성
        empList = Employee.objects.filter(Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {'id': emp.empId, 'value': emp.empName}
            empNames.append(temp)

        coWorkers = Servicereport.objects.get(serviceId=serviceId).coWorker
        serviceStatus = Servicereport.objects.get(serviceId=serviceId).serviceStatus

        context = {
            'form': form,
            'contracts': contracts,
            'companyNames': companyNames,
            'empNames': empNames,
            'contractId': contractId,
            'companyName': companyName,
            'coWorkers': coWorkers,
            'serviceStatus': serviceStatus,
        }
        return render(request, 'service/postservice.html', context)


@login_required
def copy_service(request, serviceId):
    # 로그인 사용자 정보
    instance = Servicereport.objects.get(serviceId=serviceId)
    empId = Employee(empId=request.user.employee.empId)
    empName = request.user.employee.empName
    empDeptName = request.user.employee.empDeptName
    Servicereport.objects.create(
        serviceDate=instance.serviceDate,
        contractId=instance.contractId,
        empId=empId,
        empName=empName,
        empDeptName=empDeptName,
        companyName=instance.companyName,
        serviceType=instance.serviceType,
        serviceBeginDatetime=instance.serviceBeginDatetime,
        serviceStartDatetime=instance.serviceStartDatetime,
        serviceEndDatetime=instance.serviceEndDatetime,
        serviceFinishDatetime=instance.serviceFinishDatetime,
        serviceHour=instance.serviceHour,
        serviceOverHour=instance.serviceOverHour,
        serviceRegHour=instance.serviceRegHour,
        serviceLocation=instance.serviceLocation,
        directgo=instance.directgo,
        serviceTitle=instance.serviceTitle,
        serviceDetails=instance.serviceDetails,
        serviceStatus=instance.serviceStatus,
    )
    return redirect('scheduler', instance.serviceDate)


@login_required
def show_serviceforms(request):
    empId = Employee(empId=request.user.employee.empId)
    serviceforms = Serviceform.objects.filter(empId=empId)

    context = {
        'serviceforms': serviceforms,
    }
    return render(request, 'service/showserviceforms.html', context)


@login_required
def modify_serviceform(request, serviceFormId):
    instance = Serviceform.objects.get(serviceFormId=serviceFormId)
    empId = Employee(empId=request.user.employee.empId)

    if request.method == "POST":
        form = ServiceformForm(request.POST, instance=instance)

        if form.is_valid():
            post = form.save(commit=False)
            post.empId = empId
            post.save()
            return redirect('service:postservice', str(datetime.date.today()))

    else:
        form = ServiceformForm(instance=instance)
        context = {
            'form': form,
            'serviceFormId': serviceFormId,
        }
        return render(request, 'service/postserviceform.html', context)


@login_required
def delete_serviceform(request, serviceFormId):
    Serviceform.objects.filter(serviceFormId=serviceFormId).delete()
    return redirect('service:showserviceforms')


@login_required
def show_vacations(request):
    empId = Employee(empId=request.user.employee.empId)
    vacations = Vacation.objects.filter(empId=empId)
    context = {
        'vacations': vacations,
    }
    return render(request, 'service/showvacations.html', context)


@login_required
def delete_vacation(request, vacationId):
    Vacation.objects.filter(vacationId=vacationId).delete()
    return redirect('service:showvacations')


@login_required
def day_report(request, day=None):
    if day is None:
        day = str(datetime.datetime.today())[:10]
    Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
    beforeDate = Date - datetime.timedelta(days=1)
    afterDate = Date + datetime.timedelta(days=1)

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

    context = {
        'day': day,
        'Date': Date,
        'beforeDate': beforeDate,
        'afterDate': afterDate,
        'rows': rows,
    }

    return render(request, 'service/dayreport.html', context)


@login_required
def view_service_pdf(request, serviceId):
    service = Servicereport.objects.get(serviceId=serviceId)

    if service.coWorker:
        coWorker = []
        for coWorkerId in service.coWorker.split(','):
            coWorker.append(str(Employee.objects.get(empId=coWorkerId).empName))
    else:
        coWorker = ''

    context = {
        'service': service,
        'coWorker': coWorker
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="SERVICE REPORT.pdf"'
    template = get_template('service/viewservicepdf.html')
    html = template.render(context, request)

    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@login_required
@csrf_exempt
def post_geolocation(request, serviceId, status, latitude, longitude):
    service = Servicereport.objects.get(serviceId=serviceId)
    if service.empId.empId != request.user.employee.empId:
        return HttpResponse('자신의 일정만 수정 가능합니다.')

    if status == "begin":
        Geolocation.objects.create(
            serviceId=Servicereport.objects.get(serviceId=serviceId),
            beginLatitude=float(latitude),
            beginLongitude=float(longitude),
        )
        service.serviceBeginDatetime = datetime.datetime.now()
        service.serviceDate = str(service.serviceBeginDatetime)[:10]
        service.serviceHour = str_to_timedelta_hour(str(service.serviceFinishDatetime), str(service.serviceBeginDatetime))
        service.serviceOverHour = overtime(str(service.serviceBeginDatetime), str(service.serviceFinishDatetime))
        service.serviceRegHour = service.serviceHour - service.serviceOverHour
        service.serviceStatus = 'B'
        service.save()

    elif status == "start":
        post = Geolocation.objects.get(serviceId=serviceId)
        post.startLatitude = float(latitude)
        post.startLongitude = float(longitude)
        post.save()
        service.serviceStartDatetime = datetime.datetime.now()
        service.serviceHour = str_to_timedelta_hour(str(service.serviceFinishDatetime), str(service.serviceBeginDatetime))
        service.serviceOverHour = overtime(str(service.serviceBeginDatetime), str(service.serviceFinishDatetime))
        service.serviceRegHour = service.serviceHour - service.serviceOverHour
        service.serviceStatus = 'S'
        service.save()

    elif status == "end":
        post = Geolocation.objects.get(serviceId=serviceId)
        post.endLatitude = float(latitude)
        post.endLongitude = float(longitude)
        post.save()
        service.serviceEndDatetime = datetime.datetime.now()
        service.serviceHour = str_to_timedelta_hour(str(service.serviceFinishDatetime), str(service.serviceBeginDatetime))
        service.serviceOverHour = overtime(str(service.serviceBeginDatetime), str(service.serviceFinishDatetime))
        service.serviceRegHour = service.serviceHour - service.serviceOverHour
        service.serviceStatus = 'E'
        service.save()

    elif status == "finish":
        post = Geolocation.objects.get(serviceId=serviceId)
        post.finishLatitude = float(latitude)
        post.finishLongitude = float(longitude)
        post.save()
        service.serviceFinishDatetime = datetime.datetime.now()
        service.serviceHour = str_to_timedelta_hour(str(service.serviceFinishDatetime), str(service.serviceBeginDatetime))
        service.serviceOverHour = overtime(str(service.serviceBeginDatetime), str(service.serviceFinishDatetime))
        service.serviceRegHour = service.serviceHour - service.serviceOverHour
        service.serviceStatus = 'Y'
        service.save()

    return redirect('service:viewservice', serviceId)


@login_required
@csrf_exempt
def change_contracts_name(request):
    serviceIds = json.loads(request.POST['serviceId'])
    contractId = request.POST['contractId']

    for serviceId in serviceIds:
        temp = Servicereport.objects.get(serviceId=serviceId)
        temp.contractId = Contract.objects.get(contractId=contractId)
        temp.save()

    return redirect('service:showservices')


@login_required
@csrf_exempt
def post_car(request):
    cars = Car.objects.all().order_by('-oilType', 'carType')

    if request.method == "POST":
        jsonCar = json.loads(request.POST['jsonCar'])
        carId = [i[0] for i in cars.values_list('carId')]
        jsonCarId = []
        for car in jsonCar:
            if car["carId"] == "추가":
                Car.objects.create(
                    oilType=car["oilType"],
                    carType=car["carType"],
                    comment=car["comment"],
                    kpl=car["kpl"],
                )
            else:
                carInstance = cars.get(carId=int(car["carId"]))
                carInstance.oilType = car["oilType"]
                carInstance.carType = car["carType"]
                carInstance.comment = car["comment"]
                carInstance.kpl = car["kpl"]
                carInstance.save()
                jsonCarId.append(int(car["carId"]))

        delCarId = list(set(carId) - set(jsonCarId))
        if delCarId:
            for Id in delCarId:
                Car.objects.filter(carId=Id).delete()

    context = {
        'cars': cars,
    }

    return render(request, 'service/postcar.html', context)


@login_required
@csrf_exempt
def show_oils(request):
    if request.POST:
        selectMonth = datetime.datetime(int(request.POST['findDate'][:4]), int(request.POST['findDate'][5:7]), 1).date()
    else:
        todayMonth = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month, 1).date()
        oilMonth = Oil.objects.aggregate(maxMonth=Max('oilDate'))['maxMonth']
        selectMonth = todayMonth

        if todayMonth != oilMonth:
            selectMonth = todayMonth - relativedelta(months=1)

    oils = Oil.objects.filter(oilDate=selectMonth).order_by('-carId__oilType', 'carId__carType')
    lastOils = Oil.objects.filter(oilDate=selectMonth-relativedelta(months=1))

    joinOils = []

    for oil in oils:
        if lastOils:
            lastmpk = lastOils.filter(carId=oil.carId).first().mpk
        else:
            lastmpk = '-'
        temp = {
            'oilType': oil.carId.oilType,
            'carType': oil.carId.carType,
            'carComment': oil.carId.comment,
            'lastmpk': lastmpk,
            'mpk': oil.mpk,
            'kpl': oil.carId.kpl,
            'oilMoney': oil.oilMoney,
        }
        if lastmpk != '-':
            iad = temp['mpk'] - temp['lastmpk']
            if iad > 0:
                temp['iad'] = str(abs(iad)) + '원상승'
            elif iad < 0:
                temp['iad'] = str(abs(iad)) + '원하락'
            else:
                temp['iad'] = '동일'
        else:
            temp['iad'] = '-'

        joinOils.append(temp)

    context = {
        'selectMonth': selectMonth,
        'joinOils': joinOils,
    }

    return render(request, 'service/showoils.html', context)


@login_required
@csrf_exempt
def post_oils(request):
    if request.method == "POST":
        cars = Car.objects.all()
        if Oil.objects.filter(oilDate=request.POST['oilDate']+'-01'):
            Oil.objects.filter(oilDate=request.POST['oilDate']+'-01').delete()
        for car in cars:
            if car.oilType == '휘발유':
                oilMoney = float(request.POST['gasoline'])
            elif car.oilType == '경유':
                oilMoney = float(request.POST['diesel'])
            elif car.oilType == 'LPG':
                oilMoney = float(request.POST['lpg'])
            else:
                oilMoney = 0
            Oil.objects.create(
                oilDate=request.POST['oilDate'] + '-01',
                carId=car,
                oilMoney=oilMoney,
                mpk=round(oilMoney/car.kpl),
            )
        return redirect('service:showoils')


@login_required
@csrf_exempt
def show_fuel(request):
    if request.method == 'POST':
        y = int(request.POST['findDate'][:4])
        m = int(request.POST['findDate'][5:7])
    else:
        y = datetime.datetime.today().year
        m = datetime.datetime.today().month
    startdate = str(datetime.datetime(y, m, 1).date())
    enddate = str((datetime.datetime(y, m+1, 1) - datetime.timedelta(days=1)).date())
    context = {
        'startdate': startdate,
        'enddate': enddate,
    }
    return render(request, 'service/showfuel.html', context)


@login_required
@csrf_exempt
def post_fuel(request):
    context = {}
    if request.method == 'POST':
        serviceIds = json.loads(request.POST['serviceId'])
        print(serviceIds)
        for serviceId in serviceIds:
            geo = Geolocation.objects.get(serviceId=serviceId)
            distance1 = latlng_distance(geo.beginLatitude, geo.beginLongitude, geo.startLatitude, geo.startLongitude)
            distance2 = latlng_distance(geo.startLatitude, geo.startLongitude, geo.endLatitude, geo.endLongitude)
            distance3 = latlng_distance(geo.endLatitude, geo.endLongitude, geo.finishLatitude, geo.finishLongitude)
            totalDistance = distance1 + distance2 + distance3
            Fuel.objects.create(
                serviceId=Servicereport.objects.get(serviceId=serviceId),
                distance1=distance1,
                distance2=distance2,
                distance3=distance3,
                totalDistance=totalDistance,
            )
    return render(request, 'service/showfuel.html', context)


@login_required
@csrf_exempt
def fuel_asjson(request):
    status = request.POST['status']
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']

    if status == 'post':
        services = Geolocation.objects.select_related().filter(
            Q(serviceId__empId=request.user.employee.empId) &
            Q(serviceId__serviceStatus='Y')
        ).annotate(
            serviceDate=F('serviceId__serviceDate'),
            companyName=F('serviceId__companyName__companyName'),
            serviceTitle=F('serviceId__serviceTitle'),
            distance=Value(0, output_field=FloatField()),
        )
        if startdate:
            services = services.filter(serviceDate__gte=startdate)
        if enddate:
            services = services.filter(serviceDate__lte=enddate)

        services = services.values(
            'serviceId', 'serviceId__serviceId', 'serviceDate', 'companyName', 'serviceTitle', 'distance',
            'beginLatitude', 'beginLongitude', 'startLatitude', 'startLongitude',
            'endLatitude', 'endLongitude', 'finishLatitude', 'finishLongitude',
        )

        for service in services:
            service['distance'] = latlng_distance(
                service['beginLatitude'],
                service['beginLongitude'],
                service['startLatitude'],
                service['startLongitude'],
            ) + latlng_distance(
                service['startLatitude'],
                service['startLongitude'],
                service['endLatitude'],
                service['endLongitude'],
            ) + latlng_distance(
                service['endLatitude'],
                service['endLongitude'],
                service['finishLatitude'],
                service['finishLongitude'],
            )

        structure = json.dumps(list(services), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')

    elif status == 'show':
        services = Fuel.objects.select_related().filter(
            Q(serviceId__empId=request.user.employee.empId) &
            Q(serviceId__serviceStatus='Y')
        ).annotate(
            serviceDate=F('serviceId__serviceDate'),
            companyName=F('serviceId__companyName__companyName'),
            serviceTitle=F('serviceId__serviceTitle'),
        )
        if startdate:
            services = services.filter(serviceDate__gte=startdate)
        if enddate:
            services = services.filter(serviceDate__lte=enddate)

        services = services.values(
            'serviceId__serviceId', 'serviceDate', 'companyName', 'serviceTitle', 'totalDistance',
        )

        structure = json.dumps(list(services), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')