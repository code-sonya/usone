from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from hr.models import Employee
from .models import Center, CenterManager, CenterManagerEmp, CheckList, ConfirmCheckList
from .forms import CenterManagerForm
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, FloatField, F, Case, When, Count, Q, Min, Max, Value, CharField
import json
import datetime
from dateutil.relativedelta import relativedelta
from xhtml2pdf import pisa
from service.functions import link_callback
import calendar



# Create your views here.

@login_required
def show_centermanagers(request):
    template = loader.get_template('daesungwork/showcentermanagers.html')
    today = datetime.datetime.today()
    centermanager = CenterManager.objects.filter(Q(centerManagerStatus='Y') & Q(startDate__lte=today) & Q(endDate__gte=today)).order_by('-endDate').first()
    if centermanager:
        centermanageremps = CenterManagerEmp.objects.filter(centerManagerId=centermanager.centerManagerId)
    else:
        centermanageremps = None
    context = {
        'centermanager': centermanager,
        'centermanageremps': centermanageremps,
        'today': today,

    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def post_manager(request):
    template = loader.get_template('daesungwork/postmanager.html')
    if request.method == 'POST':
        form = CenterManagerForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.writeEmp = Employee.objects.get(empId=request.user.employee.empId)
            post.save()

            jsonManagerEmp = json.loads(request.POST['jsonManagerEmp'])
            print(jsonManagerEmp)

            for item in jsonManagerEmp:
                CenterManagerEmp.objects.create(
                    centerManagerId=post,
                    empId=Employee.objects.get(empId=item["empId"]),
                    manageArea=Center.objects.get(Q(centerName=item["manageArea"]) & Q(centerStatus='Y')),
                    additionalArea=item["additionalArea"],
                    cleanupArea=Center.objects.filter(Q(centerName=item["cleanupArea"]) & Q(centerStatus='Y')).first(),
                )

            return redirect('daesungwork:showcentermanagers')

    else:
        form = CenterManagerForm()
        context = {
            'form': form
        }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def modify_centermanager(request, centerManagerId):
    template = loader.get_template('daesungwork/postmanager.html')
    centerManagerInstance = CenterManager.objects.get(centerManagerId=centerManagerId)
    if request.method == 'POST':
        form = CenterManagerForm(request.POST, instance=centerManagerInstance)

        if form.is_valid():
            post = form.save(commit=False)
            post.writeEmp = Employee.objects.get(empId=request.user.employee.empId)
            post.save()

            jsonManagerEmp = json.loads(request.POST['jsonManagerEmp'])
            managerEmpId = list(i[0] for i in CenterManagerEmp.objects.filter(centerManagerId=centerManagerId).values_list('managerId'))
            jsonManagerEmpId = []
            for item in jsonManagerEmp:
                if item['centerManagerEmpId'] == '추가':
                    CenterManagerEmp.objects.create(
                        centerManagerId=post,
                        empId=Employee.objects.get(empId=item["empId"]),
                        manageArea=Center.objects.get(Q(centerName=item["manageArea"]) & Q(centerStatus='Y')),
                        additionalArea=item["additionalArea"],
                        cleanupArea=Center.objects.filter(Q(centerName=item["cleanupArea"]) & Q(centerStatus='Y')).first(),
                    )
                else:
                    managerEmpInstance = CenterManagerEmp.objects.get(managerId=int(item['centerManagerEmpId']))
                    managerEmpInstance.centerManagerId = post
                    managerEmpInstance.empId = Employee.objects.get(empId=item["empId"])
                    managerEmpInstance.manageArea = Center.objects.get(Q(centerName=item["manageArea"]) & Q(centerStatus='Y'))
                    managerEmpInstance.additionalArea = item["additionalArea"]
                    managerEmpInstance.cleanupArea = Center.objects.filter(Q(centerName=item["cleanupArea"]) & Q(centerStatus='Y')).first()
                    managerEmpInstance.save()
                    jsonManagerEmpId.append(int(item['centerManagerEmpId']))

            delManagerEmpId = list(set(managerEmpId) - set(jsonManagerEmpId))
            if delManagerEmpId:
                for Id in delManagerEmpId:
                    CenterManagerEmp.objects.filter(managerId=Id).delete()
            return redirect('daesungwork:showcentermanagers')
        else:
            return HttpResponse('유효하지 않은 형식입니다.')

    else:
        form = CenterManagerForm(instance=centerManagerInstance)
        centerManagerEmps = CenterManagerEmp.objects.filter(centerManagerId=centerManagerId)
        context = {
            'centerManagerId': centerManagerId,
            'form': form,
            'centerManagerEmps': centerManagerEmps,
        }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def center_asjson(request):
    centerManagerId = request.POST['centerManagerId']
    if centerManagerId:
        centers = Center.objects.filter(centerStatus='Y').values('centerName').order_by('centerName')
        employees = Employee.objects.filter(empStatus='Y').values('empName', 'empId').order_by('empId')
        centerManagerEmps = CenterManagerEmp.objects.filter(centerManagerId=centerManagerId)\
            .values('empId', 'empId__empName', 'manageArea__centerName', 'additionalArea', 'cleanupArea__centerName')
        jsonList = []
        jsonList.append(list(centers))
        jsonList.append(list(employees))
        jsonList.append(list(centerManagerEmps))

    else:
        centers = Center.objects.filter(centerStatus='Y').values('centerName').order_by('centerName')
        employees = Employee.objects.filter(empStatus='Y').values('empName', 'empId').order_by('empId')
        jsonList = []
        jsonList.append(list(centers))
        jsonList.append(list(employees))

    structure = json.dumps(jsonList, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def centermanager_asjson(request):
    centermanagers = CenterManager.objects.filter(centerManagerStatus='Y')\
        .values('centerManagerId', 'writeEmp__empName', 'startDate', 'endDate', 'createdDatetime').order_by('centerManagerId')
    structure = json.dumps(list(centermanagers), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
@csrf_exempt
def view_centermanager(request, centerManagerId):
    template = loader.get_template('daesungwork/viewcentermanager.html')
    centermanager = CenterManager.objects.get(centerManagerId=centerManagerId)
    centermanageremps = CenterManagerEmp.objects.filter(centerManagerId=centermanager.centerManagerId)
    context = {
        'centermanager': centermanager,
        'centermanageremps': centermanageremps,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def delete_centermanager(request, centerManagerId):
    centermanager = CenterManager.objects.get(centerManagerId=centerManagerId)
    centermanager.delete()
    return redirect('daesungwork:showcentermanagers')


@login_required
@csrf_exempt
def show_checklist(request):
    template = loader.get_template('daesungwork/showchecklist.html')
    checklist = CheckList.objects.filter(checkListStatus="Y").order_by('checkListId')
    confirmCheckList = ConfirmCheckList.objects.all()
    today = datetime.datetime.today()
    centers = Center.objects.filter(Q(centerStatus="Y"))

    # 등록된 센터 정보 있는지(ex.자수실, 비품실 등)
    if centers:
        # 등록된 점검 항목 목록이 있는지(ex. 소등상태, 냉난방기구 전원 등)
        if CheckList.objects.all():
            if request.method == 'POST':
                # 조회 기간
                searchDay = request.POST['searchDay']
                thisMonday = datetime.datetime(int(searchDay[:4]), int(searchDay[5:7]), int(searchDay[8:10]))
                thisSunday = thisMonday + datetime.timedelta(days=6)
                lastMonday = thisMonday - datetime.timedelta(days=7)
                nextMonday = thisMonday + datetime.timedelta(days=7)

                if request.user.is_staff:
                    employees = Employee.objects.filter(empStatus='Y')
                else:
                    # 담당한 센터가 있는지 확인
                    centermanager = CenterManagerEmp.objects.filter(Q(empId=request.user.employee.empId))
                    employees = Employee.objects.filter(empId=request.user.employee.empId)
                    centermanager = centermanager.filter(Q(centerManagerId__endDate__gte=thisMonday) & Q(centerManagerId__startDate__lte=thisSunday))
                    centers = centers.filter(centerId__in=centermanager.values_list('manageArea__centerId'))

                # 센터 정보
                centerName = request.POST['centerName']
                confirmCheckList = confirmCheckList.filter(centerId__centerName=centerName)
                confirmCheckList = confirmCheckList.filter(Q(confirmDate__gte=thisMonday) & Q(confirmDate__lte=thisSunday)).order_by('checkListId')

            else:
                # 조회 기간
                thisMonday = today - datetime.timedelta(days=today.weekday())
                thisSunday = thisMonday + datetime.timedelta(days=6)
                lastMonday = thisMonday - datetime.timedelta(days=7)
                nextMonday = thisMonday + datetime.timedelta(days=7)
                searchDay = thisMonday

                if request.user.is_staff:
                    employees = Employee.objects.filter(empStatus='Y')
                else:
                    # 담당한 센터가 있는지 확인
                    centermanager = CenterManagerEmp.objects.filter(Q(empId=request.user.employee.empId))
                    employees = Employee.objects.filter(empId=request.user.employee.empId)
                    centermanager = centermanager.filter(Q(centerManagerId__endDate__gte=thisMonday) & Q(centerManagerId__startDate__lte=thisSunday))
                    centers = centers.filter(centerId__in=centermanager.values_list('manageArea__centerId'))
                # 센터 정보
                centerName = centers.first().centerName
                confirmCheckList = confirmCheckList.filter(centerId__centerName=centerName)
                confirmCheckList = confirmCheckList.filter(Q(confirmDate__gte=thisMonday) & Q(confirmDate__lte=thisSunday)).order_by('checkListId')

            cheklistDict = {}
            for check in checklist:
                cheklistDict[check.checkListId] = ''
            dateList = []
            for day in range(0, 7):
                data = confirmCheckList.filter(confirmDate=(thisMonday + relativedelta(days=day))).order_by('checkListId')
                dateList.append({'empName': data.values('empId__empName').first(),
                                 'confirmDate': (thisMonday + relativedelta(days=day)),
                                 'data': data})
            context = {
                'today': today,
                'thisMonday': thisMonday,
                'thisSunday': thisSunday,
                'lastMonday': lastMonday.date,
                'nextMonday': nextMonday.date,
                'centers': centers,
                'employees': employees,
                'checklist': checklist,
                'confirmCheckList': confirmCheckList,
                'dateList': dateList,
                'centerName': centerName,
                'searchDay': searchDay,
                'checklists': checklist,
            }
            return HttpResponse(template.render(context, request))
        else:
            return HttpResponse('점검 항목이 없습니다. 점검항목을 등록해 주세요.')
    else:
        return redirect('daesungwork:showcenters')

@login_required
@csrf_exempt
def post_checklist(request):
    if request.POST:
        centerName = request.POST['modalCenterName']
        modalEmpName = request.POST['modalEmpName']
        modalCheckDate = request.POST['modalCheckDate']
        centerId = Center.objects.get(Q(centerName=centerName) & Q(centerStatus='Y'))
        empId = Employee.objects.get(empId=modalEmpName)

        if CenterManagerEmp.objects.filter(Q(empId=empId) & Q(manageArea=centerId.centerId) & Q(centerManagerId__startDate__lte=modalCheckDate) & Q(centerManagerId__endDate__gte=modalCheckDate)) or empId.user.is_staff:
            jsonCheckList = json.loads(request.POST['jsonCheckList'])
            ConfirmCheckList.objects.filter(Q(confirmDate=modalCheckDate) & Q(centerId__centerName=centerName)).delete()
            for item in jsonCheckList:
                if item['checkListBox']:
                    checkListStatus = 'Y'
                else:
                    checkListStatus = 'N'

                file = None
                if item['checkListFiles']:
                    fileName = item['checkListFiles'].split('\\')[-1]
                    for f in request.FILES.getlist('checkListFiles'):
                        if f.name == fileName:
                            file = f
                            break

                ConfirmCheckList.objects.create(
                    centerId=centerId,
                    empId=empId,
                    confirmDate=modalCheckDate,
                    checkListId=CheckList.objects.get(checkListName=item['checkListName']),
                    checkListStatus=checkListStatus,
                    comment=item['checkListComment'],
                    file=file,
                )
            return redirect('daesungwork:showchecklist')
        else:
            return HttpResponse('{}는(은) {}에 {}의 담당자가 아닙니다. 담당자배정정보를 확인 해주세요.'.format(empId.empName, modalCheckDate, centerName))

    else:
        return HttpResponse('점검 항목이 없습니다. 점검항목을 등록해 주세요.')


@login_required
@csrf_exempt
def view_checklist_pdf(request, month):
    todayYear = month[:4]
    todayMonth = month[5:]
    centers = Center.objects.filter(centerStatus="Y")
    checklists = CheckList.objects.filter(checkListStatus="Y").order_by('checkListId')
    table = []
    for center in centers:
        for checklist in checklists:
            rowDict = {'centerName': center.centerName, 'checkListId': checklist.checkListId, 'checkListName': checklist.checkListName}
            confirmCheckList = ConfirmCheckList.objects.filter(Q(centerId=center.centerId) & Q(checkListId=checklist.checkListId))
            dateTuple = calendar.monthrange(int(todayYear), int(todayMonth))
            dateDict = []
            for date in range(1, dateTuple[1]+1):
                try:
                    dateDict.append(confirmCheckList.get(confirmDate='{}-{}-{}'.format(todayYear, todayMonth, date)).checkListStatus)
                except:
                    dateDict.append('-')
            rowDict['dateDict'] = dateDict
            table.append(rowDict)

    context = {
        'todayYear': todayYear,
        'todayMonth': todayMonth,
        'checklists': checklists,
        'table': table,
        'days':  range(1, dateTuple[1]+1)
    }
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="{} 센터별 체크리스트.pdf"'.format(month)

    template = get_template('daesungwork/viewchecklistpdf.html')
    html = template.render(context, request)
    # create a pdf
    pisaStatus = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisaStatus.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@login_required
@csrf_exempt
def show_centers(request):
    template = loader.get_template('daesungwork/showcenters.html')
    if request.method == 'POST':
        centerName = request.POST['centerName']
        Center.objects.create(
            centerName=centerName.replace(" ", "")
        )
    centers = Center.objects.filter(centerStatus="Y")
    context = {
        "centers": centers,
    }
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def delete_center(request):
    if request.method == 'POST':
        try:
            centerId = request.POST.get('centerId', None)
            center = Center.objects.get(centerId=centerId)
            center.centerStatus = 'N'
            center.save()
            return redirect('daesungwork:showcenters')
        except Exception as e:
            print(e)
            return redirect('daesungwork:showcenters')
    else:
        print('else')
        return HttpResponse('오류발생! 관리자에게 문의하세요 :(')