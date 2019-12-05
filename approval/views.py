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
from django.db.models import Sum, FloatField, F, Case, When, Count, Q, Min, Max

from service.models import Employee
from sales.models import Contract, Revenue, Purchase, Contractfile
from .models import Documentcategory, Documentform, Documentfile, Document, Approvalform, Relateddocument, Approval
from .functions import data_format, who_approval, template_format, mail_approval


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
        documentNumber = yymmdd + '-' + str(todayDocumentCount + 1).rjust(3, '0')

        # 문서 전처리 (\n 없애고, '를 "로 변경)
        HTML = request.POST['contentHtml']
        HTML = HTML.replace('\'', '"')
        HTML = HTML.replace('\r', '')
        HTML = HTML.replace('\n', '')

        # 문서 등록
        document = Document.objects.create(
            documentNumber=documentNumber,
            writeEmp=request.user.employee,
            formId=formId,
            preservationYear=preservationYear,
            securityLevel=request.POST['securityLevel'][0],
            title=request.POST['title'],
            contentHtml=HTML,
            writeDatetime=datetime.datetime.now(),
            modifyDatetime=datetime.datetime.now(),
            documentStatus=request.POST['documentStatus'],
        )

        if request.POST['documentStatus'] == '진행':
            document.draftDatetime = datetime.datetime.now()
            document.save()

        # 기안 할 경우에만 첨부파일 및 관련문서 저장 (임시 저장 시 첨부파일 및 관련문서 저장하지 않음)
        if request.POST['documentStatus'] == '진행':
            # 첨부파일 처리
            # 1. 첨부파일 업로드 정보
            jsonFile = json.loads(request.POST['jsonFile'])
            filesInfo = {}  # {fileName1: fileSize1, fileName2: fileSize2, ...}
            filesName = []  # [fileName1, fileName2, ...]
            for i in jsonFile:
                filesInfo[i['fileName']] = i['fileSize']
                filesName.append(i['fileName'])
            # 2. 업로드 된 파일 중, 화면에서 삭제하지 않은 것만 등록
            for f in request.FILES.getlist('files'):
                if f.name in filesName:
                    Documentfile.objects.create(
                        documentId=document,
                        file=f,
                        fileName=f.name,
                        fileSize=filesInfo[f.name][:-2],
                    )

            # 관련문서 처리
            jsonId = json.loads(request.POST['relatedDocumentId'])
            for relatedId in jsonId:
                relatedDocument = Document.objects.get(documentId=relatedId)
                Relateddocument.objects.create(
                    documentId=document,
                    relatedDocumentId=relatedDocument,
                )

        # 결재선 처리
        approval = []
        if request.POST['approvalFormat'] == '신청':
            if request.POST['apply']:
                applyList = request.POST['apply'].split(',')
                for i, a in enumerate(applyList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '신청'})
            if request.POST['process']:
                processList = request.POST['process'].split(',')
                for i, p in enumerate(processList):
                    if p != '':
                        approval.append({'approvalEmp': p, 'approvalStep': i + 1, 'approvalCategory': '승인'})
            if request.POST['reference']:
                referenceList = request.POST['reference'].split(',')
                for i, r in enumerate(referenceList):
                    if r != '':
                        approval.append({'approvalEmp': r, 'approvalStep': i + 1, 'approvalCategory': '참조'})
        elif request.POST['approvalFormat'] == '결재':
            if request.POST['approval'].split(','):
                approvalList = request.POST['approval'].split(',')
                for i, a in enumerate(approvalList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '결재'})
            if request.POST['agreement'].split(','):
                agreementList = request.POST['agreement'].split(',')
                for i, a in enumerate(agreementList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '합의'})
            if request.POST['financial'].split(','):
                financialList = request.POST['financial'].split(',')
                for i, f in enumerate(financialList):
                    if f != '':
                        approval.append({'approvalEmp': f, 'approvalStep': i + 1, 'approvalCategory': '재무합의'})
            if request.POST['reference2'].split(','):
                referenceList = request.POST['reference2'].split(',')
                for i, r in enumerate(referenceList):
                    if r != '':
                        approval.append({'approvalEmp': r, 'approvalStep': i + 1, 'approvalCategory': '참조'})

        for a in approval:
            empId = Employee.objects.get(empId=a['approvalEmp'])
            # 기안자는 자동 결재
            if request.POST['documentStatus'] == '진행' and empId.user == request.user:
                Approval.objects.create(
                    documentId=document,
                    approvalEmp=empId,
                    approvalStep=a['approvalStep'],
                    approvalCategory=a['approvalCategory'],
                    approvalStatus='완료',
                    approvalDatetime=datetime.datetime.now(),
                )
            else:
                Approval.objects.create(
                    documentId=document,
                    approvalEmp=empId,
                    approvalStep=a['approvalStep'],
                    approvalCategory=a['approvalCategory'],
                )

        whoApproval = who_approval(document.documentId)
        if len(whoApproval['do']) == 0:
            document.documentStatus = '완료'
            document.save()
            return redirect("approval:showdocumentendall")
        else:
            for empId in whoApproval['do']:
                employee = Employee.objects.get(empId=empId)
                mail_approval(employee, document)

        if request.POST['documentStatus'] == '임시':
            return redirect("approval:showdocumenttemp")
        else:
            return redirect("approval:showdocumentingdone")

    else:
        # 참조자 자동완성
        empList = Employee.objects.filter(Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {
                'id': emp.empId,
                'name': emp.empName,
                'position': emp.empPosition.positionName,
                'dept': emp.empDeptName,
            }
            empNames.append(temp)
        context = {
            'empNames': empNames
        }
        return render(request, 'approval/postdocument.html', context)


@login_required
def modify_document(request, documentId):
    if request.method == 'POST':
        # 임시저장 문서
        document = Document.objects.get(documentId=documentId)

        # 문서 종류 선택
        document.formId = Documentform.objects.get(
            categoryId__firstCategory=request.POST['firstCategory'],
            categoryId__secondCategory=request.POST['secondCategory'],
            formTitle=request.POST['formTitle'],
        )

        # 보존연한 숫자로 변환
        if request.POST['preservationYear'] == '영구':
            document.preservationYear = 9999
        else:
            document.preservationYear = request.POST['preservationYear'][:-1]

        # 문서번호 자동생성 (yymmdd-000)
        yymmdd = str(datetime.date.today()).replace('-', '')[2:]
        todayDocumentCount = len(Document.objects.filter(documentNumber__contains=yymmdd))
        document.documentNumber = yymmdd + '-' + str(todayDocumentCount + 1).rjust(3, '0')

        document.securityLevel = request.POST['securityLevel'][0]
        document.title = request.POST['title']
        # 문서 전처리 (\n 없애고, '를 "로 변경)
        HTML = request.POST['contentHtml']
        HTML = HTML.replace('\'', '"')
        HTML = HTML.replace('\r', '')
        HTML = HTML.replace('\n', '')
        document.contentHtml = request.POST['contentHtml']
        document.modifyDatetime = datetime.datetime.now()
        document.documentStatus = request.POST['documentStatus']

        if request.POST['documentStatus'] == '진행':
            document.draftDatetime = datetime.datetime.now()

        document.save()

        # 기안 할 경우에만 첨부파일 및 관련문서 저장 (임시 저장 시 첨부파일 및 관련문서 저장하지 않음)
        if request.POST['documentStatus'] == '진행':
            # 첨부파일 처리
            # 1. 첨부파일 업로드 정보
            jsonFile = json.loads(request.POST['jsonFile'])
            filesInfo = {}  # {fileName1: fileSize1, fileName2: fileSize2, ...}
            filesName = []  # [fileName1, fileName2, ...]
            for i in jsonFile:
                filesInfo[i['fileName']] = i['fileSize']
                filesName.append(i['fileName'])
            # 2. 업로드 된 파일 중, 화면에서 삭제하지 않은 것만 등록
            for f in request.FILES.getlist('files'):
                if f.name in filesName:
                    Documentfile.objects.create(
                        documentId=document,
                        file=f,
                        fileName=f.name,
                        fileSize=filesInfo[f.name][:-2],
                    )

            # 관련문서 처리
            jsonId = json.loads(request.POST['relatedDocumentId'])
            for relatedId in jsonId:
                relatedDocument = Document.objects.get(documentId=relatedId)
                Relateddocument.objects.create(
                    documentId=document,
                    relatedDocumentId=relatedDocument,
                )

        # 결재선 처리 (기존 결재 삭제 후 처리)
        Approval.objects.filter(documentId=document).delete()
        approval = []
        if request.POST['approvalFormat'] == '신청':
            if request.POST['apply']:
                applyList = request.POST['apply'].split(',')
                for i, a in enumerate(applyList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '신청'})
            if request.POST['process']:
                processList = request.POST['process'].split(',')
                for i, p in enumerate(processList):
                    if p != '':
                        approval.append({'approvalEmp': p, 'approvalStep': i + 1, 'approvalCategory': '승인'})
            if request.POST['reference']:
                referenceList = request.POST['reference'].split(',')
                for i, r in enumerate(referenceList):
                    if r != '':
                        approval.append({'approvalEmp': r, 'approvalStep': i + 1, 'approvalCategory': '참조'})
        elif request.POST['approvalFormat'] == '결재':
            if request.POST['approval'].split(','):
                approvalList = request.POST['approval'].split(',')
                for i, a in enumerate(approvalList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '결재'})
            if request.POST['agreement'].split(','):
                agreementList = request.POST['agreement'].split(',')
                for i, a in enumerate(agreementList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '합의'})
            if request.POST['financial'].split(','):
                financialList = request.POST['financial'].split(',')
                for i, f in enumerate(financialList):
                    if f != '':
                        approval.append({'approvalEmp': f, 'approvalStep': i + 1, 'approvalCategory': '재무합의'})
            if request.POST['reference2'].split(','):
                referenceList = request.POST['reference2'].split(',')
                for i, r in enumerate(referenceList):
                    if r != '':
                        approval.append({'approvalEmp': r, 'approvalStep': i + 1, 'approvalCategory': '참조'})

        for a in approval:
            empId = Employee.objects.get(empId=a['approvalEmp'])
            # 기안자는 자동 결재
            if request.POST['documentStatus'] == '진행' and empId.user == request.user:
                Approval.objects.create(
                    documentId=document,
                    approvalEmp=empId,
                    approvalStep=a['approvalStep'],
                    approvalCategory=a['approvalCategory'],
                    approvalStatus='완료',
                    approvalDatetime=datetime.datetime.now(),
                )
            else:
                Approval.objects.create(
                    documentId=document,
                    approvalEmp=empId,
                    approvalStep=a['approvalStep'],
                    approvalCategory=a['approvalCategory'],
                )
        if request.POST['documentStatus'] == '임시':
            return redirect("approval:showdocumenttemp")
        else:
            return redirect("approval:showdocumentingdone")

    else:
        # 임시저장 문서
        document = Document.objects.get(documentId=documentId)

        # 참조자 자동완성
        empList = Employee.objects.filter(Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {
                'id': emp.empId,
                'name': emp.empName,
                'position': emp.empPosition.positionName,
                'dept': emp.empDeptName,
            }
            empNames.append(temp)
        context = {
            'document': document,
            'empNames': empNames,
        }
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
    ).values(
        'formId', 'formNumber', 'firstCategory', 'secondCategory', 'formTitle', 'comment'
    ).order_by(
        'categoryId__firstCategory', 'formNumber'
    )

    structure = json.dumps(list(documentforms), cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def post_documentform(request):
    if request.method == 'POST':
        categoryId = Documentcategory.objects.get(
            firstCategory=request.POST['firstCategory'],
            secondCategory=request.POST['secondCategory'],
        )

        # 문서 전처리 (\n 없애고, '를 "로 변경)
        HTML = request.POST['formHtml']
        HTML = HTML.replace('\'', '"')
        HTML = HTML.replace('\r', '')
        HTML = HTML.replace('\n', '')

        documentformId = Documentform.objects.create(
            categoryId=categoryId,
            approvalFormat=request.POST['approvalFormat'],
            formNumber=request.POST['formNumber'],
            formTitle=request.POST['formTitle'],
            formHtml=HTML,
            preservationYear=request.POST['preservationYear'],
            securityLevel=request.POST['securityLevel'],
            comment=request.POST['comment'],
        )
        approval = []
        if request.POST['approvalFormat'] == '신청':
            if request.POST['apply']:
                applyList = request.POST['apply'].split(',')
                for i, a in enumerate(applyList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '신청'})
            if request.POST['process']:
                processList = request.POST['process'].split(',')
                for i, p in enumerate(processList):
                    if p != '':
                        approval.append({'approvalEmp': p, 'approvalStep': i + 1, 'approvalCategory': '승인'})
            if request.POST['reference']:
                referenceList = request.POST['reference'].split(',')
                for i, r in enumerate(referenceList):
                    if r != '':
                        approval.append({'approvalEmp': r, 'approvalStep': i + 1, 'approvalCategory': '참조'})
        elif request.POST['approvalFormat'] == '결재':
            if request.POST['approval'].split(','):
                approvalList = request.POST['approval'].split(',')
                for i, a in enumerate(approvalList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '결재'})
            if request.POST['agreement'].split(','):
                agreementList = request.POST['agreement'].split(',')
                for i, a in enumerate(agreementList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '합의'})
            if request.POST['financial'].split(','):
                financialList = request.POST['financial'].split(',')
                for i, f in enumerate(financialList):
                    if f != '':
                        approval.append({'approvalEmp': f, 'approvalStep': i + 1, 'approvalCategory': '재무합의'})
            if request.POST['reference2'].split(','):
                referenceList = request.POST['reference2'].split(',')
                for i, r in enumerate(referenceList):
                    if r != '':
                        approval.append({'approvalEmp': r, 'approvalStep': i + 1, 'approvalCategory': '참조'})

        if len(approval) != 0:
            for a in approval:
                empId = Employee.objects.get(empId=a['approvalEmp'])
                Approvalform.objects.create(
                    formId=documentformId,
                    approvalEmp=empId,
                    approvalStep=a['approvalStep'],
                    approvalCategory=a['approvalCategory'],
                )
        return redirect('approval:showdocumentform')
    else:
        # 결재자 자동완성
        empList = Employee.objects.filter(Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {
                'id': emp.empId,
                'name': emp.empName,
                'position': emp.empPosition.positionName,
                'dept': emp.empDeptName,
            }
            empNames.append(temp)

        context = {
            'empNames': empNames
        }
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
        form.formNumber = request.POST['formNumber']
        form.approvalFormat = request.POST['approvalFormat']
        form.formTitle = request.POST['formTitle']
        # 문서 전처리 (\n 없애고, '를 "로 변경)
        HTML = request.POST['formHtml']
        HTML = HTML.replace('\'', '"')
        HTML = HTML.replace('\r', '')
        HTML = HTML.replace('\n', '')
        form.formHtml = HTML
        form.preservationYear = request.POST['preservationYear']
        form.securityLevel = request.POST['securityLevel']
        form.comment = request.POST['comment']
        form.save()

        Approvalform.objects.filter(formId=formId).delete()
        approval = []
        if request.POST['approvalFormat'] == '신청':
            if request.POST['apply']:
                applyList = request.POST['apply'].split(',')
                for i, a in enumerate(applyList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '신청'})
            if request.POST['process']:
                processList = request.POST['process'].split(',')
                for i, p in enumerate(processList):
                    if p != '':
                        approval.append({'approvalEmp': p, 'approvalStep': i + 1, 'approvalCategory': '승인'})
            if request.POST['reference']:
                referenceList = request.POST['reference'].split(',')
                for i, r in enumerate(referenceList):
                    if r != '':
                        approval.append({'approvalEmp': r, 'approvalStep': i + 1, 'approvalCategory': '참조'})
        elif request.POST['approvalFormat'] == '결재':
            if request.POST['approval'].split(','):
                approvalList = request.POST['approval'].split(',')
                for i, a in enumerate(approvalList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '결재'})
            if request.POST['agreement'].split(','):
                agreementList = request.POST['agreement'].split(',')
                for i, a in enumerate(agreementList):
                    if a != '':
                        approval.append({'approvalEmp': a, 'approvalStep': i + 1, 'approvalCategory': '합의'})
            if request.POST['financial'].split(','):
                financialList = request.POST['financial'].split(',')
                for i, f in enumerate(financialList):
                    if f != '':
                        approval.append({'approvalEmp': f, 'approvalStep': i + 1, 'approvalCategory': '재무합의'})
            if request.POST['reference2'].split(','):
                referenceList = request.POST['reference2'].split(',')
                for i, r in enumerate(referenceList):
                    if r != '':
                        approval.append({'approvalEmp': r, 'approvalStep': i + 1, 'approvalCategory': '참조'})

        if len(approval) != 0:
            for a in approval:
                empId = Employee.objects.get(empId=a['approvalEmp'])
                Approvalform.objects.create(
                    formId=form,
                    approvalEmp=empId,
                    approvalStep=a['approvalStep'],
                    approvalCategory=a['approvalCategory'],
                )

        return redirect('approval:showdocumentform')
    else:
        form = Documentform.objects.get(formId=formId)
        apply, process, reference, approval, agreement, financial = data_format(formId, request.user, form.approvalFormat, 'N', 'approvalform')

        # 결재자 자동완성
        empList = Employee.objects.filter(Q(empStatus='Y'))
        empNames = []
        for emp in empList:
            temp = {
                'id': emp.empId,
                'name': emp.empName,
                'position': emp.empPosition.positionName,
                'dept': emp.empDeptName,
            }
            empNames.append(temp)

        context = {
            'form': form,
            'empNames': empNames,
            'apply': apply,
            'process': process,
            'reference': reference,
            'approval': approval,
            'agreement': agreement,
            'financial': financial,
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
            ).values(
                'formNumber', 'formTitle', 'approvalFormat'
            )
            structure = json.dumps(list(documentForm), cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')

        elif request.GET['type'] == 'form':
            documentForm = Documentform.objects.filter(
                Q(categoryId__firstCategory=request.GET['firstCategory']) &
                Q(categoryId__secondCategory=request.GET['secondCategory']) &
                Q(formTitle=request.GET['formTitle'])
            ).annotate(
                html=F('formHtml')
            ).values(
                'preservationYear', 'securityLevel', 'html', 'approvalFormat', 'formId'
            )
            apply, process, reference, approval, agreement, financial = data_format(
                documentForm.first()['formId'],
                request.user,
                documentForm.first()['approvalFormat'],
                'Y',
                'approvalform'
            )
            approvalList = {
                "apply": apply or None,
                "process": process or None,
                "reference": reference or None,
                "approval": approval or None,
                "agreement": agreement or None,
                "financial": financial or None
            }
            structureList = list(documentForm)
            structureList.append(approvalList)
            structure = json.dumps(structureList, cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')

        elif request.GET['type'] == 'temp':
            document = Document.objects.filter(
                documentId=request.GET['documentId']
            ).annotate(
                approvalFormat=F('formId__approvalFormat'),
                html=F('contentHtml'),
            ).values(
                'preservationYear', 'securityLevel', 'html', 'approvalFormat', 'title', 'documentId',
            )
            apply, process, reference, approval, agreement, financial = data_format(
                document.first()['documentId'],
                request.user,
                document.first()['approvalFormat'],
                'N',
                'approval'
            )
            approvalList = {
                "apply": apply or None,
                "process": process or None,
                "reference": reference or None,
                "approval": approval or None,
                "agreement": agreement or None,
                "financial": financial or None
            }
            structureList = list(document)
            structureList.append(approvalList)
            structure = json.dumps(structureList, cls=DjangoJSONEncoder)
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


@login_required
def showdocument_asjson(request):
    empId = request.user.employee.empId
    if request.method == 'GET':
        documentStatus = request.GET['documentStatus']
        category = request.GET['category']

        documentsId = []
        documents = Document.objects.filter(documentStatus=documentStatus)

        if documentStatus == '진행':
            tempDocumentsId = []
            for document in documents:
                approvalEmpId = [
                    i['approvalEmp__empId'] for i in Approval.objects.filter(
                        documentId__documentId=document.documentId
                    ).values(
                        'approvalEmp__empId'
                    )
                ]
                if empId in approvalEmpId:
                    tempDocumentsId.append(document.documentId)
            if category == '전체':
                documentsId = tempDocumentsId
            elif category == '진행':
                for documentId in tempDocumentsId:
                    if empId in who_approval(documentId)['done']:
                        documentsId.append(documentId)
            elif category == '대기':
                for documentId in tempDocumentsId:
                    if empId in who_approval(documentId)['do']:
                        documentsId.append(documentId)
            elif category == '확인':
                for documentId in tempDocumentsId:
                    if empId in who_approval(documentId)['check']:
                        documentsId.append(documentId)
            elif category == '예정':
                for documentId in tempDocumentsId:
                    if empId in who_approval(documentId)['will']:
                        documentsId.append(documentId)

        elif documentStatus == '완료':
            tempDocumentsId = []
            for document in documents:
                preservationDate = datetime.date(
                    year=min(document.writeDatetime.year + document.preservationYear, 9999),
                    month=document.writeDatetime.month,
                    day=document.writeDatetime.day,
                )
                # 보존연한체크 (문서 기안일 + 보존연한 > today)
                if preservationDate > datetime.date.today():
                    # 보안등급체크 (C: 전체 조회)
                    if document.securityLevel == 'C':
                        tempDocumentsId.append(document.documentId)
                    # 보안등급체크 (B: 본인과 임원 조회)
                    elif document.securityLevel == 'B':
                        if request.user.employee.empPosition.positionName == '임원':
                            tempDocumentsId.append(document.documentId)
                        else:
                            approvalEmpId = [
                                i['approvalEmp__empId'] for i in Approval.objects.filter(
                                    documentId__documentId=document.documentId
                                ).values(
                                    'approvalEmp__empId'
                                )
                            ]
                            if empId in approvalEmpId:
                                tempDocumentsId.append(document.documentId)
                    # 보안등급체크 (A: 본인과 대표이사 조회)
                    elif document.securityLevel == 'A':
                        if request.user.employee.empId <= 2:
                            tempDocumentsId.append(document.documentId)
                        else:
                            approvalEmpId = [
                                i['approvalEmp__empId'] for i in Approval.objects.filter(
                                    documentId__documentId=document.documentId
                                ).values(
                                    'approvalEmp__empId'
                                )
                            ]
                            if empId in approvalEmpId:
                                tempDocumentsId.append(document.documentId)
                    # 보안등급체크 (S: 본인만 조회)
                    elif document.securityLevel == 'S':
                        approvalEmpId = [
                            i['approvalEmp__empId'] for i in Approval.objects.filter(
                                documentId__documentId=document.documentId
                            ).values(
                                'approvalEmp__empId'
                            )
                        ]
                        if empId in approvalEmpId:
                            tempDocumentsId.append(document.documentId)
            if category == '전체':
                documentsId = tempDocumentsId

            # 내가 기안자 인 경우
            elif category == '기안':
                for documentId in tempDocumentsId:
                    if empId == Document.objects.get(documentId=documentId).writeEmp.empId:
                        documentsId.append(documentId)

            # 내가 기안자가 아니고, 참조자도 아닌 경우
            elif category == '결재':
                for documentId in tempDocumentsId:
                    checkEmpId = [
                        i['approvalEmp__empId'] for i in Approval.objects.filter(
                            documentId__documentId=documentId,
                            approvalCategory='참조',
                        ).values(
                            'approvalEmp__empId'
                        )
                    ]
                    if empId != Document.objects.get(documentId=documentId).writeEmp.empId:
                        if empId not in checkEmpId:
                            documentsId.append(documentId)

            # 문서상태가 완료이면서, 내가 참조자에 들어가 있는 문서
            elif category == '참조':
                for documentId in tempDocumentsId:
                    checkEmpId = [
                        i['approvalEmp__empId'] for i in Approval.objects.filter(
                            documentId__documentId=documentId,
                            approvalCategory='참조',
                        ).values(
                            'approvalEmp__empId'
                        )
                    ]
                    if empId in checkEmpId:
                        documentsId.append(documentId)

        # 문서 상태가 반려인 경우
        elif documentStatus == '반려':
            for document in documents:
                documentsId.append(document.documentId)

        # 문서 상태가 임시저장인 경우
        elif documentStatus == '임시':
            for document in documents:
                documentsId.append(document.documentId)

        returnDocuments = Document.objects.filter(
            documentId__in=documentsId
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime'
        )

        structure = json.dumps(list(returnDocuments), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
def show_document_end_all(request):
    context = {
        'documentStatus': '완료',
        'category': '전체',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_end_write(request):
    context = {
        'documentStatus': '완료',
        'category': '기안',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_end_approval(request):
    context = {
        'documentStatus': '완료',
        'category': '결재',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_end_check(request):
    context = {
        'documentStatus': '완료',
        'category': '참조',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_end_reject(request):
    context = {
        'documentStatus': '완료',
        'category': '반려',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_ing_all(request):
    context = {
        'documentStatus': '진행',
        'category': '전체',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_ing_done(request):
    context = {
        'documentStatus': '진행',
        'category': '진행',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_ing_do(request):
    context = {
        'documentStatus': '진행',
        'category': '대기',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_ing_check(request):
    context = {
        'documentStatus': '진행',
        'category': '확인',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_ing_will(request):
    context = {
        'documentStatus': '진행',
        'category': '예정',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_temp(request):
    context = {
        'documentStatus': '임시',
        'category': '임시',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def view_document(request, documentId):
    document = Document.objects.get(documentId=documentId)
    files = Documentfile.objects.filter(documentId__documentId=documentId)
    related = Relateddocument.objects.filter(documentId__documentId=documentId)
    apply, process, reference, approval, agreement, financial = template_format(documentId)
    do_approval = who_approval(documentId)['do']
    check_approval = who_approval(documentId)['check']

    # 참조자 자동완성
    empList = Employee.objects.filter(Q(empStatus='Y'))
    empNames = []
    for emp in empList:
        temp = {
            'id': emp.empId,
            'name': emp.empName,
            'position': emp.empPosition.positionName,
            'dept': emp.empDeptName,
        }
        empNames.append(temp)

    context = {
        'document': document,
        'files': files,
        'related': related,
        'empNames': empNames,
        'approvalList': [apply, process, approval, agreement, financial],
        'reference': reference,
        'do_approval': do_approval,
        'check_approval': check_approval,
    }
    return render(request, 'approval/viewdocument.html', context)


@login_required
def approve_document(request, approvalId):
    now = datetime.datetime.now()

    approval = Approval.objects.get(approvalId=approvalId)
    approval.approvalStatus = '완료'
    approval.approvalDatetime = now
    approval.save()

    if len(who_approval(approval.documentId_id)['do']) == 0:
        document = Document.objects.get(documentId=approval.documentId_id)
        document.documentStatus = '완료'
        document.approveDatetime = now
        document.save()

    return redirect('approval:viewdocument', approval.documentId_id)


@login_required
def return_document(request, approvalId):
    now = datetime.datetime.now()

    approval = Approval.objects.get(approvalId=approvalId)
    approval.approvalStatus = '반려'
    approval.approvalDatetime = now
    approval.save()

    document = Document.objects.get(documentId=approval.documentId_id)
    document.documentStatus = '반려'
    document.approveDatetime = now
    document.save()

    approvals = Approval.objects.filter(Q(documentId=approval.documentId_id) & Q(approvalStatus='대기'))
    approvals.update(approvalStatus='정지')

    return redirect('approval:viewdocument', approval.documentId_id)


def post_contract_document(request, contractId, documentType):
    # 결재 문서 양식명
    formTitle = ''
    if documentType == '매출견적서':
        formTitle = '매출견적서'
    elif documentType == '수주통보서':
        formTitle = '수주통보서'
    elif documentType == '매출발행':
        formTitle = '매출발행'
    elif documentType == '선발주':
        formTitle = '선발주품의서'
    # 문서 종류 선택
    formId = Documentform.objects.get(
        categoryId__firstCategory='영업',
        categoryId__secondCategory='일반',
        formTitle=formTitle,
    )

    # 문서번호 자동생성 (yymmdd-000)
    yymmdd = str(datetime.date.today()).replace('-', '')[2:]
    todayDocumentCount = len(Document.objects.filter(documentNumber__contains=yymmdd))
    documentNumber = yymmdd + '-' + str(todayDocumentCount + 1).rjust(3, '0')

    # 문서에 필요내용 자동입력
    # 계약(contract), 매출(revenues), 매입(purchases), 계약파일(files)
    contract = Contract.objects.get(contractId=contractId)
    revenues = Revenue.objects.filter(contractId=contract)
    purchases = Purchase.objects.filter(contractId=contract)
    files = Contractfile.objects.filter(contractId=contract)

    # 계약명(contractName)
    contractName = '<a href="/sales/viewcontract/' + contractId + '/" target="_blank">[' + contract.contractCode + '] ' + \
                   contract.contractName + '</a>'

    # 매출처(revenueCompany)
    revenueCompany = ''
    for company in revenues.values('revenueCompany__companyNameKo').distinct():
        if not revenueCompany:
            revenueCompany += company['revenueCompany__companyNameKo']
        else:
            revenueCompany += (', ' + company['revenueCompany__companyNameKo'])

    # 매출액(revenuePrice), GP(profitPrice)
    revenuePrice = revenues.aggregate(Sum('revenuePrice'))['revenuePrice__sum']
    profitPrice = revenues.aggregate(Sum('revenueProfitPrice'))['revenueProfitPrice__sum']
    profitRatio = round(profitPrice / revenuePrice * 100)

    # 매입처(purchaseCompany)
    purchaseCompany = ''
    for company in purchases.values('purchaseCompany__companyNameKo').distinct():
        if not purchaseCompany:
            purchaseCompany += company['purchaseCompany__companyNameKo']
        else:
            purchaseCompany += (', ' + company['purchaseCompany__companyNameKo'])

    # 매입액(purchasePrice)
    purchasePrice = purchases.aggregate(Sum('purchasePrice'))['purchasePrice__sum']

    # 매입견적서(purchaseEstimate)
    lastFile = files.filter(fileCategory='매입견적서')
    maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
    lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
    purchaseEstimate = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    # 매출견적서(revenueEstimate)
    lastFile = files.filter(fileCategory='매출견적서')
    maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
    lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
    revenueEstimate = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    # 계약서(contractPaper)
    lastFile = files.filter(fileCategory='계약서')
    maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
    lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
    contractPaper = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    # 수주통보서(orderPaper)
    lastFile = files.filter(fileCategory='수주통보서')
    maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
    lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
    orderPaper = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    # 확인서(confirmPaper)
    lastFile = files.filter(fileCategory='납품,구축,검수확인서')
    maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
    lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
    confirmPaper = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    contentHtml = formId.formHtml
    contentHtml = contentHtml.replace('계약명자동입력', contractName)
    contentHtml = contentHtml.replace('매출처자동입력', revenueCompany)
    contentHtml = contentHtml.replace('매출액자동입력', format(revenuePrice, ',') + '원')
    contentHtml = contentHtml.replace('GP자동입력', format(profitPrice, ',') + '원 (' + str(profitRatio) + '%)')
    contentHtml = contentHtml.replace('매입처자동입력', purchaseCompany)
    contentHtml = contentHtml.replace('매입액자동입력', format(purchasePrice, ',') + '원')
    # 1. 매출견적서
    if formTitle == '매출견적서':
        contentHtml = contentHtml.replace('매입견적서링크', purchaseEstimate)
        contentHtml = contentHtml.replace('매출견적서링크', revenueEstimate)

    # 2. 수주통보서
    if formTitle == '수주통보서':
        contentHtml = contentHtml.replace('계약서링크', contractPaper)
        contentHtml = contentHtml.replace('수주통보서링크', orderPaper)

    # 3. 매출발행
    if formTitle == '매출발행':
        contentHtml = contentHtml.replace('수주통보서링크', orderPaper)
        contentHtml = contentHtml.replace('납품,구축,검수확인서링크', confirmPaper)

    # 4. 선발주
    if formTitle == '선발주품의서':
        contentHtml = contentHtml.replace('매입견적서링크', purchaseEstimate)

    # 문서 등록
    document = Document.objects.create(
        documentNumber=documentNumber,
        writeEmp=request.user.employee,
        formId=formId,
        preservationYear=formId.preservationYear,
        securityLevel=formId.securityLevel,
        title='[' + contract.contractName + '] ' + formTitle + ' 결재 자동생성',
        contentHtml=contentHtml,
        writeDatetime=datetime.datetime.now(),
        modifyDatetime=datetime.datetime.now(),
        documentStatus='임시',
        contractId=contract,
    )

    # 결재선 등록
    Approval.objects.create(
        documentId=document,
        approvalEmp=request.user.employee,
        approvalStep=1,
        approvalCategory='결재',
    )
    for a in Approvalform.objects.filter(formId=formId):
        Approval.objects.create(
            documentId=document,
            approvalEmp=a.approvalEmp,
            approvalStep=a.approvalStep,
            approvalCategory=a.approvalCategory,
        )

    return redirect('approval:modifydocument', document.documentId)
