from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect, get_object_or_404
from dateutil.relativedelta import relativedelta
import datetime
from django.db.models import Q
from service.models import Servicereport, Vacation


def scheduler(request):
    template = loader.get_template('scheduler/scheduler.html')
    userId = request.user.id

    if userId :
        empId = request.user.employee.empId
        print("empId : ",empId)
        empName = request.user.employee.empName
        print("empName : ", empName)
        empDeptName = request.user.employee.empDeptName

        ### 일정 ###
        teamCalendar = Servicereport.objects.filter(Q(empDeptName=empDeptName)&Q(serviceStartDatetime__gte=datetime.date.today()-relativedelta(months=1))).exclude(empName=empName)
        myCalendar = Servicereport.objects.filter(empName=empName)

        ### 휴가 ###
        teamVacation = Vacation.objects.exclude(empId=empId)
        myVacation = Servicereport.objects.filter(empId=empId)
        print (str(datetime.date.today()))

        print("teamCalendar",teamCalendar ,"myCalendar",myCalendar , "teamVacation",teamVacation , "myVacation",myVacation )

        context = {
            'today': str(datetime.date.today()),
            'teamCalendar' : teamCalendar,
            'myCalendar' : myCalendar,
            'teamVacation' : teamVacation,
            'myVacation' : myVacation
        }
        return HttpResponse(template.render(context, request))
    else :
        return render(request, 'accounts/login.html')



