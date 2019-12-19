
import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.serializers.json import DjangoJSONEncoder

from .models import DownloadLog, OrderLog, ApprovalLog
from hr.models import Employee
from sales.models import Contract
import datetime

def insert_downloadlog(request):
    downloadUrl = request.POST['downloadUrl']
    downloadType = request.POST['downloadType']
    downloadName = downloadUrl.split('/')[-1]
    contractId = request.POST['contractId']

    DownloadLog.objects.create(
        empId=Employee(empId=request.user.employee.empId),
        contractId=Contract(contractId=contractId),
        downloadDatetime=datetime.datetime.now(),
        downloadType=downloadType,
        downloadName=downloadName,
        downloadUrl=downloadUrl,
    )
    structure = json.dumps(['Y'], cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def show_downloads(request):
    if request.method == "POST":
        empDeptName = request.POST["empDeptName"]
        empName = request.POST["empName"]
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']


    else:
        empDeptName = ''
        empName = ''
        startdate = ''
        enddate = ''

    context = {
        'empDeptName': empDeptName,
        'empName': empName,
        'startdate': startdate,
        'enddate': enddate,
    }
    return render(request, 'logs/showdownloads.html', context)


@login_required
@csrf_exempt
def download_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    empDeptName = request.POST['empDeptName']
    empName = request.POST['empName']

    downloads = DownloadLog.objects.all()
    if startdate:
        downloads = downloads.filter(downloadDatetime__gte=startdate)
    if enddate:
        downloads = downloads.filter(downloadDatetime__lte=enddate)
    if empDeptName:
        downloads = downloads.filter(empId__empDeptName__icontains=empDeptName)
    if empName:
        downloads = downloads.filter(empId__empName__icontains=empName)

    downloads = downloads.values('downloadDatetime', 'empId__empDeptName', 'empId__empName', 'downloadType', 'downloadName', 'downloadUrl', 'downloadLogId')
    structure = json.dumps(list(downloads), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def show_approvals(request):
    if request.method == "POST":
        empDeptName = request.POST["empDeptName"]
        empName = request.POST["empName"]
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']

    else:
        empDeptName = ''
        empName = ''
        startdate = ''
        enddate = ''

    context = {
        'empDeptName': empDeptName,
        'empName': empName,
        'startdate': startdate,
        'enddate': enddate,
    }
    return render(request, 'logs/showapprovals.html', context)


@login_required
@csrf_exempt
def approval_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    empDeptName = request.POST['empDeptName']
    empName = request.POST['empName']

    approvals = ApprovalLog.objects.all()
    if startdate:
        approvals = approvals.filter(approvalDatetime__gte=startdate)
    if enddate:
        approvals = approvals.filter(approvalDatetime__lte=enddate)
    if empDeptName:
        approvals = approvals.filter(empId__empDeptName__icontains=empDeptName)
    if empName:
        approvals = approvals.filter(empId__empName__icontains=empName)

    downloads = approvals.values('approvalDatetime', 'empId__empDeptName', 'empId__empName', 'documentId__title', 'documentId__documentId', 'approvalStatus', 'approvalLogId')
    structure = json.dumps(list(downloads), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')
