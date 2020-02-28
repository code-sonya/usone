# -*- coding: utf-8 -*-
import datetime
import json

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from hr.models import Employee
from service.models import Servicereport
from .forms import BoardForm
from .models import Board


@login_required
@csrf_exempt
def board_asjson(request):
    startdate = request.POST['startdate']
    enddate = request.POST['enddate']
    empDeptName = request.POST['empDeptName']
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

    boards = boards.values(
        'boardWriteDatetime', 'serviceId__serviceType__typeName', 'boardWriter__empName',
        'serviceId__companyName', 'boardTitle', 'boardDetails', 'boardId'
    )
    structure = json.dumps(list(boards), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_board(request, serviceId):
    instance = ''  # modify_board 와 구분하기 위한 변수
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


@login_required
def show_boards(request):
    if request.method == "POST":
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        empDeptName = request.POST['empDeptName']
        empName = request.POST['empName']
        companyName = request.POST['companyName']
        serviceType = request.POST['serviceType']
        boardTitle = request.POST['boardTitle']

        context = {
            'filter': 'Y',
            'startdate': startdate,
            'enddate': enddate,
            'empDeptName': empDeptName,
            'empName': empName,
            'companyName': companyName,
            'serviceType': serviceType,
            'boardTitle': boardTitle,

        }
        return render(request, 'noticeboard/showboards.html', context)

    else:
        context = {
            'filter': 'N',
        }
        return render(request, 'noticeboard/showboards.html', context)


@login_required
def view_board(request, boardId):
    board = Board.objects.get(boardId=boardId)
    filename = str(board.boardFiles).split('/')[-1]
    context = {
        'board': board,
        'filename': filename,
    }
    return render(request, 'noticeboard/viewboard.html', context)


@login_required
def delete_board(request, boardId):
    Board.objects.filter(boardId=boardId).delete()
    return redirect('noticeboard:showboards')


@login_required
def modify_board(request, boardId):
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
