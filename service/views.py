import json

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa

from client.models import Company
from hr.models import Employee
from noticeboard.models import Board
from sales.models import Contract
from extrapay.models import OverHour, ExtraPay
from .forms import ServicereportForm, ServiceformForm, AdminServiceForm, ServiceTypeForm, ReportForm
from .functions import *
from approval.functions import who_approval, mail_approval
from .models import Servicereport, Vacation, Serviceform, Geolocation, Servicetype, Vacationcategory, Report, Participant
from sales.models import Contractfile
from approval.models import Document, Documentform, Documentfile, Relateddocument, Approval


@login_required
@csrf_exempt
def service_asjson(request):
    selectType = request.POST['selectType']
    if selectType == 'show':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        empCheck = int(request.POST['empCheck'])
        companyName = request.POST['companyName']
        serviceType = request.POST['serviceType']
        contractName = request.POST['contractName']
        contractCheck = int(request.POST['contractCheck'])
        serviceTitle = request.POST['serviceTitle']

        services = Servicereport.objects.all()
        if empCheck == 0:
            if empDeptName:
                services = services.filter(empDeptName__icontains=empDeptName)
            if empName:
                services = services.filter(empName__icontains=empName)
        elif empCheck == 1:
            services = services.filter(empId=request.user.employee)

        if startdate:
            services = services.filter(serviceDate__gte=startdate)
        if enddate:
            services = services.filter(serviceDate__lte=enddate)
        if companyName:
            services = services.filter(companyName__companyName__icontains=companyName)
        if serviceType:
            services = services.filter(serviceType__typeName__icontains=serviceType)

        if contractCheck == 0:
            if contractName:
                services = services.filter(contractId__contractName__icontains=contractName)
        elif contractCheck == 1:
            services = services.filter(contractId__isnull=True)

        if serviceTitle:
            services = services.filter(Q(serviceTitle__icontains=serviceTitle) | Q(serviceDetails__icontains=serviceTitle))

    elif selectType == 'change':
        companyName = request.POST['companyName']
        services = Servicereport.objects.filter(
            empId=request.user.employee.empId,
            contractId__isnull=True,
        )
        if companyName:
            services = services.filter(companyName__companyName__icontains=companyName)

    services = services.values(
        'serviceDate', 'companyName__companyName', 'serviceTitle', 'empName', 'directgo', 'serviceType',
        'serviceBeginDatetime', 'serviceStartDatetime', 'serviceEndDatetime', 'serviceFinishDatetime',
        'serviceHour', 'serviceOverHour', 'serviceDetails',
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
            # if request.POST['contractId']:
            #     post.contractId = Contract.objects.get(contractId=request.POST['contractId'])
            # else:
            #     post.contractId = None
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
                post.serviceRegHour = round(post.serviceHour - post.serviceOverHour, 1)
                post.save()
                return redirect('scheduler:scheduler', str(post.serviceBeginDatetime)[:10])

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
                        post.serviceRegHour = round(post.serviceHour - post.serviceOverHour, 1)
                        timeCalculateFlag = False
                    Servicereport.objects.create(
                        # contractId=post.contractId,
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
                return redirect('scheduler:scheduler', firstDate)

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
                            post.serviceRegHour = round(post.serviceHour - post.serviceOverHour, 1)
                            timeCalculateFlag = False
                        Servicereport.objects.create(
                            # contractId=post.contractId,
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
                return redirect('scheduler:scheduler', firstDate)

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
                        post.serviceRegHour = round(post.serviceHour - post.serviceOverHour, 1)
                        timeCalculateFlag = False
                    Servicereport.objects.create(
                        # contractId=post.contractId,
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
                return redirect('scheduler:scheduler', firstDate)

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
    emp = request.user.employee
    empName = emp.empName
    empDeptName = emp.empDeptName
    now = datetime.datetime.now()

    if request.method == "POST":
        vacationDays = list(request.POST.keys())[1:-9]

        # 문서 종류 선택
        formId = Documentform.objects.get(
            categoryId__firstCategory='공통',
            categoryId__secondCategory='자동생성',
            formTitle='휴가신청서',
        )

        preservationYear = formId.preservationYear
        securityLevel = formId.securityLevel
        vacationCategory = Vacationcategory.objects.get(categoryId=request.POST['vacationCategory'])
        comment = request.POST['comment']

        # 문서번호 자동생성 (yymmdd-000)
        yymmdd = str(datetime.date.today()).replace('-', '')[2:]
        todayDocumentCount = len(Document.objects.filter(documentNumber__contains=yymmdd))
        documentNumber = yymmdd + '-' + str(todayDocumentCount + 1).rjust(3, '0')

        # 문서 전처리 (\n 없애고, '를 "로 변경)
        HTML = formId.formHtml
        HTML = HTML.replace('성함자동입력', empName)
        HTML = HTML.replace('부서자동입력', empDeptName)
        HTML = HTML.replace('종류자동입력', vacationCategory.categoryName)

        vacationDay = 0
        vacationDate = ''
        weekday = ['월', '화', '수', '목', '금', '토', '일']
        for day in vacationDays:
            dtday = datetime.datetime(year=int(day[:4]), month=int(day[5:7]), day=int(day[8:10]))
            vacationDate += day + '(' + weekday[dtday.weekday()] + ')'
            if request.POST[day] == 'all':
                vacationDay += 1
                vacationDate += ' (일차)<br>'
            elif request.POST[day] == 'am':
                vacationDay += 0.5
                vacationDate += ' (오전반차)<br>'
            elif request.POST[day] == 'pm':
                vacationDay += 0.5
                vacationDate += ' (오후반차)<br>'
            
        HTML = HTML.replace('일수자동입력', str(vacationDay) + '일')
        HTML = HTML.replace('기간자동입력', vacationDate)
        HTML = HTML.replace('사유자동입력', comment)

        # 문서 등록
        document = Document.objects.create(
            documentNumber=documentNumber,
            writeEmp=request.user.employee,
            formId=formId,
            preservationYear=preservationYear,
            securityLevel=securityLevel,
            title='[휴가신청] ' + empName + '님의 ' + vacationCategory.categoryName + ' 신청의 건',
            contentHtml=HTML,
            writeDatetime=now,
            modifyDatetime=now,
            draftDatetime=now,
            documentStatus='진행',
        )

        # 첨부파일 처리
        # 1. 첨부파일 업로드 정보
        jsonFile = json.loads(request.POST['jsonFile'])
        filesInfo = {}  # {fileName1: fileSize1, fileName2: fileSize2, ...}
        filesName = []  # [fileName1, fileName2, ...]
        for i in jsonFile:
            filesInfo[i['fileName']] = i['fileSize']
            filesName.append(i['fileName'])
        # 2. 업로드 된 파일 중, 화면에서 삭제하지 않은 것만 등록
        for f in request.FILES.getlist('files'):
            if f.name in filesName:
                Documentfile.objects.create(
                    documentId=document,
                    file=f,
                    fileName=f.name,
                    fileSize=filesInfo[f.name][:-2],
                )

        # 관련문서 처리
        jsonId = json.loads(request.POST['relatedDocumentId'])
        for relatedId in jsonId:
            relatedDocument = Document.objects.get(documentId=relatedId)
            Relateddocument.objects.create(
                documentId=document,
                relatedDocumentId=relatedDocument,
            )

        # 결재선 처리
        approval = []
        if request.POST['apply']:
            applyList = request.POST['apply'].split(',')
            for i, a in enumerate(applyList):
                if a != '':
                    approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '신청'})
        if request.POST['process']:
            processList = request.POST['process'].split(',')
            for i, p in enumerate(processList):
                if p != '':
                    approval.append({'approvalEmp': p, 'approvalStep': i + 1, 'approvalCategory': '승인'})
        if request.POST['reference']:
            referenceList = request.POST['reference'].split(',')
            for i, r in enumerate(referenceList):
                if r != '':
                    approval.append({'approvalEmp': r, 'approvalStep': i + 1, 'approvalCategory': '참조'})

        for a in approval:
            empId = Employee.objects.get(empId=a['approvalEmp'])
            # 기안자는 자동 결재
            if empId.user == request.user and a['approvalStep'] == 1:
                Approval.objects.create(
                    documentId=document,
                    approvalEmp=empId,
                    approvalStep=a['approvalStep'],
                    approvalCategory=a['approvalCategory'],
                    approvalStatus='완료',
                    approvalDatetime=now,
                )
            else:
                Approval.objects.create(
                    documentId=document,
                    approvalEmp=empId,
                    approvalStep=a['approvalStep'],
                    approvalCategory=a['approvalCategory'],
                )

        whoApproval = who_approval(document.documentId)
        if len(whoApproval['do']) == 0:
            document.documentStatus = '완료'
            document.approveDatetime = now
            document.save()
        else:
            for empId in whoApproval['do']:
                employee = Employee.objects.get(empId=empId)
                mail_approval(employee, document, "결재요청")

        for vacationDate in vacationDays:
            if request.POST[vacationDate] == 'all':
                vacationType = "일차"
            elif request.POST[vacationDate] == 'am':
                vacationType = "오전반차"
            elif request.POST[vacationDate] == 'pm':
                vacationType = "오후반차"
            else:
                vacationType = ""

            Vacation.objects.create(
                documentId=document,
                empId=emp,
                empName=empName,
                empDeptName=empDeptName,
                vacationDate=vacationDate,
                vacationType=vacationType,
                vacationCategory=vacationCategory,
                rewardVacationType=request.POST['rewardVacationType'],
                comment=comment,
            )

        if len(whoApproval['do']) == 0:
            Vacation.objects.filter(documentId=document).update(vacationStatus='Y')

        if vacationCategory.categoryName == '하계휴가':
            emp.empAnnualLeave -= vacationDay
            emp.save()
        elif vacationCategory.categoryName == '동계휴가':
            emp.empSpecialLeave -= vacationDay
            emp.save()
        return redirect('service:showvacations')

    else:
        # 결재자 자동완성
        empList = Employee.objects.filter(Q(empStatus='Y'))
        empNames = []
        for e in empList:
            temp = {
                'id': e.empId,
                'name': e.empName,
                'position': e.empPosition.positionName,
                'dept': e.empDeptName,
            }
            empNames.append(temp)

        context = {
            'empNames': empNames,
            'vacationCategory': Vacationcategory.objects.all(),
        }
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
    # filter values
    if request.method == "POST":
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        if 'empCheck' not in request.POST.keys():
            empCheck = 0
        else:
            empCheck = 1
        companyName = request.POST['companyName']
        serviceType = request.POST['serviceType']
        contractName = request.POST['contractName']
        if 'contractCheck' not in request.POST.keys():
            contractCheck = 0
        else:
            contractCheck = 1
        serviceTitle = request.POST['serviceTitle']
    else:
        today = str(datetime.datetime.now())[:10]
        yyyy = today[:4]
        mm = today[5:7]
        if mm == '01':
            yyyyBefore = str(int(yyyy) - 1)
            mmBefore = '12'
        else:
            yyyyBefore = yyyy
            mmBefore = str(int(mm) - 1).zfill(2)

        # startdate = yyyyBefore + '-' + mmBefore + '-01'
        startdate = today
        enddate = today
        empDeptName = ""
        empName = ""
        empCheck = 1
        companyName = ""
        serviceType = ""
        contractName = ""
        contractCheck = 0
        serviceTitle = ""

    startDay = ""
    endDay = ""
    services = Servicereport.objects.all()
    if empCheck == 0:
        if empDeptName:
            services = services.filter(empDeptName__icontains=empDeptName)
        if empName:
            services = services.filter(empName__icontains=empName)
    elif empCheck == 1:
        services = services.filter(empId=request.user.employee)

    if startdate:
        services = services.filter(serviceDate__gte=startdate)
        startDay = datetime.date(year=int(startdate[:4]), month=int(startdate[5:7]), day=int(startdate[8:10]))
    if enddate:
        services = services.filter(serviceDate__lte=enddate)
        endDay = datetime.date(year=int(enddate[:4]), month=int(enddate[5:7]), day=int(enddate[8:10]))
    if companyName:
        services = services.filter(companyName__companyName__icontains=companyName)
    if serviceType:
        services = services.filter(serviceType__typeName__icontains=serviceType)

    if contractCheck == 0:
        if contractName:
            services = services.filter(contractId__contractName__icontains=contractName)
    elif contractCheck == 1:
        services = services.filter(contractId__isnull=True)

    if serviceTitle:
        services = services.filter(Q(serviceTitle__icontains=serviceTitle) | Q(serviceDetails__icontains=serviceTitle))

    if services:
        countServices = services.count()
        sumHour = round(services.aggregate(Sum('serviceHour'))['serviceHour__sum'], 1)
        sumOverHour = round(services.aggregate(Sum('serviceOverHour'))['serviceOverHour__sum'], 1)
    else:
        countServices = 0
        sumHour = 0
        sumOverHour = 0

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
        'countServices': countServices,
        'sumHour': sumHour,
        'sumOverHour': sumOverHour,

        # filter values
        'startdate': startdate,
        'enddate': enddate,
        'startDay': startDay,
        'endDay': endDay,
        'empDeptName': empDeptName,
        'empName': empName,
        'empCheck': empCheck,
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

    beforeServiceDate = service.serviceDate - datetime.timedelta(days=1)
    afterServiceDate = service.serviceDate + datetime.timedelta(days=1)

    coWorkerSign = Servicereport.objects.filter(
        serviceDate__lte=afterServiceDate,
        serviceDate__gte=beforeServiceDate,
        companyName=service.companyName,
        coWorker__contains=service.empId.empId,
    ).exclude(
        serviceSignPath='/media/images/signature/nosign.jpg'
    )

    context = {
        'service': service,
        'contractName': contractName,
        'board': board,
        'coWorker': coWorker,
        'coWorkerSign': coWorkerSign,
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
    return redirect('scheduler:scheduler', str(datetime.datetime.today())[:10])


@login_required
def delete_service(request, serviceId):
    Servicereport.objects.filter(serviceId=serviceId).delete()
    return redirect('scheduler:scheduler', str(datetime.datetime.today())[:10])


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
            # if request.POST['contractId']:
            #     post.contractId = Contract.objects.get(contractId=request.POST['contractId'])
            # else:
            post.contractId = None
            post.empId = empId
            post.empName = empName
            post.empDeptName = empDeptName
            if post.serviceStatus == 'N':
                post.serviceBeginDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
                post.serviceStartDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
                post.serviceEndDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
                post.serviceFinishDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
            elif post.serviceStatus == 'B':
                post.serviceStartDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
                post.serviceEndDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
                post.serviceFinishDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
            elif post.serviceStatus == 'S':
                post.serviceEndDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
                post.serviceFinishDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
            elif post.serviceStatus == 'E':
                post.serviceFinishDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
            post.serviceDate = str(post.serviceBeginDatetime)[:10]
            post.serviceHour = str_to_timedelta_hour(post.serviceFinishDatetime, post.serviceBeginDatetime)
            post.serviceOverHour = overtime(
                form.clean()['startdate'] + ' ' + form.clean()['starttime'],
                form.clean()['enddate'] + ' ' + form.clean()['endtime']
            )
            post.serviceRegHour = round(post.serviceHour - post.serviceOverHour, 1)
            post.coWorker = request.POST['coWorkerId']
            post.save()
            return redirect('scheduler:scheduler', str(post.serviceBeginDatetime)[:10])
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
    )
    return redirect('scheduler:scheduler', instance.serviceDate)


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
def showvacations_asjson(request):
    emp = Employee.objects.get(empId=request.GET['empId'])
    vacations = Vacation.objects.filter(empId=emp).values(
        'vacationDate', 'vacationType', 'vacationCategory__categoryName', 'comment', 'vacationStatus',
        'documentId__documentId',
    )

    structure = json.dumps(list(vacations), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def delete_vacation(request, vacationId):
    Vacation.objects.filter(vacationId=vacationId).delete()
    return redirect('service:showvacations')


@login_required
def day_report(request, day=None):
    # 20년 2월 1일 이전
    if day is None:
        day = str(datetime.datetime.today())[:10]

    if day <= '2020-01-31':
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

    # 20년 2월 1일 부터
    else:
        Date = datetime.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]))
        beforeDate = Date - datetime.timedelta(days=1)
        afterDate = Date + datetime.timedelta(days=1)

        sales = dayreport_query(empDeptName=["인프라솔루션사업부", "영업팀"], day=day)
        rnd = dayreport_query(empDeptName=["R&D 전략사업부", "Technical Architecture팀", "AI Platform Labs"], day=day)
        db = dayreport_query(empDeptName=["Platform Biz", "DB Expert팀"], day=day)
        solution = dayreport_query(empDeptName=["Platform Biz", "솔루션팀"], day=day)

        dept = request.user.employee.empDeptName
        rows = []
        if dept == "Technical Architecture팀" or dept == "AI Platform Labs":
            rows.append([
                {'title': '[R&D 전략사업부]TA팀·AI Labs', 'service': rnd[0], 'education': rnd[1], 'vacation': rnd[2]},
                {'title': '[인프라솔루션사업부]영업팀', 'service': sales[0], 'education': sales[1], 'vacation': sales[2]},
            ])
            rows.append([
                {'title': '[Platform Biz]솔루션팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
                {'title': '[Platform Biz]DB Expert팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
            ])
        elif dept == '솔루션팀':
            rows.append([
                {'title': '[Platform Biz]솔루션팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
                {'title': '[Platform Biz]DB Expert팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
            ])
            rows.append([
                {'title': '[인프라솔루션사업부]영업팀', 'service': sales[0], 'education': sales[1], 'vacation': sales[2]},
                {'title': '[R&D 전략사업부]TA팀·AI Labs', 'service': rnd[0], 'education': rnd[1], 'vacation': rnd[2]},
            ])
        elif dept == 'DB Expert팀':
            rows.append([
                {'title': '[Platform Biz]DB Expert팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
                {'title': '[Platform Biz]솔루션팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
            ])
            rows.append([
                {'title': '[인프라솔루션사업부]영업팀', 'service': sales[0], 'education': sales[1], 'vacation': sales[2]},
                {'title': '[R&D 전략사업부]TA팀·dAI Labs', 'service': rnd[0], 'education': rnd[1], 'vacation': rnd[2]},
            ])
        else:
            rows.append([
                {'title': '[인프라솔루션사업부]영업팀', 'service': sales[0], 'education': sales[1], 'vacation': sales[2]},
                {'title': '[R&D 전략사업부]TA팀·AI Labs', 'service': rnd[0], 'education': rnd[1], 'vacation': rnd[2]},
            ])
            rows.append([
                {'title': '[Platform Biz]솔루션팀', 'service': solution[0], 'education': solution[1], 'vacation': solution[2]},
                {'title': '[Platform Biz]DB Expert팀', 'service': db[0], 'education': db[1], 'vacation': db[2]},
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
        service.serviceRegHour = round(service.serviceHour - service.serviceOverHour, 1)
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
        service.serviceRegHour = round(service.serviceHour - service.serviceOverHour, 1)
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
        service.serviceRegHour = round(service.serviceHour - service.serviceOverHour, 1)
        service.serviceStatus = 'E'
        service.save()

    elif status == "finish":
        post = Geolocation.objects.get(serviceId=serviceId)
        post.finishLatitude = float(latitude)
        post.finishLongitude = float(longitude)

        # 거리, 경로, 길찾기 결과코드
        latlngs = [
            [post.beginLatitude, post.beginLongitude],
            [post.startLatitude, post.startLongitude],
            [post.endLatitude, post.endLongitude],
            [post.finishLatitude, post.finishLongitude],
        ]
        distance, path, distanceCode, tollMoney = naver_distance(latlngs)
        post.distance = distance
        post.path = path
        post.tollMoney = tollMoney
        post.distanceCode = distanceCode

        # 거리 계산 비율
        beginAlias, beginRegion = reverse_geo(post.beginLatitude, post.beginLongitude)
        startAlias, startRegion = reverse_geo(post.startLatitude, post.startLongitude)
        endAlias, endRegion = reverse_geo(post.endLatitude, post.endLongitude)
        finishAlias, finishRegion = reverse_geo(post.finishLatitude, post.finishLongitude)
        if beginAlias not in ['서울', '경기'] or startAlias not in ['서울', '경기'] or endAlias not in ['서울', '경기'] or finishAlias not in ['서울', '경기']:
            post.distanceRatio = 1.0

        # 출발, 시작, 종료, 도착 위치
        if distanceCode == 0:
            post.beginLocation = beginRegion
            post.startLocation = startRegion
            post.endLocation = endRegion
            post.finishLocation = finishRegion

        post.save()

        service.serviceFinishDatetime = datetime.datetime.now()
        service.serviceHour = str_to_timedelta_hour(str(service.serviceFinishDatetime), str(service.serviceBeginDatetime))
        if service.empName == '이현수':
            service.serviceOverHour, overhour, min_date, max_date = overtime_extrapay_etc(str(service.serviceBeginDatetime), str(service.serviceFinishDatetime))
        else:
            service.serviceOverHour, overhour, min_date, max_date = overtime_extrapay(str(service.serviceBeginDatetime), str(service.serviceFinishDatetime))
        service.serviceRegHour = round(service.serviceHour - service.serviceOverHour, 1)
        service.serviceStatus = 'Y'

        # overhour create
        # 석식대
        if service.empId.empRewardAvailable == '가능':
            foodcosts = cal_foodcost(str(service.serviceBeginDatetime), str(service.serviceFinishDatetime))
            if foodcosts > 0 or overhour > 0:
                emp = Employee.objects.get(empId=service.empId_id)
                overhourcost = emp.empSalary*overhour*1.5

                # IF문으로 해당 엔지니어의 월별 정보가 extrapay에 있는지 확인하고 없으면 생성
                service_year = service.serviceDate.year
                service_month = service.serviceDate.month
                extrapay = ExtraPay.objects.filter(
                    Q(overHourDate__year=service_year) &
                    Q(overHourDate__month=service_month) &
                    Q(empId=service.empId_id)
                ).first()
                if extrapay:
                    sumOverHour = extrapay.sumOverHour
                    extrapay.sumOverHour = float(sumOverHour)+float(overhour)
                    extrapay.save()
                else:
                    extrapay = ExtraPay.objects.create(
                        empId=service.empId,
                        empName=service.empName,
                        overHourDate=service.serviceDate,
                        sumOverHour=overhour,
                    )

                OverHour.objects.create(
                    serviceId=service,
                    empId=service.empId,
                    empName=service.empName,
                    overHourTitle=service.serviceTitle,
                    overHourStartDate=min_date,
                    overHourEndDate=max_date,
                    overHour=overhour,
                    overHourCost=overhourcost,
                    foodCost=foodcosts,
                    extraPayId=extrapay,
                )

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
def admin_service(request, serviceId):
    # 로그인 사용자 정보
    empId = Employee(empId=request.user.employee.empId)
    if empId.empId == 1:
        serviceInstance = Servicereport.objects.get(serviceId=serviceId)
        geoInstance = Geolocation.objects.get(serviceId=serviceId)

        if request.method == "POST":
            form = AdminServiceForm(request.POST, instance=serviceInstance)

            if form.is_valid():
                # 일정(Servicereport) 수정
                post = form.save(commit=False)
                if request.POST['contractId']:
                    post.contractId = Contract.objects.get(contractId=request.POST['contractId'])
                else:
                    post.contractId = None
                post.serviceBeginDatetime = form.clean()['begindate'] + ' ' + form.clean()['begintime']
                post.serviceStartDatetime = form.clean()['startdate'] + ' ' + form.clean()['starttime']
                post.serviceEndDatetime = form.clean()['enddate'] + ' ' + form.clean()['endtime']
                post.serviceFinishDatetime = form.clean()['finishdate'] + ' ' + form.clean()['finishtime']
                post.serviceDate = str(post.serviceBeginDatetime)[:10]
                post.serviceHour = str_to_timedelta_hour(post.serviceFinishDatetime, post.serviceBeginDatetime)
                post.serviceOverHour = overtime(post.serviceBeginDatetime, post.serviceFinishDatetime)
                post.serviceRegHour = round(post.serviceHour - post.serviceOverHour, 1)
                post.coWorker = request.POST['coWorkerId']

                # 초과근무 등록
                if post.empName == '이현수':
                    post.serviceOverHour, overhour, min_date, max_date = overtime_extrapay_etc(
                        str(post.serviceBeginDatetime), str(post.serviceFinishDatetime)
                    )
                else:
                    post.serviceOverHour, overhour, min_date, max_date = overtime_extrapay(
                        str(post.serviceBeginDatetime), str(post.serviceFinishDatetime)
                    )
                post.serviceRegHour = round(post.serviceHour - post.serviceOverHour, 1)
                post.serviceStatus = 'Y'
                post.save()

                # 기존 초과근무 삭제
                overhourInstance = OverHour.objects.filter(serviceId=post).first()
                if overhourInstance:
                    extrapay = ExtraPay.objects.filter(
                        Q(overHourDate__year=post.serviceDate[:4]) &
                        Q(overHourDate__month=post.serviceDate[5:7]) &
                        Q(empId=post.empId_id)
                    ).first()
                    if extrapay:
                        extrapay.sumOverHour = float(extrapay.sumOverHour) - overhourInstance.overHour
                        extrapay.save()
                    overhourInstance.delete()

                # 식대
                if post.empId.empRewardAvailable == '가능':
                    foodcosts = cal_foodcost(str(post.serviceBeginDatetime), str(post.serviceFinishDatetime))
                    if foodcosts > 0 or overhour > 0:
                        emp = Employee.objects.get(empId=post.empId_id)
                        overhourcost = emp.empSalary * overhour * 1.5

                        # 해당 엔지니어의 월별 정보가 extrapay에 있는지 확인하고 없으면 생성 (이 부분 수정)
                        service_year = post.serviceDate[:4]
                        service_month = post.serviceDate[5:7]
                        extrapay = ExtraPay.objects.filter(
                            Q(overHourDate__year=service_year) &
                            Q(overHourDate__month=service_month) &
                            Q(empId=post.empId_id)
                        ).first()
                        if extrapay:
                            extrapay.sumOverHour = float(extrapay.sumOverHour) + float(overhour)
                            extrapay.save()
                        else:
                            extrapay = ExtraPay.objects.create(
                                empId=post.empId,
                                empName=post.empName,
                                overHourDate=post.serviceDate,
                                sumOverHour=overhour,
                            )

                        OverHour.objects.create(
                            serviceId=post,
                            empId=post.empId,
                            empName=post.empName,
                            overHourTitle=post.serviceTitle,
                            overHourStartDate=min_date,
                            overHourEndDate=max_date,
                            overHour=overhour,
                            overHourCost=overhourcost,
                            foodCost=foodcosts,
                            extraPayId=extrapay,
                        )

                # 위치 정보 수정
                post = Geolocation.objects.get(serviceId=serviceId)
                post.beginLatitude = float(form.clean()['beginLatitude'])
                post.beginLongitude = float(form.clean()['beginLongitude'])
                post.startLatitude = float(form.clean()['startLatitude'])
                post.startLongitude = float(form.clean()['startLongitude'])
                post.endLatitude = float(form.clean()['endLatitude'])
                post.endLongitude = float(form.clean()['endLongitude'])
                post.finishLatitude = float(form.clean()['finishLatitude'])
                post.finishLongitude = float(form.clean()['finishLongitude'])

                # 거리, 경로, 길찾기 결과코드
                latlngs = [
                    [post.beginLatitude, post.beginLongitude],
                    [post.startLatitude, post.startLongitude],
                    [post.endLatitude, post.endLongitude],
                    [post.finishLatitude, post.finishLongitude],
                ]
                distance, path, distanceCode, tollMoney = naver_distance(latlngs)
                post.distance = distance
                post.path = path
                post.tollMoney = tollMoney
                post.distanceCode = distanceCode

                # 거리 계산 비율
                beginAlias, beginRegion = reverse_geo(post.beginLatitude, post.beginLongitude)
                startAlias, startRegion = reverse_geo(post.startLatitude, post.startLongitude)
                endAlias, endRegion = reverse_geo(post.endLatitude, post.endLongitude)
                finishAlias, finishRegion = reverse_geo(post.finishLatitude, post.finishLongitude)
                if beginAlias not in ['서울', '경기'] or startAlias not in ['서울', '경기'] or \
                        endAlias not in ['서울', '경기'] or finishAlias not in ['서울', '경기']:
                    post.distanceRatio = 1.0

                # 출발, 시작, 종료, 도착 위치
                if distanceCode == 0:
                    post.beginLocation = beginRegion
                    post.startLocation = startRegion
                    post.endLocation = endRegion
                    post.finishLocation = finishRegion

                post.save()

                return redirect('service:viewservice', serviceId)
        else:
            form = AdminServiceForm(instance=serviceInstance)
            form.fields['begindate'].initial = str(serviceInstance.serviceBeginDatetime)[:10]
            form.fields['begintime'].initial = str(serviceInstance.serviceBeginDatetime)[11:16]
            form.fields['startdate'].initial = str(serviceInstance.serviceStartDatetime)[:10]
            form.fields['starttime'].initial = str(serviceInstance.serviceStartDatetime)[11:16]
            form.fields['enddate'].initial = str(serviceInstance.serviceEndDatetime)[:10]
            form.fields['endtime'].initial = str(serviceInstance.serviceEndDatetime)[11:16]
            form.fields['finishdate'].initial = str(serviceInstance.serviceFinishDatetime)[:10]
            form.fields['finishtime'].initial = str(serviceInstance.serviceFinishDatetime)[11:16]
            form.fields['beginLatitude'].initial = str(geoInstance.beginLatitude)
            form.fields['beginLongitude'].initial = str(geoInstance.beginLongitude)
            form.fields['startLatitude'].initial = str(geoInstance.startLatitude)
            form.fields['startLongitude'].initial = str(geoInstance.startLongitude)
            form.fields['endLatitude'].initial = str(geoInstance.endLatitude)
            form.fields['endLongitude'].initial = str(geoInstance.endLongitude)
            form.fields['finishLatitude'].initial = str(geoInstance.finishLatitude)
            form.fields['finishLongitude'].initial = str(geoInstance.finishLongitude)

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

            # 동행자 자동완성
            empList = Employee.objects.filter(Q(empStatus='Y'))
            empNames = []
            for emp in empList:
                temp = {'id': emp.empId, 'value': emp.empName}
                empNames.append(temp)

            context = {
                'form': form,
                'service': serviceInstance,
                'contracts': contracts,
                'companyNames': companyNames,
                'empNames': empNames,
                'contractId': contractId,
                'companyName': serviceInstance.companyName,
                'coWorkers': serviceInstance.coWorker,
            }
            return render(request, 'service/adminservice.html', context)


def save_confirm_files(request, contractId):
    if request.method == 'POST':
        # 0. serviceId 정보
        serviceId = request.POST['serviceId']

        # 1. 첨부파일 업로드 정보
        jsonFile = json.loads(request.POST['jsonFile'])
        filesInfo = {}  # {fileName1: fileSize1, fileName2: fileSize2, ...}
        filesName = []  # [fileName1, fileName2, ...]
        for i in jsonFile:
            filesInfo[i['fileName']] = i['fileSize']
            filesName.append(i['fileName'])

        # 2. 업로드 된 파일 중, 화면에서 삭제하지 않은 것만 등록
        for f in request.FILES.getlist('files'):
            if f.name in filesName:
                Contractfile.objects.create(
                    contractId=Contract.objects.get(contractId=contractId),
                    fileCategory='납품,구축,검수확인서',
                    fileName=f.name,
                    fileSize=filesInfo[f.name][:-2],
                    file=f,
                    uploadEmp=request.user.employee,
                    uploadDatetime=datetime.datetime.now(),
                )
        return redirect('service:viewservice', serviceId)


@login_required
def show_service_type(request):
    context = {}
    return render(request, 'service/showservicetype.html', context)


@login_required
def showservicetype_asjson(request):
    serviceType = Servicetype.objects.all().values(
        'typeId', 'typeName', 'orderNumber',
    )

    structure = json.dumps(list(serviceType), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def view_service_type(request, typeId):
    serviceType = Servicetype.objects.get(typeId=typeId)

    if request.method == 'POST':
        form = ServiceTypeForm(request.POST, instance=serviceType)
        form.save()
        return redirect('service:showservicetype')

    else:
        form = ServiceTypeForm(instance=serviceType)

        context = {
            'serviceType': serviceType,
            'form': form,
        }
        return render(request, 'service/postservicetype.html', context)


@login_required
def post_service_type(request):
    if request.method == 'POST':
        form = ServiceTypeForm(request.POST)
        form.save()
        return redirect('service:showservicetype')
    else:
        form = ServiceTypeForm()

        context = {
            'form': form
        }

        return render(request, 'service/postservicetype.html', context)


@login_required
def delete_service_type(request, typeId):
    Servicetype.objects.get(typeId=typeId).delete()
    return redirect('service:showservicetype')


@login_required
def coworker_sign(request, serviceId):
    if request.method == 'POST':
        signId = Servicereport.objects.get(serviceId=request.POST['signId'])
        service = Servicereport.objects.get(serviceId=serviceId)
        service.serviceSignPath = signId.serviceSignPath
        service.save()
        return redirect('service:viewservice', serviceId)


# 주간회의록
@login_required
def show_reports(request):
    if request.method == 'POST':
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        category = request.POST['category']
        writer = request.POST['writer']
    else:
        startdate = ''
        enddate = ''
        category = ''
        writer = ''
    categories = [i[0] for i in Report.categoryChoices]

    context = {
        'startdate': startdate,
        'enddate': enddate,
        'category': category,
        'writer': writer,
        'categories': categories,
    }
    return render(request, 'service/showreports.html', context)


@login_required
@csrf_exempt
def reports_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    category = request.POST['category']
    writer = request.POST['writer']

    reports = Report.objects.all()
    if startdate:
        reports = reports.filter(reportDate__gte=startdate)
    if enddate:
        reports = reports.filter(reportDate__lte=enddate)
    if category:
        reports = reports.filter(category=category)
    if writer:
        reports = reports.filter(writer__empName__icontains=writer)
    result = reports.values('reportId', 'category', 'reportDate', 'writer__empName', 'writeDatetime', 'modifyDatetime')
    structure = json.dumps(list(result), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)

        if form.is_valid():
            # 회의록 등록
            post = form.save(commit=False)
            post.leader = Employee.objects.get(empId=request.POST['leader'])
            post.writer = Employee.objects.get(empId=request.POST['writer'])
            post.contents = request.POST['contents']
            post.save()

            # 참가자 등록
            if request.POST['participants']:
                participants = request.POST['participants'].split(',')
                for participant in participants:
                    Participant.objects.create(
                        reportId=post,
                        empId=Employee.objects.get(empId=participant),
                    )
            return redirect('service:showreports')

        else:
            return HttpResponse('입력된 양식이 잘못되었습니다.')

    else:
        form = ReportForm()
        form.fields['category'].initial = '주간회의'
        form.fields['reportDate'].initial = str(datetime.datetime.now())[:10]
        form.fields['reportTime'].initial = "10:00"
        contents = weekly_report(request.GET['startdate'], request.GET['enddate'])

        # 직원 자동완성
        empList = Employee.objects.filter(Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {'id': emp.empId, 'value': emp.empName}
            empNames.append(temp)

        context = {
            'form': form,
            'empNames': empNames,
            'contents': contents,
        }
        return render(request, 'service/postreport.html', context)


@login_required
def view_report(request, reportId):
    report = Report.objects.get(reportId=reportId)
    participants = Participant.objects.filter(reportId=report)
    context = {
        'report': report,
        'participants': participants,
    }
    return render(request, 'service/viewreport.html', context)


@login_required
def delete_report(request, reportId):
    Report.objects.get(reportId=reportId).delete()
    return redirect('service:showreports')


@ login_required
def modify_report(request, reportId):
    instance = Report.objects.get(reportId=reportId)
    participants = Participant.objects.filter(reportId__reportId=reportId)

    if request.method == 'POST':
        form = ReportForm(request.POST, instance=instance)

        if form.is_valid():
            # 회의록 등록
            post = form.save(commit=False)
            post.leader = Employee.objects.get(empId=request.POST['leader'])
            post.writer = Employee.objects.get(empId=request.POST['writer'])
            post.contents = request.POST['contents']
            post.save()

            # 참가자 등록
            participants.delete()
            if request.POST['participants']:
                participants = request.POST['participants'].split(',')
                for participant in participants:
                    Participant.objects.create(
                        reportId=post,
                        empId=Employee.objects.get(empId=participant),
                    )
            return redirect('service:showreports')

        else:
            return HttpResponse('입력된 양식이 잘못되었습니다.')

    else:
        form = ReportForm(instance=instance)

        # 직원 자동완성
        empList = Employee.objects.filter(Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {'id': emp.empId, 'value': emp.empName}
            empNames.append(temp)

        participantIds = ''
        for participant in participants:
            participantIds += (str(participant.empId.empId) + ',')
        participantIds = participantIds[:-1]

        context = {
            'form': form,
            'empNames': empNames,
            'leader': instance.leader.empId,
            'writer': instance.writer.empId,
            'participants': participantIds,
            'contents': instance.contents,
        }
        return render(request, 'service/postreport.html', context)\



@login_required
def view_report_pdf(request, reportId):
    report = Report.objects.get(reportId=reportId)
    participants = Participant.objects.filter(reportId=report)
    context = {
        'report': report,
        'participants': participants,
    }
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{} 회의록.pdf"'.format(report.reportDate)

    template = get_template('service/viewreportpdf.html')
    html = template.render(context, request)
    # create a pdf
    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

