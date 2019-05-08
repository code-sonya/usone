# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa

from hr.models import Employee
from .forms import OpportunityForm
from .models import Contract
from service.models import Company ,Customer


@login_required
def post_opportunity(request):
    empId = Employee(empId=request.user.employee.empId)

    if request.method == "POST":
        form = OpportunityForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('service:showservices')

    else:
        form = OpportunityForm()
        context = {
            'form': form,
        }
        return render(request, 'sales/postopportunity.html', context)


@login_required
@csrf_exempt
def salemanager_asjson(request):
    companyName = request.POST['saleCompanyName']
    #companyName="AXA손해보험"
    print(companyName)
    customer = Customer.objects.filter(companyName=companyName)
    json = serializers.serialize('json', customer)
    return HttpResponse(json, content_type='application/json')