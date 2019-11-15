import json
import datetime

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
from django.db.models import Sum, FloatField, F, Case, When, Count, Q

from .models import Documentcategory, Documentform, Documentfile, Document


@login_required
def post_document(request):
    if request.method == 'POST':
        # 문서 종류 선택
        formId = Documentform.objects.get(
            categoryId__firstCategory=request.POST['firstCategory'],
            categoryId__secondCategory=request.POST['secondCategory'],
            formTitle=request.POST['formTitle'],
        )

        # 보존연한 숫자로 변환
        if request.POST['preservationYear'] == '영구':
            preservationYear = 9999
        else:
            preservationYear = request.POST['preservationYear'][:-1]

        # 문서번호 자동생성 (yymmdd-000)
        yymmdd = str(datetime.date.today()).replace('-', '')[2:]
        todayDocumentCount = len(Document.objects.filter(documentNumber__contains=yymmdd))
        documentNumber = yymmdd + '-' + str(todayDocumentCount+1).rjust(3, '0')

        # 문서 등록
        documentId = Document.objects.create(
            documentNumber=documentNumber,
            writeEmp=request.user.employee,
            formId=formId,
            preservationYear=preservationYear,
            securityLevel=request.POST['securityLevel'][0],
            title=request.POST['title'],
            contentHtml=request.POST['contentHtml'],
            writeDatetime=datetime.datetime.now(),
            modifyDatetime=datetime.datetime.now(),
            draftDatetime=datetime.datetime.now(),
            documentStatus=request.POST['documentStatus'],
        )

        # 첨부파일 처리
        # 1. 첨부파일 업로드 정보
        jsonFile = json.loads(request.POST['jsonFile'])
        filesInfo = {}   # {fileName1: fileSize1, fileName2: fileSize2, ...}
        filesName = []   # [fileName1, fileName2, ...]
        for i in jsonFile:
            filesInfo[i['fileName']] = i['fileSize']
            filesName.append(i['fileName'])
        # 2. 업로드 된 파일 중, 화면에서 삭제하지 않은 것만 등록
        for f in request.FILES.getlist('files'):
            if f.name in filesName:
                Documentfile.objects.create(
                    documentId=documentId,
                    file=f,
                    fileName=f.name,
                    fileSize=filesInfo[f.name][:-2],
                )

    context = {}
    return render(request, 'approval/postdocument.html', context)


@login_required
def show_documentform(request):
    context = {}
    return render(request, 'approval/showdocumentform.html', context)


@login_required
def showdocumentform_asjson(request):
    documentforms = Documentform.objects.all().annotate(
        firstCategory=F('categoryId__firstCategory'),
        secondCategory=F('categoryId__secondCategory'),
    ).values('formId', 'firstCategory', 'secondCategory', 'formTitle', 'comment')

    structure = json.dumps(list(documentforms), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_documentform(request):
    if request.method == 'POST':
        categoryId = Documentcategory.objects.get(
            firstCategory=request.POST['firstCategory'],
            secondCategory=request.POST['secondCategory'],
        )
        Documentform.objects.create(
            categoryId=categoryId,
            formTitle=request.POST['formTitle'],
            formHtml=request.POST['formHtml'],
            preservationYear=request.POST['preservationYear'],
            securityLevel=request.POST['securityLevel'],
            comment=request.POST['comment'],
        )
        return redirect('approval:showdocumentform')
    else:
        context = {}
        return render(request, 'approval/postdocumentform.html', context)


@login_required
def modify_documentform(request, formId):
    if request.method == 'POST':
        categoryId = Documentcategory.objects.get(
            firstCategory=request.POST['firstCategory'],
            secondCategory=request.POST['secondCategory'],
        )
        form = Documentform.objects.get(formId=formId)
        form.categoryId = categoryId
        form.formTitle = request.POST['formTitle']
        form.formHtml = request.POST['formHtml']
        form.preservationYear = request.POST['preservationYear']
        form.securityLevel = request.POST['securityLevel']
        form.comment = request.POST['comment']
        form.save()
        return redirect('approval:showdocumentform')
    else:
        form = Documentform.objects.get(formId=formId)
        context = {
            'form': form,
        }
        return render(request, 'approval/postdocumentform.html', context)


@login_required
def documentcategory_asjson(request):
    if request.method == 'GET':
        documentCategory = ''
        if request.GET['category'] == 'first':
            documentCategory = Documentcategory.objects.values(
                'firstCategory'
            ).distinct()
        elif request.GET['category'] == 'second':
            documentCategory = Documentcategory.objects.filter(
                firstCategory=request.GET['firstCategory']
            ).values(
                'secondCategory'
            ).distinct()
        structure = json.dumps(list(documentCategory), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
def documentform_asjson(request):
    if request.method == 'GET':
        if request.GET['type'] == 'formTitle':
            documentForm = Documentform.objects.filter(
                Q(categoryId__firstCategory=request.GET['firstCategory']) &
                Q(categoryId__secondCategory=request.GET['secondCategory'])
            ).values('formTitle')

            structure = json.dumps(list(documentForm), cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')
        elif request.GET['type'] == 'form':
            documentForm = Documentform.objects.filter(
                Q(categoryId__firstCategory=request.GET['firstCategory']) &
                Q(categoryId__secondCategory=request.GET['secondCategory']) &
                Q(formTitle=request.GET['formTitle'])
            ).values('preservationYear', 'securityLevel', 'formHtml')

            structure = json.dumps(list(documentForm), cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')


@login_required
def post_documentcategory(request):
    if request.method == 'POST':
        firstCategory = request.POST['firstCategoryAdd']
        secondCategory = request.POST['secondCategoryAdd']

        documentCategory = Documentcategory.objects.filter(
            firstCategory=firstCategory,
            secondCategory=secondCategory,
        )

        if documentCategory:
            message = '존재하는 분류입니다.\n확인 후 다시 등록해주세요.'
        else:
            Documentcategory.objects.create(
                firstCategory=firstCategory,
                secondCategory=secondCategory,
            )
            message = '등록이 완료되었습니다.'

        structure = json.dumps(message, cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')
