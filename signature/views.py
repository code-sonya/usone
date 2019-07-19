from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from client.models import Customer
from service.models import Servicereport


@login_required
def signature(request, serviceId):
    template = loader.get_template('signature/sign-pad.html')
    servicereport = Servicereport.objects.get(serviceId=serviceId)

    if request.method == "POST":
        if request.POST["customer"] == "temp":
            servicereport.customerName = request.POST["customerName"]
            servicereport.customerDeptName = request.POST["customerDept"]
            servicereport.customerEmail = request.POST["customerEmail"]
            servicereport.customerPhone = request.POST["customerPhone"]
            servicereport.save()

        else:
            customerInfo = Customer.objects.get(customerId=request.POST["customer"])
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


@login_required
def selectmanager(request, serviceId):
    template = loader.get_template('signature/selectmanager.html')
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
