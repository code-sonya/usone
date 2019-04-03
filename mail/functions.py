from functools import lru_cache

import pandas as pd
from datetime import datetime, timedelta
import requests
from django.db.models import Q
from dateutil.relativedelta import relativedelta
from scheduler.models import Eventday
from service.models import Servicereport
from django.contrib.auth.models import User
from hr.models import Employee
import pdfkit

def html2pdf(url):
    options = {
        'margin-top': '5mm',
        'margin-right': '0mm',
        'margin-left': '2mm',
        'margin-bottom': '0mm',
        'page-width': '225mm',
        'page-height': '153mm',
        'encoding': "UTF-8",
        'no-outline': None,
    }
    #window: path_wkthmltopdf = u'/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'
    #mac:
    path_wkthmltopdf = '/usr/local/bin/wkhtmltopdf'
    #server:path_wkthmltopdf = '/usr/local/bin/wkhtmltopdf'

    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
    return pdfkit.from_url(url, False, options=options, configuration=config)


def servicereporthtml(serviceId):
    servicereport = Servicereport.objects.get(serviceId=serviceId)
    emp = Employee.objects.get(empId=servicereport.empId.empId)

    servicereport.empId

    html = """<html lang="ko">
            <head>  <title> UNIONEINC SERVICE REPORT</title></head>
            <body>
            <table style="width: 1000px; height: 600px; border-collapse: collapse; border: 2px solid black;table-layout:fixed; ">
            <tbody>
            <tr style="height: 75px; border: 2px solid black; ">
                <td style="width: 1000px; height: 75px; text-align: center;" colspan="10"><strong><font size="6">SERVICE REPORT</font></strong></td>
            </tr>
                <tr style="height: 25px; border: 1px solid black; ">
                <td style="width: 200px; height: 25px; border: 2px solid black; text-align: center;" colspan="2"><strong>고 객 사</strong></td>
                <td style="width: 200px; height: 25px; border: 2px solid black; text-align: center;" colspan="2"><strong>지 원 종 류</strong></td>
                <td style="width: 200px; height: 25px; border: 2px solid black; text-align: center;" colspan="2"><strong>개 시 일 시</strong></td>
                <td style="width: 200px; height: 25px; border: 2px solid black; text-align: center;" colspan="2"><strong>완 료 일 시</strong></td>
                <td style="width: 200px; height: 25px; border: 2px solid black; text-align: center;" colspan="2"><strong>소 요 시 간</strong></td>
            </tr>
            <tr style="height: 50px; border: 2px solid black; ">
                <td style="width: 200px; height: 50px; border: 2px solid black; text-align: center;" colspan="2"><strong><font size="4">""" + servicereport.companyName.companyName + """</font></strong> 귀중</td>
                <td style="width: 200px; height: 50px; border: 2px solid black; text-align: center;" colspan="2">""" + servicereport.serviceType + """</td>
                <td style="width: 200px; height: 50px; border: 2px solid black; text-align: center;" colspan="2"><font size="2.5">""" + str(servicereport.serviceStartDatetime) + """</font></td>
                <td style="width: 200px; height: 50px; border: 2px solid black; text-align: center;" colspan="2"><font size="2.5">""" + str(servicereport.serviceEndDatetime) + """</font></td>
                <td style="width: 200px; height: 50px; border: 2px solid black; text-align: center;" colspan="2">""" + str(servicereport.serviceHour) + """ 시간</td>



            </tr>
            <tr style="height: 370px; border: 2px solid black; ">
                <td style="width: 1000px; height: 370px;" colspan="10" valign="top">
                    <p>&nbsp;</P>&nbsp;&nbsp;<strong>지 원 내 용 :</strong><p><br><div style="padding-left: 40px">""" + servicereport.serviceDetails + """</div> &nbsp; &nbsp;&nbsp;&nbsp;&nbsp;</p>
                </td>
            </tr>

            <tr style="height: 20px; border: 2px solid black; ">
                <td style="width: 300px; height: 20px; border: 2px solid black; " colspan="3"><strong>&nbsp;&nbsp;지원담당부서 :</strong> """ + str(servicereport.empDeptName) + """</td>
                <td style="width: 300px; height: 20px; border: 2px solid black; " colspan="3"><strong>&nbsp;&nbsp;고객담당부서 :</strong> """ + str(servicereport.customerDeptName) + """</td>
                <td style="width: 100px; border: 2px solid black; text-align: center;" colspan="2" rowspan="4"><p>고객서명</p></td>
                <td style="width: 300px; border: 2px solid black; text-align: center;" colspan="2" rowspan="4">
                        <img src="cid:sign" height="85px">
                </td>

            </tr>
            <tr style="height: 20px; border: 2px solid black; ">
                <td style="width: 300px; height: 20px; border: 2px solid black; " colspan="3"><strong>&nbsp;&nbsp;성&nbsp;&nbsp;&nbsp;&nbsp;명 :</strong> """ + str(servicereport.empName) + """</td>
                <td style="width: 300px; height: 20px; border: 2px solid black; " colspan="3"><strong>&nbsp;&nbsp;성&nbsp;&nbsp;&nbsp;&nbsp;명 :</strong> """ + str(servicereport.customerName) + """</td>
            </tr>
            <tr style="height: 20px; border: 2px solid black; ">
                <td style="width: 300px; height: 20px; border: 2px solid black; " colspan="3"><strong>&nbsp;&nbsp;연&nbsp;락&nbsp;처 :</strong> """ + str(emp.empPhone) + """</td>
                <td style="width: 300px; height: 20px; border: 2px solid black; " colspan="3"><strong>&nbsp;&nbsp;연&nbsp;락&nbsp;처 :</strong> """ + str(servicereport.customerPhone) + """</td>
            </tr>
            <tr style="height: 20px; border: 2px solid black; ">
                <td style="width: 300px; height: 20px; border: 2px solid black; " colspan="3"><strong>&nbsp;&nbsp;이 메 일 :</strong>""" + str(emp.empEmail) + """</td>
                <td style="width: 300px; height: 20px; border: 2px solid black; " colspan="3"><strong>&nbsp;&nbsp;이 메 일 :</strong> """ + str(servicereport.customerEmail) + """</td>
            </tr>
            </tbody>
            </table>
            </body>
            </html>"""
    return html

