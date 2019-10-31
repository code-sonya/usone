import json

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
from django.db.models import Sum, FloatField, F, Case, When, Count

from .models import Documentcategory, Documentform


@login_required
def post_document(request):
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
            comment=request.POST['comment'],
        )

    context = {}
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
