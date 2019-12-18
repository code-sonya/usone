from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .models import DownloadLog, OrderLog, ApprovalLog
from hr.models import Employee
import datetime

def insert_downloadlog(request):
    downloadType = request.POST['downloadType']
    downloadUrl = request.POST['downloadUrl']
    contractId = request.POST['contractId']
    DownloadLog.objects.create(
        empId=Employee(empId=request.user.employee.empId),
        contractId=contractId,
        downloadDatetime=datetime.datetime.now(),
        downloadType=downloadType,
        downloadUrl=downloadUrl,
    )
    return HttpResponse({'result':'Y'}, content_type='application/json')