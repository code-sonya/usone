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

from service.models import Employee
from .models import Documentcategory, Documentform, Documentfile, Document, Approvalform, Relateddocument, Approval
from .functions import data_format, who_approval, template_format


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
        filesInfo = {}  # {fileName1: fileSize1, fileName2: fileSize2, ...}
        filesName = []  # [fileName1, fileName2, ...]
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

        # 관련문서 처리
        jsonId = json.loads(request.POST['relatedDocumentId'])
        for relatedId in jsonId:
            relatedDocument = Document.objects.get(documentId=relatedId)
            Relateddocument.objects.create(
                documentId=documentId,
                relatedDocumentId=relatedDocument,
            )

        # 결재선 처리
        if request.POST['documentStatus'] == '진행':
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
                if empId.user == request.user:
                    Approval.objects.create(
                        documentId=documentId,
                        approvalEmp=empId,
                        approvalStep=a['approvalStep'],
                        approvalCategory=a['approvalCategory'],
                        approvalStatus='완료',
                        approvalDatetime=datetime.datetime.now(),
                    )
                else:
                    Approval.objects.create(
                        documentId=documentId,
                        approvalEmp=empId,
                        approvalStep=a['approvalStep'],
                        approvalCategory=a['approvalCategory'],
                    )
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
        filesInfo = {}  # {fileName1: fileSize1, fileName2: fileSize2, ...}
        filesName = []  # [fileName1, fileName2, ...]
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

        # 관련문서 처리
        jsonId = json.loads(request.POST['relatedDocumentId'])
        for relatedId in jsonId:
            relatedDocument = Document.objects.get(documentId=relatedId)
            Relateddocument.objects.create(
                documentId=documentId,
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
                    documentId=documentId,
                    approvalEmp=empId,
                    approvalStep=a['approvalStep'],
                    approvalCategory=a['approvalCategory'],
                    approvalStatus='완료',
                    approvalDatetime=datetime.datetime.now(),
                )
            else:
                Approval.objects.create(
                    documentId=documentId,
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
        documentformId = Documentform.objects.create(
            categoryId=categoryId,
            approvalFormat=request.POST['approvalFormat'],
            formNumber=request.POST['formNumber'],
            formTitle=request.POST['formTitle'],
            formHtml=request.POST['formHtml'],
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
        form.formHtml = request.POST['formHtml']
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
        apply, process, reference, approval, agreement, financial = data_format(formId, request.user)

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
            ).values('formNumber', 'formTitle', 'approvalFormat')
            structure = json.dumps(list(documentForm), cls=DjangoJSONEncoder)
            return HttpResponse(structure, content_type='application/json')
        elif request.GET['type'] == 'form':
            documentForm = Documentform.objects.filter(
                Q(categoryId__firstCategory=request.GET['firstCategory']) &
                Q(categoryId__secondCategory=request.GET['secondCategory']) &
                Q(formTitle=request.GET['formTitle'])
            ).values(
                'preservationYear', 'securityLevel', 'formHtml', 'approvalFormat', 'formId'
            )
            apply, process, reference, approval, agreement, financial = data_format(documentForm.first()['formId'], request.user)
            approvalList = {"apply": apply or None, "process": process or None, "reference": reference or None, "approval": approval or None, "agreement": agreement or None, "financial": financial or None}
            structureList = list(documentForm)
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
            'formNumber', 'formTitle', 'documentStatus'
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
    print(do_approval, check_approval)

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
    approval = Approval.objects.get(approvalId=approvalId)
    approval.approvalStatus = '완료'
    approval.approvalDatetime = datetime.datetime.now()
    approval.save()
    if len(who_approval(approval.documentId_id)['do']) == 0:
        document = Document.objects.get(documentId=approval.documentId_id)
        document.documentStatus = '완료'
        document.save()
    return redirect('approval:viewdocument', approval.documentId_id)


@login_required
def return_document(request, approvalId):
    approval = Approval.objects.get(approvalId=approvalId)
    approval.approvalStatus = '반려'
    approval.approvalDatetime = datetime.datetime.now()
    approval.save()

    document = Document.objects.get(documentId=approval.documentId_id)
    document.documentStatus = '반려'
    document.save()

    approvals = Approval.objects.filter(Q(documentId=approval.documentId_id) & Q(approvalStatus='대기'))
    approvals.update(approvalStatus='정지')

    return redirect('approval:viewdocument', approval.documentId_id)


