from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, QueryDict
from django.db.models import Q

from .forms import BoardForm
from .models import Board
from hr.models import Employee
from service.models import Servicereport

import datetime


def post_board(request, serviceId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        # 로그인 사용자 정보
        empId = Employee(empId=request.user.employee.empId)

        if request.method == 'POST':
            form = BoardForm(request.POST, request.FILES)
            post = form.save(commit=False)
            post.boardWriter = empId
            post.boardWriteDatetime = datetime.datetime.now()
            post.boardEditDatetime = datetime.datetime.now()
            post.save()
            if serviceId != '0':
                post.serviceId = Servicereport(serviceId=serviceId)

            return redirect('noticeboard:showboards')  # redirect는 show_board

        else:
            form = BoardForm()

            if serviceId == '0':
                service = ''
            else:
                service = Servicereport.objects.get(serviceId=serviceId)
                form.fields['boardTitle'].initial = '[' + str(service.companyName) + '] ' + str(service.serviceTitle)

            context = {
                'form': form,
                'service': service,
            }

            return render(request, 'noticeboard/postboard.html', context)


def show_boards(request):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        if request.method == "POST":
            startdate = request.POST['startdate']
            enddate= request.POST['enddate']
            empDeptName= request.POST['empDeptName']
            empName = request.POST['empName']
            companyName = request.POST['companyName']
            serviceType = request.POST['serviceType']
            boardTitle = request.POST['boardTitle']

            boards = Board.objects.all()
            if startdate:
                boards = boards.filter(boardWriteDatetime__gte=startdate)
            if enddate:
                boards = boards.filter(boardWriteDatetime__lte=enddate)
            if empDeptName:
                boards = boards.filter(boardWriter__empDeptName__icontains=empDeptName)
            if empName:
                boards = boards.filter(boardWriter__empName__icontains=empName)
            if companyName:
                boards = boards.filter(serviceId__companyName__companyName__icontains=companyName)
            if serviceType:
                boards = boards.filter(serviceId__serviceType__icontains=serviceType)
            if boardTitle:
                boards = boards.filter(Q(boardTitle__icontains=boardTitle) | Q(boardDetails__icontains=boardTitle))

            context = {
                'boards': boards,
            }
            return render(request, 'noticeboard/showboards.html', context)

        else:
            boards = Board.objects.all()

            context = {
                'boards': boards,
            }

            return render(request, 'noticeboard/showboards.html', context)