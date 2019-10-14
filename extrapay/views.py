from django.shortcuts import render

from datetime import datetime, timedelta
import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template import loader
from service.models import Servicereport
from django.db.models import Q, F, Case, When, Value, CharField
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def over_hour(request):
    template = loader.get_template('extrapay/overhourlist.html')

    if request.method == "POST":
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        filter = 'Y'


    else:
        startdate = ''
        enddate = ''
        filter = 'N'

    context = {
        'filter': filter,
        'startdate': startdate,
        'enddate': enddate,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def over_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    overHour = Servicereport.objects.filter(Q(serviceOverHour__gt=0) & Q(serviceStatus='Y') & (Q(empDeptName='DB지원팀') | Q(empDeptName='솔루션지원팀')))
    if startdate:
        overHour = overHour.filter(Q(serviceDate__gte=startdate))
    if enddate:
        overHour = overHour.filter(Q(serviceDate__lte=enddate))

    overHourlist = overHour.values('serviceStartDatetime', 'serviceEndDatetime', 'empName', 'empDeptName', 'companyName', 'serviceOverHour', 'serviceId')
    structure = json.dumps(list(overHourlist), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')
