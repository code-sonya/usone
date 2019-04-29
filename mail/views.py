# -*- coding: utf-8 -*-
import os
import smtplib
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa

from client.models import Company, Customer
from hr.models import Employee
from service.functions import link_callback, num_to_str_position
from service.models import Servicereport
from .functions import servicereporthtml
from .mailInfo import smtp_server, port, userid, passwd


@login_required
@csrf_exempt
def selectreceiver(request, serviceId):
    template = loader.get_template('mail/selectreceiver.html')

    servicereport = Servicereport.objects.get(serviceId=serviceId)
    customers = Customer.objects.filter(Q(companyName=servicereport.companyName)&Q(customerStatus='Y'))
    deptmanager = Employee.objects.filter(Q(empManager="Y") &
                                          Q(empDeptName=request.user.employee.empDeptName))
    company = Company.objects.get(companyName=servicereport.companyName)
    sales = Employee.objects.get(empId=company.saleEmpId.empId)

    context = {
        'serviceId': serviceId,
        'servicereport': servicereport,
        'customers': customers,
        'sales': sales,
        'deptmanager': deptmanager,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def sendmail(request, serviceId):
    if request.method == 'POST':
        servicereport = Servicereport.objects.get(serviceId=serviceId)
        if servicereport.coWorker:
            coWorker = ''
            for coWorkerId in servicereport.coWorker.split(','):
                coWorker = coWorker + (str(Employee.objects.get(empId=coWorkerId).empName) +
                                       ' ' + num_to_str_position(Employee.objects.get(empId=coWorkerId).empPosition)) + ', '
            coWorker = coWorker[:-2]
        else:
            coWorker = ''
        emailList = request.POST["emailList"]
        emailList = emailList.split(',')
        empEmail = request.user.employee.empEmail

        # 메일 전송
        title = "[{}_{}]{} 유니원아이앤씨(주) SERVICE REPORT".format(servicereport.companyName, request.user.employee.empDeptName, servicereport.serviceDate)
        html = servicereporthtml(serviceId, coWorker)

        msg = MIMEMultipart("alternative")
        msg["From"] = empEmail
        msg["To"] = ",".join(emailList)
        msg["Subject"] = Header(s=title, charset="utf-8")
        msg.attach(MIMEText(html, "html", _charset="utf-8"))

        if servicereport.serviceSignPath:
            serviceSignPath = os.path.join(settings.MEDIA_ROOT, servicereport.serviceSignPath[7:])
            print(settings.MEDIA_ROOT)
            print(serviceSignPath)
        else:
            serviceSignPath = os.path.join(settings.MEDIA_ROOT, 'images/signature/nosign.jpg')

        # 서명 이미지
        with open(serviceSignPath, 'rb') as f:
            signatureimg = f.read()

        sign = MIMEImage(signatureimg)
        sign.add_header('Content-ID', '<sign>')
        msg.attach(sign)

        # pdf 첨부
        if servicereport.coWorker:
            coWorker = []
            for coWorkerId in servicereport.coWorker.split(','):
                coWorker.append(str(Employee.objects.get(empId=coWorkerId).empName) +
                                ' ' + num_to_str_position(Employee.objects.get(empId=coWorkerId).empPosition))
        else:
            coWorker = ''
        template_path = 'service/viewservicepdf.html'
        template = loader.get_template(template_path)
        context = {
            'service': servicereport,
            'coWorker': coWorker,
        }
        html = template.render(context, request)
        src = BytesIO(html.encode('utf-8'))
        dest = BytesIO()

        pdfStatus = pisa.pisaDocument(src, dest, encoding='utf-8', link_callback=link_callback)
        if not pdfStatus.err:
            pdf = dest.getvalue()
            pdffile = MIMEBase("application/pdf", "application/x-pdf")
            pdffile.set_payload(pdf)
            encoders.encode_base64(pdffile)
            pdffile.add_header("Content-Disposition", "attachment", filename=title + '.pdf')
            msg.attach(pdffile)

        smtp = smtplib.SMTP(smtp_server, port)
        smtp.login(userid, passwd)
        smtp.sendmail(empEmail, emailList, msg.as_string())
        smtp.close()

        return redirect('service:showservices')

    else:
        resp = "잘못된 접근 방식"
        return HttpResponse(resp)
