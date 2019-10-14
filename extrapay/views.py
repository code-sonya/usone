from django.shortcuts import render

from datetime import datetime, timedelta
import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.template import loader
from service.models import Servicereport
from .models import OverHour
from django.db.models import Q, F, Case, When, Value, CharField
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def over_hour(request):
    template = loader.get_template('extrapay/overhourlist.html')

    if request.method == "POST":
        searchdate = request.POST['searchdate']
        filter = 'Y'


    else:
        searchdate = ''
        filter = 'N'

    context = {
        'filter': filter,
        'searchdate': searchdate,
    }

    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def over_asjson(request):
    searchdate = request.POST['searchdate']
    searchYear = searchdate[:4]
    searchMonth = searchdate[5:7]

    overHour = OverHour.objects.all()
    if searchdate:
        overHour = overHour.filter(Q(overHourDate__year=searchYear) & Q(overHourDate__month=searchMonth))

    overHourlist = overHour.values('overHourDate', 'empId__empDeptName', 'empName', 'sumOverHour', 'compensatedHour', 'payHour', 'overHourId')
    print(overHourlist)
    structure = json.dumps(list(overHourlist), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')
