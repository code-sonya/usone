# import lxml.html
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.db.models import Q


from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from django.views.decorators.csrf import csrf_exempt
import os
import pdfkit
import smtplib
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase

from service.models import Servicereport, Serviceform, Vacation
from client.models import Company, Customer
from hr.models import Employee
from scheduler.models import Eventday


# Create your views here.

def selectreceiver(request, serviceId):
    userId = request.user.id  # 로그인 유무 판단 변수
    template = loader.get_template('mail/selectreceiver.html')

    if userId:
        print(request.user.employee.empDeptName)
        servicereport=Servicereport.objects.get(serviceId=serviceId)
        customers=Customer.objects.filter(companyName=servicereport.companyName)
        deptmanager=Employee.objects.filter(Q(empManager="Y") &
                                            Q(empDeptName=request.user.employee.empDeptName))
        company = Company.objects.get(companyName=servicereport.companyName)

        sales = Employee.objects.get(empId=company.saleEmpId.empId)

        context = {
            'serviceId': serviceId,
            'servicereport':servicereport,
            'customers':customers,
            'sales':sales,
            'deptmanager':deptmanager,
        }

        return HttpResponse(template.render(context, request))
    else:

        return render(request, 'accounts/login.html')