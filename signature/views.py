from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
from service.models import Servicereport
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from client.models import Company, Customer

def signature(request, serviceId):
    template = loader.get_template('signature/sign-pad.html')
    userId = request.user.id
    servicereport = Servicereport.objects.get(serviceId=serviceId)

    if userId:
        if request.method == "POST":
            if request.POST["customer"] == "temp":
                servicereport.customerName = request.POST["customerName"]
                servicereport.customerDeptName = request.POST["customerDept"]
                servicereport.customerEmail = request.POST["customerEmail"]
                servicereport.customerPhone = request.POST["customerPhone"]
                servicereport.save()

            else:
                customerInfo =Customer.objects.get(customerEmail=request.POST["customer"])
                servicereport.customerName = customerInfo.customerName
                servicereport.customerDeptName = customerInfo.customerDeptName
                servicereport.customerEmail = customerInfo.customerEmail
                servicereport.customerPhone = customerInfo.customerPhone
                servicereport.save()

            context = {
                'serviceId': serviceId,
            }
            return HttpResponse(template.render(context, request))

        else:
            context = {
                'serviceId': serviceId,
            }
            return HttpResponse(template.render(context, request))

    else:
        return render(request, 'accounts/login.html')

def selectmanager(request, serviceId):
    template = loader.get_template('signature/selectmanager.html')
    userId = request.user.id

    if userId:
        servicereport = Servicereport.objects.get(serviceId=serviceId)
        servicereport.serviceStatus = 'Y'
        servicereport.save()
        customers = Customer.objects.filter(companyName=servicereport.companyName)
        context = {
            'serviceId': serviceId,
            'servicereport': servicereport,
            'customers': customers,
        }
        return HttpResponse(template.render(context, request))

    else:
        return render(request, 'accounts/login.html')


@csrf_exempt
def saveimg(request, serviceId):

    if request.method == 'POST':
        data = request.FILES.get('file')
        path = default_storage.save('images/signature/'+serviceId+'.jpg', ContentFile(data.read()))
        img_file = os.path.join(settings.MEDIA_ROOT, path)
        print(img_file)
        service = Servicereport.objects.get(serviceId=serviceId)
        service.serviceSignPath = img_file
        service.save()
        resp="이미지 저장"
        return HttpResponse(resp)
    else:
        resp = "잘못된 접근 방식"
        return HttpResponse(resp)
