from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from hr.models import Employee
from .models import CenterManager, CenterManagerEmp
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, FloatField, F, Case, When, Count, Q, Min, Max, Value, CharField

# Create your views here.


def manage_center(request):
    template = loader.get_template('daesungwork/managecenter.html')
    context = {}
    return HttpResponse(template.render(context, request))

def post_manager(request):
    template = loader.get_template('daesungwork/postmanager.html')
    empList = Employee.objects.filter(Q(empStatus='Y'))
    empNames = []
    for emp in empList:
        temp = {'id': emp.empId, 'value': emp.empName}
        empNames.append(temp)
    print(empNames)
    context = {
        'empNames': empNames
    }
    return HttpResponse(template.render(context, request))
