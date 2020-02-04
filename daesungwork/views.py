from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from hr.models import Employee
from .models import Center, CenterManager, CenterManagerEmp
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


# Create your views here.


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
                    cleanupArea=Center.objects.filter(centerName=item["cleanupArea"]).first(),
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
def center_asjson(request):
    centerManagerId = request.POST['centerManagerId']
    if centerManagerId:
        centers = Center.objects.all().values('centerName').order_by('centerName')
        employees = Employee.objects.filter(empStatus='Y').values('empName', 'empId').order_by('empId')
        centerManagerEmps = CenterManagerEmp.objects.filter(centerManagerId=centerManagerId).values('')
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
    centermanagers = CenterManager.objects.filter(centerManagerStatus='Y').values('centerManagerId', 'writeEmp__empName', 'startDate', 'endDate', 'createdDatetime').order_by('centerManagerId')
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