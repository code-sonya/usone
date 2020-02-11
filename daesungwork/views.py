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
            for item in jsonManagerEmp:
                CenterManagerEmp.objects.create(
                    centerManagerId=post,
                    empId=Employee.objects.get(empId=item["empId"]),
                    manageArea=Center.objects.get(centerName=item["manageArea"]),
                    additionalArea=item["additionalArea"],
                    cleanupArea=Center.objects.get(centerName=item["cleanupArea"]),
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
                        manageArea=Center.objects.get(centerName=item["manageArea"]),
                        additionalArea=item["additionalArea"],
                        cleanupArea=Center.objects.filter(centerName=item["cleanupArea"]).first(),
                    )
                else:
                    managerEmpInstance = CenterManagerEmp.objects.get(managerId=int(item['centerManagerEmpId']))
                    managerEmpInstance.centerManagerId = post
                    managerEmpInstance.empId = Employee.objects.get(empId=item["empId"])
                    managerEmpInstance.manageArea = Center.objects.get(centerName=item["manageArea"])
                    managerEmpInstance.additionalArea = item["additionalArea"]
                    managerEmpInstance.cleanupArea = Center.objects.filter(centerName=item["cleanupArea"]).first()
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
        centers = Center.objects.all().values('centerName').order_by('centerName')
        employees = Employee.objects.filter(empStatus='Y').values('empName', 'empId').order_by('empId')
        centerManagerEmps = CenterManagerEmp.objects.filter(centerManagerId=centerManagerId)\
            .values('empId', 'empId__empName', 'manageArea__centerName', 'additionalArea', 'cleanupArea__centerName')
        jsonList = []
        jsonList.append(list(centers))
        jsonList.append(list(employees))
        jsonList.append(list(centerManagerEmps))

    else:
        centers = Center.objects.all().values('centerName').order_by('centerName')
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
    centers = Center.objects.filter(centerStatus="Y")
    employees = Employee.objects.filter(empStatus="Y")
    checklist = CheckList.objects.filter(checkListStatus="Y").order_by('checkListId')
    confirmCheckList = ConfirmCheckList.objects.all()
    today = datetime.datetime.today()
    if CheckList.objects.all():
        if request.method == 'POST':
            centerName = request.POST['centerName']
            searchDay = request.POST['searchDay']
            confirmCheckList = confirmCheckList.filter(centerId__centerName=centerName)
            thisMonday = datetime.datetime(int(searchDay[:4]), int(searchDay[5:7]), int(searchDay[8:10]))
            thisSunday = thisMonday + datetime.timedelta(days=6)
            lastMonday = thisMonday - datetime.timedelta(days=7)
            nextMonday = thisMonday + datetime.timedelta(days=7)
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
        else:
            centerName = centers.first().centerName
            confirmCheckList = confirmCheckList.filter(centerId__centerName=centerName)
            thisMonday = today - datetime.timedelta(days=today.weekday())
            thisSunday = thisMonday + datetime.timedelta(days=6)
            lastMonday = thisMonday - datetime.timedelta(days=7)
            nextMonday = thisMonday + datetime.timedelta(days=7)
            searchDay = thisMonday
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


@login_required
@csrf_exempt
def post_checklist(request):
    if request.POST:
        centerName = request.POST['modalCenterName']
        modalEmpName = request.POST['modalEmpName']
        modalCheckDate = request.POST['modalCheckDate']
        centerId = Center.objects.get(centerName=centerName)
        empId = Employee.objects.get(empId=modalEmpName)

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