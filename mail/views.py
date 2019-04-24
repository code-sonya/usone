# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
import smtplib
from io import BytesIO
from xhtml2pdf import pisa
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.header import Header
from email import encoders

from .functions import servicereporthtml
from service.functions import link_callback
from service.models import Servicereport
from client.models import Company, Customer
from hr.models import Employee
from .mailInfo import smtp_server, port, userid, passwd
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags


@login_required
@csrf_exempt
def selectreceiver(request, serviceId):
    userId = request.user.id  # 로그인 유무 판단 변수
    template = loader.get_template('mail/selectreceiver.html')

    if userId:
        servicereport = Servicereport.objects.get(serviceId=serviceId)
        customers = Customer.objects.filter(companyName=servicereport.companyName)
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
    else:

        return render(request, 'accounts/login.html')


def sendmail(request, serviceId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:

        if request.method == 'POST':
            servicereport = Servicereport.objects.get(serviceId=serviceId)
            emailList = request.POST["emailList"]
            emailList = emailList.split(',')
            empEmail = request.user.employee.empEmail

            ###메일 전송
            title = "[{}_{}]{} 유니원아이앤씨(주) SERVICE REPORT".format(servicereport.companyName, request.user.employee.empDeptName, servicereport.serviceDate)
            html = servicereporthtml(serviceId)

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
            
            # pdf생성
            template_path = 'service/viewservicepdf.html'
            template = loader.get_template(template_path)
            context = {'service': servicereport}
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

    else:
        return render(request, 'accounts/login.html')


def servicereport(request, serviceId):
    servicereport = Servicereport.objects.get(serviceId=serviceId)
    try:
        img = servicereport.serviceSignPath.split('/')
        img = "/media/images/signature/" + img[-1]
    except:
        img = '/media/images/nosign.jpg'

    context = {'servicereport': servicereport, "img": img}

    return render(request, 'mail/servicereport.html', context)

