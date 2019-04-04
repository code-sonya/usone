from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.db.models import Q
from email.mime.image import MIMEImage
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
<<<<<<< HEAD
from .functions import servicereporthtml, html2pdf
import os
import pdfkit
import smtplib
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase

from service.models import Servicereport, Serviceform, Vacation
=======
from .functions import servicereporthtml
from service.models import Servicereport
>>>>>>> sonya
from client.models import Company, Customer
from hr.models import Employee
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

            ###메일 전송
            title = "[{}_{}]{} 유니원아이앤씨(주) SERVICE REPORT".format(servicereport.companyName, request.user.employee.empDeptName, servicereport.serviceDate)
            html = servicereporthtml(serviceId)
            subject, from_email = title, request.user.employee.empEmail
            text_content = strip_tags(html)

            #html 메일본문
            message = EmailMultiAlternatives(subject, text_content, from_email, emailList)
            message.attach_alternative(html, "text/html")

            #서명 이미지
            with open(servicereport.serviceSignPath, 'rb') as f:
                signatureimg = f.read()

            sign = MIMEImage(signatureimg)
            sign.add_header('Content-ID', '<sign>')
            message.attach(sign)

            #pdf file
            #로컬:
            base="127.0.0.1:8000"
            #서버: base="lop.unioneinc.co.kr:6203
            servicereportUrl = base+"/mail/servicereport/" + serviceId + "/"

            try:
                pdf = html2pdf(servicereportUrl)
                pdffile = MIMEBase("application/pdf", "application/x-pdf")
                pdffile.set_payload(pdf)
                encoders.encode_base64(pdffile)
                pdffile.add_header("Content-Disposition", "attachment", filename=title + '.pdf')
                message.attach(pdffile)
                message.send()
            except Exception as ex:
                print(ex)
                resp = "메일 전송 실패! 관리자에게 문의하세요:)"
                return HttpResponse(resp)



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
