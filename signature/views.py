

from PIL import Image
# from datashape import json
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpRequest, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
import datetime
from service.models import Servicereport, Serviceform, Vacation
from client.models import Company, Customer
from hr.models import Employee
from scheduler.models import Eventday

def signature(request, serviceId):
    template = loader.get_template('signature/sign-pad.html')
    userId = request.user.id

    if userId:
        context = {
            'serviceId': serviceId,
        }
        return HttpResponse(template.render(context, request))
    else:
        return render(request, 'accounts/login.html')


import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

@csrf_exempt
def saveimg(request, serviceId):

    if request.method == 'POST':
        data = request.FILES.get('file')
        path = default_storage.save('images/signature/'+serviceId+'.jpg', ContentFile(data.read()))
        img_file = os.path.join(settings.MEDIA_ROOT, path)

        service = Servicereport.objects.get(pk=serviceId)
        service.SERVICE_REPORT = img_file
        service.save()
        resp="이미지 저장"
        return HttpResponse(resp)
    else:
        resp = "잘못된 접근 방식"
        return HttpResponse(resp)
