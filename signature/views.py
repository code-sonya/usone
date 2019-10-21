from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect

from client.models import Customer
from service.models import Servicereport


@login_required
def signature(request, serviceId):
    template = loader.get_template('signature/sign-pad.html')
    servicereport = Servicereport.objects.get(serviceId=serviceId)

    context = {
        'serviceId': serviceId,
    }
    return HttpResponse(template.render(context, request))


@login_required
def selectmanager(request, serviceId):
    template = loader.get_template('signature/selectmanager.html')
    service = Servicereport.objects.get(serviceId=serviceId)

    if request.method == 'POST':
        if request.POST["customer"] == "temp":
            service.customerName = request.POST["customerName"]
            service.customerDeptName = request.POST["customerDept"]
            service.customerEmail = request.POST["customerEmail"]
            service.customerPhone = request.POST["customerPhone"]
        else:
            customerInfo = Customer.objects.get(customerId=request.POST["customer"])
            service.customerName = customerInfo.customerName
            service.customerDeptName = customerInfo.customerDeptName
            service.customerEmail = customerInfo.customerEmail
            service.customerPhone = customerInfo.customerPhone
        service.save()
        return redirect('signature:signature', serviceId)
    else:
        customers = Customer.objects.filter(companyName=service.companyName)
        context = {
            'serviceId': serviceId,
            'customers': customers,
        }
        return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def saveimg(request, serviceId):
    if request.method == 'POST':
        data = request.FILES.get('file')
        default_storage.save('images/signature/' + serviceId + '.jpg', ContentFile(data.read()))
        service = Servicereport.objects.get(serviceId=serviceId)
        service.serviceSignPath = service.serviceSignPath = '/media/images/signature/' + serviceId + '.jpg'
        service.save()
        resp = "이미지 저장"
        return HttpResponse(resp)
    else:
        resp = "잘못된 접근 방식"
        return HttpResponse(resp)
