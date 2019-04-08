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
    instance = ''

    if userId:
        # 로그인 사용자 정보
        empId = Employee(empId=request.user.employee.empId)

        if request.method == 'POST':
            form = BoardForm(request.POST, request.FILES)
            post = form.save(commit=False)
            post.boardWriter = empId
            post.boardWriteDatetime = datetime.datetime.now()
            post.boardEditDatetime = datetime.datetime.now()
            if serviceId != '0':
                post.serviceId = Servicereport(serviceId=serviceId)
            post.save()

            return redirect('noticeboard:showboards')

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
                'instance': instance,
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


def view_board(request, boardId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        board = Board.objects.get(boardId=boardId)
        filename = str(board.boardFiles).split('/')[-1]

        context = {
            'board': board,
            'filename': filename,
        }

        return render(request, 'noticeboard/viewboard.html', context)


def delete_board(request, boardId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        Board.objects.filter(boardId=boardId).delete()

        return redirect('noticeboard:showboards')

    else:
        return HttpResponse("로그아웃 시 표시될 화면 또는 URL")


def modify_board(request, boardId):
    userId = request.user.id  # 로그인 유무 판단 변수

    if userId:
        instance = Board.objects.get(boardId=boardId)

        if request.method == 'POST':
            form = BoardForm(request.POST, request.FILES, instance=instance)
            post = form.save(commit=False)
            post.boardEditDatetime = datetime.datetime.now()
            post.save()

            return redirect('noticeboard:showboards')

        else:
            form = BoardForm(instance=instance)

            context = {
                'form': form,
                'instance': instance,
            }

            return render(request, 'noticeboard/postboard.html', context)
