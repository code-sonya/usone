import json
import datetime
from dateutil.relativedelta import relativedelta

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from xhtml2pdf import pisa
from django.db.models import Sum, FloatField, F, Case, When, Count, Q, Min, Max, Value, CharField

from service.models import Employee
from sales.models import Contract, Revenue, Purchase, Contractfile, Purchasefile
from client.models import Company
from hr.models import AdminEmail
from .models import Documentcategory, Documentform, Documentfile, Document, Approvalform, Relateddocument, Approval
from logs.models import ApprovalLog
from .functions import data_format, who_approval, template_format, mail_approval, mail_document, intcomma
from sales.functions import detailPurchase, summaryPurchase

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
            if request.POST['documentStatus'] == '진행' and empId.user == request.user and a['approvalStep'] == 1:
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
            return redirect("approval:showdocumentdone")
        else:
            for empId in whoApproval['do']:
                employee = Employee.objects.get(empId=empId)
                mail_approval(employee, document)

        if request.POST['documentStatus'] == '임시':
            return redirect("approval:showdocumenttemp")
        else:
            return redirect("approval:showdocumenting")

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

        whoApproval = who_approval(document.documentId)
        if len(whoApproval['do']) == 0:
            document.documentStatus = '완료'
            document.save()
            return redirect("approval:showdocumentdone")
        else:
            for empId in whoApproval['do']:
                employee = Employee.objects.get(empId=empId)
                mail_approval(employee, document)

        if request.POST['documentStatus'] == '임시':
            return redirect("approval:showdocumenttemp")
        else:
            return redirect("approval:showdocumenting")

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
        category = request.GET['category']

        documentsIngDone = []  # 진행, 완료
        documentsIngWait = []  # 진행, 대기
        documentsIngWill = []  # 진행, 예정
        documentsIngCheck = []  # 진행, 참조
        documentsDoneWrite = []  # 완료, 기안
        documentsDoneApproval = []  # 완료, 결재
        documentsDoneCheck = []  # 완료, 참조
        documentsDoneReject = []  # 완료, 반려
        documentsDoneView = []  # 완료, 조회
        documentsTemp = []  # 임시

        if category == '전체' or category == '진행':
            # 진행
            tempDocumentsId = Approval.objects.filter(
                documentId__documentStatus='진행',
                approvalEmp=request.user.employee,
            ).values_list('documentId__documentId', flat=True)

            for documentId in tempDocumentsId:
                # 진행, 완료
                if empId in who_approval(documentId)['done']:
                    documentsIngDone.append(documentId)
                # 진행, 대기
                elif empId in who_approval(documentId)['do']:
                    documentsIngWait.append(documentId)
                # 진행, 예정
                elif empId in who_approval(documentId)['will']:
                    documentsIngWill.append(documentId)
                # 진행, 참조
                elif empId in who_approval(documentId)['check']:
                    documentsIngCheck.append(documentId)

        if category == '전체' or category == '완료':
            # 완료
            tempDocumentsId = Approval.objects.filter(
                documentId__documentStatus='완료',
                approvalEmp=request.user.employee,
            ).exclude(
                approvalCategory='참조'
            ).values_list('documentId__documentId', flat=True)

            for documentId in tempDocumentsId:
                document = Document.objects.get(documentId=documentId)
                # 보존연한체크
                if document.preservationDate() > datetime.datetime.now():
                    # 완료, 기안
                    if empId == document.writeEmp.empId:
                        documentsDoneWrite.append(documentId)
                    # 완료, 결재
                    else:
                        documentsDoneApproval.append(documentId)

            tempDocumentsId = Approval.objects.filter(
                documentId__documentStatus='완료',
                approvalEmp=request.user.employee,
                approvalCategory='참조',
            ).values_list('documentId__documentId', flat=True)

            for documentId in tempDocumentsId:
                document = Document.objects.get(documentId=documentId)
                # 보존연한체크
                if document.preservationDate() > datetime.datetime.now():
                    # 완료, 참조
                    documentsDoneCheck.append(documentId)

            tempDocumentsId = Approval.objects.filter(
                documentId__documentStatus='반려',
                approvalEmp=request.user.employee,
            ).values_list('documentId__documentId', flat=True)

            for documentId in tempDocumentsId:
                document = Document.objects.get(documentId=documentId)
                # 보존연한체크
                if document.preservationDate() > datetime.datetime.now():
                    # 완료, 반려
                    documentsDoneReject.append(documentId)

            # 조회 권한에 따라 문서 추가
            tempDocumentsId = Approval.objects.filter(
                documentId__documentStatus='완료',
                documentId__securityLevel='C',
            ).exclude(
                approvalEmp=request.user.employee,
            ).values_list('documentId__documentId', flat=True)

            for documentId in tempDocumentsId:
                document = Document.objects.get(documentId=documentId)
                if document.preservationDate() > datetime.datetime.now():
                    documentsDoneView.append(documentId)

            if request.user.employee.empPosition.positionName == '임원':
                tempDocumentsId = Approval.objects.filter(
                    documentId__documentStatus='완료',
                    documentId__securityLevel='B',
                ).exclude(
                    approvalEmp=request.user.employee,
                ).values_list('documentId__documentId', flat=True)

                for documentId in tempDocumentsId:
                    document = Document.objects.get(documentId=documentId)
                    if document.preservationDate() > datetime.datetime.now():
                        documentsDoneView.append(documentId)

            if request.user.employee.empId <= 2:
                tempDocumentsId = Approval.objects.filter(
                    documentId__documentStatus='완료',
                    documentId__securityLevel='A',
                ).exclude(
                    approvalEmp=request.user.employee,
                ).values_list('documentId__documentId', flat=True)

                for documentId in tempDocumentsId:
                    document = Document.objects.get(documentId=documentId)
                    if document.preservationDate() > datetime.datetime.now():
                        documentsDoneView.append(documentId)

        if category == '임시':
            documentsTemp = list(Document.objects.filter(
                documentStatus='임시',
                writeEmp=request.user.employee
            ).values_list('documentId', flat=True))

        returnIngDone = Document.objects.filter(
            documentId__in=documentsIngDone
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('진행중', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )
        returnIngWait = Document.objects.filter(
            documentId__in=documentsIngWait
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('결재대기', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )
        returnIngWill = Document.objects.filter(
            documentId__in=documentsIngWill
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('결재예정', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )
        returnIngCheck = Document.objects.filter(
            documentId__in=documentsIngCheck
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('참조문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )
        returnDoneWrite = Document.objects.filter(
            documentId__in=documentsDoneWrite
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('기안문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )
        returnDoneApproval = Document.objects.filter(
            documentId__in=documentsDoneApproval
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('결재문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )
        returnDoneCheck = Document.objects.filter(
            documentId__in=documentsDoneCheck
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('참조문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )
        returnDoneReject = Document.objects.filter(
            documentId__in=documentsDoneReject
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('반려문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )
        returnDoneView = Document.objects.filter(
            documentId__in=documentsDoneView
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('조회가능', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )
        returnTemp = Document.objects.filter(
            documentId__in=documentsTemp
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus=Value('임시', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus'
        )

        returnDocuments = returnIngDone.union(
            returnIngWait, returnIngWill, returnIngCheck,
            returnDoneWrite, returnDoneApproval, returnDoneCheck, returnDoneReject, returnDoneView,
            returnTemp
        )

        structure = json.dumps(list(returnDocuments), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
def show_document_all(request):
    context = {
        'category': '전체',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_ing(request):
    context = {
        'category': '진행',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_done(request):
    context = {
        'category': '완료',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_temp(request):
    context = {
        'category': '임시',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def view_document(request, documentId):
    document = Document.objects.get(documentId=documentId)
    # 문서 읽음 처리
    if document.clicked == 'N':
        document.clicked = 'Y'
        document.save()
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
    # smtp 정보
    email = AdminEmail.objects.aggregate(Max('adminId'))
    email = AdminEmail.objects.get(adminId=email['adminId__max'])

    context = {
        'document': document,
        'files': files,
        'related': related,
        'empNames': empNames,
        'approvalList': [apply, process, approval, agreement, financial],
        'reference': reference,
        'do_approval': do_approval,
        'check_approval': check_approval,
        'email': email
    }
    return render(request, 'approval/viewdocument.html', context)


@login_required
def approve_document(request, approvalId):
    now = datetime.datetime.now()

    approval = Approval.objects.get(approvalId=approvalId)
    approval.approvalStatus = '완료'
    approval.approvalDatetime = now
    approval.save()

    whoApproval = who_approval(approval.documentId_id)
    if len(whoApproval['do']) == 0:
        document = Document.objects.get(documentId=approval.documentId_id)
        document.documentStatus = '완료'
        document.approveDatetime = now
        document.save()
    else:
        for empId in whoApproval['do']:
            employee = Employee.objects.get(empId=empId)
            document = Document.objects.get(documentId=approval.documentId_id)
            mail_approval(employee, document)

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
    if lastFile:
        maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
        lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
        purchaseEstimate = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    # 매출견적서(revenueEstimate)
    lastFile = files.filter(fileCategory='매출견적서')
    if lastFile:
        maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
        lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
        revenueEstimate = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    # 계약서(contractPaper)
    lastFile = files.filter(fileCategory='계약서')
    if lastFile:
        maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
        lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
        contractPaper = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    # 수주통보서(orderPaper)
    lastFile = files.filter(fileCategory='수주통보서')
    if lastFile:
        maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
        lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
        orderPaper = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    # 확인서(confirmPaper)
    lastFile = files.filter(fileCategory='납품,구축,검수확인서')
    if lastFile:
        maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
        lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
        confirmPaper = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'

    contentHtml = formId.formHtml

    # 1. 수주통보서
    if formTitle == '수주통보서':
        # 계약 내용 요약
        contentHtml = contentHtml.replace('부서자동입력', contract.empDeptName)
        contentHtml = contentHtml.replace('영업대표자동입력', contract.empName)
        contentHtml = contentHtml.replace('계약명자동입력', contractName)

        # 계약정보
        contentHtml = contentHtml.replace('거래처자동입력', contract.saleCompanyName.companyNameKo)
        if contract.endCompanyName:
            contentHtml = contentHtml.replace('최종고객사자동입력', contract.endCompanyName.companyNameKo)
        else:
            contentHtml = contentHtml.replace('최종고객사자동입력', '')
        contentHtml = contentHtml.replace('대분류자동입력', contract.mainCategory)
        contentHtml = contentHtml.replace('소분류자동입력', contract.subCategory)
        contentHtml = contentHtml.replace('산업군,판매유형자동입력', contract.saleIndustry + '·' + contract.saleType)
        contentHtml = contentHtml.replace('계약일자동입력', str(contract.contractDate))
        if contract.contractStartDate or contract.contractEndDate:
            contentHtml = contentHtml.replace(
                '계약기간자동입력', str(contract.contractStartDate) + '~' + str(contract.contractEndDate)
            )
        else:
            contentHtml = contentHtml.replace('계약기간자동입력', '')
        contentHtml = contentHtml.replace('계약금액자동입력', format(contract.salePrice, ',') + '  ')
        if contract.depositCondition == '계산서 발행 후':
            contentHtml = contentHtml.replace(
                '수금조건자동입력', contract.depositCondition + ' ' + str(contract.depositConditionDay) + '일 이내'
            )
        elif contract.depositCondition == '당월' or contract.depositCondition == '익월':
            contentHtml = contentHtml.replace(
                '수금조건자동입력', contract.depositCondition + ' ' + str(contract.depositConditionDay) + '일'
            )
        else:
            contentHtml = contentHtml.replace(
                '수금조건자동입력', contract.depositCondition
            )

        # CoG정보
        contentHtml = contentHtml.replace('매출금액자동입력', format(revenuePrice, ','))
        contentHtml = contentHtml.replace('매출합계자동입력', format(revenuePrice, ','))
        contentHtml = contentHtml.replace('마진금액자동입력', format(profitPrice, ','))
        contentHtml = contentHtml.replace('마진합계자동입력', format(profitPrice, ','))
        summary = summaryPurchase(contractId, contract.salePrice)
        contentHtml = contentHtml.replace('상품HW매입금액자동입력', intcomma(summary['sumType1']))
        contentHtml = contentHtml.replace('상품SW매입금액자동입력', intcomma(summary['sumType2']))
        contentHtml = contentHtml.replace('용역HW매입금액자동입력', intcomma(summary['sumType3']))
        contentHtml = contentHtml.replace('용역SW매입금액자동입력', intcomma(summary['sumType4']))
        contentHtml = contentHtml.replace('기타매입금액자동입력', intcomma(summary['sumType5']))
        contentHtml = contentHtml.replace('매입합계자동입력', intcomma(summary['sumPurchase']))

        # 마진율분석
        contentHtml = contentHtml.replace('마진율자동입력', str(profitRatio) + '%')
        if (profitRatio - 15) > 0:
            contentHtml = contentHtml.replace('>마진분석결과자동입력', ' style="color: red;">' + str(profitRatio-15) + '%')
        else:
            contentHtml = contentHtml.replace('>마진분석결과자동입력', ' style="color: blue;">' + str(profitRatio - 15) + '%')

        # 고객정보
        if contract.saleCompanyName.ceo:
            contentHtml = contentHtml.replace('고객대표자자동입력', contract.saleCompanyName.ceo)
        else:
            contentHtml = contentHtml.replace('고객대표자자동입력', '')
        if contract.saleCompanyName.companyAddress:
            contentHtml = contentHtml.replace('고객주소자동입력', contract.saleCompanyName.companyAddress)
        else:
            contentHtml = contentHtml.replace('고객주소자동입력', '')
        if contract.saleCustomerId:
            contentHtml = contentHtml.replace('영업담당자이름자동입력', contract.saleCustomerId.customerName)
            contentHtml = contentHtml.replace('영업담당자연락처자동입력', contract.saleCustomerId.customerPhone)
            contentHtml = contentHtml.replace('영업담당자이메일자동입력', contract.saleCustomerId.customerEmail)
        else:
            contentHtml = contentHtml.replace('영업담당자이름자동입력', '')
            contentHtml = contentHtml.replace('영업담당자연락처자동입력', '')
            contentHtml = contentHtml.replace('영업담당자이메일자동입력', '')

        if contract.saleTaxCustomerId:
            contentHtml = contentHtml.replace('세금담당자이름자동입력', contract.saleTaxCustomerId.customerName)
            contentHtml = contentHtml.replace('세금담당자연락처자동입력', contract.saleTaxCustomerId.customerPhone)
            contentHtml = contentHtml.replace('세금담당자이메일자동입력', contract.saleTaxCustomerId.customerEmail)
        else:
            contentHtml = contentHtml.replace('세금담당자이름자동입력', '')
            contentHtml = contentHtml.replace('세금담당자연락처자동입력', '')
            contentHtml = contentHtml.replace('세금담당자이메일자동입력', '')

        # 하도급계약
        tempClass = {}
        for i in range(1, 9):
            tempClass[str(i)], tempClass['sum_'+str(i)] = detailPurchase(contractId, i)

        tempStr = ''
        if tempClass['1']:
            for t in tempClass['1']:
                tempStr += '''<tr style="height: 25px;">
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.companyName.companyNameKo + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.contents + '''</td>
                    <td style="text-align: right; padding-left: 10px; padding-right: 10px; border: 1px solid grey; border-collapse: collapse;
                    font-size: 11px;">''' + format(t.price, ',') + '''</td>
                    </tr>'''
        contentHtml = contentHtml.replace('<tr><td colspan="3">상품HW테이블자동입력</td></tr>', tempStr)
        contentHtml = contentHtml.replace('상품HW합계자동입력', format(tempClass['sum_1'], ','))

        tempStr = ''
        if tempClass['2']:
            for t in tempClass['2']:
                tempStr += '''<tr style="height: 25px;">
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.companyName.companyNameKo + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.contents + '''</td>
                    <td style="text-align: right; padding-left: 10px; padding-right: 10px; border: 1px solid grey; border-collapse: collapse;
                    font-size: 11px;">''' + format(t.price, ',') + '''</td>
                    </tr>'''
        contentHtml = contentHtml.replace('<tr><td colspan="3">상품SW테이블자동입력</td></tr>', tempStr)
        contentHtml = contentHtml.replace('상품SW합계자동입력', format(tempClass['sum_2'], ','))

        tempStr = ''
        if tempClass['3']:
            for t in tempClass['3']:
                tempStr += '''<tr style="height: 25px;">
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.companyName.companyNameKo + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.contents + '''</td>
                    <td style="text-align: right; padding-left: 10px; padding-right: 10px; border: 1px solid grey; border-collapse: collapse;
                    font-size: 11px;">''' + format(t.price, ',') + '''</td>
                    </tr>'''
        contentHtml = contentHtml.replace('<tr><td colspan="3">유지보수HW테이블자동입력</td></tr>', tempStr)
        contentHtml = contentHtml.replace('유지보수HW합계자동입력', format(tempClass['sum_3'], ','))

        tempStr = ''
        if tempClass['4']:
            for t in tempClass['4']:
                tempStr += '''<tr style="height: 25px;">
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.companyName.companyNameKo + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.contents + '''</td>
                    <td style="text-align: right; padding-left: 10px; padding-right: 10px; border: 1px solid grey; border-collapse: collapse;
                    font-size: 11px;">''' + format(t.price, ',') + '''</td>
                    </tr>'''
        contentHtml = contentHtml.replace('<tr><td colspan="3">유지보수SW테이블자동입력</td></tr>', tempStr)
        contentHtml = contentHtml.replace('유지보수SW합계자동입력', format(tempClass['sum_4'], ','))

        tempStr = ''
        if tempClass['5']:
            for t in tempClass['5']:
                tempStr += '''<tr style="height: 25px;">
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.classification + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + str(t.times) + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + str(t.sites) + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + format(t.units, ',') + '''</td>
                    <td style="text-align: right; padding-left: 10px; padding-right: 10px; border: 1px solid grey; border-collapse: collapse;
                    font-size: 11px;">''' + format(t.price, ',') + '''</td>
                    </tr>'''
        contentHtml = contentHtml.replace('<tr><td colspan="5">인력지원자사자동입력</td></tr>', tempStr)
        contentHtml = contentHtml.replace('인력지원자사합계자동입력', format(tempClass['sum_5'], ','))

        tempStr = ''
        if tempClass['6']:
            for t in tempClass['6']:
                tempStr += '''<tr style="height: 25px;">
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.classification + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.contents + '''</td>
                    <td style="text-align: right; padding-left: 10px; padding-right: 10px; border: 1px solid grey; border-collapse: collapse;
                    font-size: 11px;">''' + format(t.price, ',') + '''</td>
                    </tr>'''
        contentHtml = contentHtml.replace('<tr><td colspan="3">인력지원타사자동입력</td></tr>', tempStr)
        contentHtml = contentHtml.replace('인력지원타사합계자동입력', format(tempClass['sum_6'], ','))

        tempStr = ''
        if tempClass['7']:
            for t in tempClass['7']:
                if t.contractStartDate or t.contractEndDate:
                    contractDate = str(t.contractStartDate) + ' ~ ' + str(t.contractEndDate)
                else:
                    contractDate = ''
                tempStr += '''<tr style="height: 25px;">
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.contractNo + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + contractDate + '''</td>
                    <td style="text-align: right; padding-left: 10px; padding-right: 10px; border: 1px solid grey; border-collapse: collapse;
                    font-size: 11px;">''' + format(t.price, ',') + '''</td>
                    </tr>'''
        contentHtml = contentHtml.replace('<tr><td colspan="3">DBCOSTS테이블자동입력</td></tr>', tempStr)
        contentHtml = contentHtml.replace('DBCOSTS합계자동입력', format(tempClass['sum_7'], ','))

        tempStr = ''
        if tempClass['8']:
            for t in tempClass['8']:
                tempStr += '''<tr style="height: 25px;">
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.classification + '''</td>
                    <td style="text-align: center; border: 1px solid grey; border-collapse: collapse; font-size: 11px;">
                    ''' + t.contents + '''</td>
                    <td style="text-align: right; padding-left: 10px; padding-right: 10px; border: 1px solid grey; border-collapse: collapse;
                    font-size: 11px;">''' + format(t.price, ',') + '''</td>
                    </tr>'''
        contentHtml = contentHtml.replace('<tr><td colspan="3">기타테이블자동입력</td></tr>', tempStr)
        contentHtml = contentHtml.replace('기타합계자동입력', format(tempClass['sum_8'], ','))

        # Billing Schedule
        pMinYear = purchases.aggregate(Min('predictBillingDate__year'))
        pMaxYear = purchases.aggregate(Max('predictBillingDate__year'))
        rMinYear = revenues.aggregate(Min('predictBillingDate__year'))
        rMaxYear = revenues.aggregate(Max('predictBillingDate__year'))
        if pMinYear['predictBillingDate__year__min'] < rMinYear['predictBillingDate__year__min']:
            minYear = pMinYear
        else:
            minYear = rMinYear
        if pMaxYear['predictBillingDate__year__max'] > rMaxYear['predictBillingDate__year__max']:
            maxYear = pMaxYear
        else:
            maxYear = rMaxYear
        delta = relativedelta(years=+1)

        yearList = []
        y = minYear['predictBillingDate__year__min']
        while y <= maxYear['predictBillingDate__year__max']:
            yearList.append(y)
            y += delta

        monthList = []
        for y in yearList:
            dateList = []
            for d in range(1, 13):
                dateList.append('{}-{}'.format(y.year, str(d).zfill(2)))
            monthList.append(dateList)

        groupPurchases = purchases.values(
            'predictBillingDate__year', 'predictBillingDate__month', 'purchaseCompany'
        ).annotate(
            price=Sum('purchasePrice')
        )
        groupRevenues = revenues.values(
            'predictBillingDate__year', 'predictBillingDate__month', 'revenueCompany'
        ).annotate(
            price=Sum('revenuePrice')
        )
        groupMonthPurchases = purchases.values(
            'predictBillingDate__year', 'predictBillingDate__month'
        ).annotate(
            price=Sum('purchasePrice')
        )
        groupMonthRevenues = revenues.values(
            'predictBillingDate__year', 'predictBillingDate__month'
        ).annotate(
            price=Sum('revenuePrice')
        )
        companyPurchases = purchases.values_list('purchaseCompany__companyName', flat=True).distinct()
        companyRevenues = revenues.values_list('revenueCompany__companyName', flat=True).distinct()

        pBillingSchedule = []
        sumpBillingSchedule = []
        rBillingSchedule = []
        sumrBillingSchedule = []
        for month in monthList:
            sumrBillingSchedule.append({
                'list': month, 'year': month[0][:4], 'name': 'sum',
                '1': '', '2': '', '3': '', '4': '', '5': '', '6': '', '7': '', '8': '', '9': '', '10': '', '11': '', '12': '', 'sum': 0
            })
            sumpBillingSchedule.append({
                'list': month, 'year': month[0][:4], 'name': 'sum',
                '1': '', '2': '', '3': '', '4': '', '5': '', '6': '', '7': '', '8': '', '9': '', '10': '', '11': '', '12': '', 'sum': 0
            })
            for c in list(set(companyPurchases)):
                pBillingSchedule.append({
                    'list': month, 'year': month[0][:4], 'name': c,
                    '1': '', '2': '', '3': '', '4': '', '5': '', '6': '', '7': '', '8': '', '9': '', '10': '', '11': '', '12': '', 'sum': 0
                })
            for c in list(set(companyRevenues)):
                rBillingSchedule.append({
                    'list': month, 'year': month[0][:4], 'name': c,
                    '1': '', '2': '', '3': '', '4': '', '5': '', '6': '', '7': '', '8': '', '9': '', '10': '', '11': '', '12': '', 'sum': 0
                })

        # 매입
        for group in groupPurchases:
            for schedule in pBillingSchedule:
                if schedule['year'] == str(group['predictBillingDate__year']) and schedule['name'] == group['purchaseCompany']:
                    schedule[str(group['predictBillingDate__month'])] = group['price']
                    schedule['sum'] += group['price']
        for groupMonth in groupMonthPurchases:
            for sumBilling in sumpBillingSchedule:
                if sumBilling['year'] == str(groupMonth['predictBillingDate__year']):
                    sumBilling[str(groupMonth['predictBillingDate__month'])] = groupMonth['price']
                    sumBilling['sum'] += groupMonth['price']

        # 매출
        for group in groupRevenues:
            for schedule in rBillingSchedule:
                if schedule['year'] == str(group['predictBillingDate__year']) and schedule['name'] == group['revenueCompany']:
                    schedule[str(group['predictBillingDate__month'])] = group['price']
                    schedule['sum'] += group['price']
        for groupMonth in groupMonthRevenues:
            for sumBilling in sumrBillingSchedule:
                if sumBilling['year'] == str(groupMonth['predictBillingDate__year']):
                    sumBilling[str(groupMonth['predictBillingDate__month'])] = groupMonth['price']
                    sumBilling['sum'] += groupMonth['price']

        tempStr = ''
        for year in monthList:
            tempStr += '<tr><td><table width="100%">'
            # 구분, 업체명, 날짜
            tempStr += '''
              <tr style="height: 25px; font-size: 11px;">
                <td style="background-color: #ebfaff;" width="6%">구분</td>
                <td style="background-color: #ebfaff;" width="16%">업체명</td>
            '''
            for month in year:
                tempStr += '''
                <td style="background-color: #ebfaff;" width="6%">''' + str(month) + '''</td>
                '''
            tempStr += '''
                <td style="background-color: #ebfaff;" width="6%">TOTAL</td>
              </tr>
            '''
            # 업체별 매출
            for billing in rBillingSchedule:
                if billing['list'] == year:
                    tempStr += '''
              <tr style="height: 25px; font-size: 11px;">
                <td>매출</td>
                <td>''' + billing['name'] + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['1']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['2']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['3']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['4']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['5']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['6']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['7']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['8']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['9']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['10']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['11']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['12']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(billing['sum']) + '''</td>
              </tr>
                    '''
            # 매출 총합
            for sumBilling in sumrBillingSchedule:
                if sumBilling['list'] == year:
                    tempStr += '''
              <tr style="height: 25px; font-size: 11px;">
                <td colspan="2" style="background-color: gainsboro">TOTAL</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['1']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['2']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['3']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['4']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['5']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['6']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['7']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['8']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['9']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['10']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['11']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['12']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['sum']) + '''</td>
              </tr>
                    '''
            # 업체별 매입
            for billing in pBillingSchedule:
                if billing['list'] == year:
                    tempStr += '''
              <tr style="height: 25px; font-size: 11px;">
                <td>매입</td>
                <td>''' + billing['name'] + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['1']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['2']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['3']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['4']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['5']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['6']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['7']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['8']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['9']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['10']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['11']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['12']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(billing['sum']) + '''</td>
              </tr>
                    '''
            # 매입총합
            for sumBilling in sumpBillingSchedule:
                if sumBilling['list'] == year:
                    tempStr += '''
              <tr style="height: 25px; font-size: 11px; margin-bottom: 5px">
                <td colspan="2"style="background-color: gainsboro">TOTAL</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['1']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['2']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['3']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['4']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['5']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['6']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['7']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['8']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['9']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['10']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['11']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['12']) + '''</td>
                <td style="text-align: right; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(sumBilling['sum']) + '''</td>
              </tr>
                    '''
            tempStr += '</table></td></tr>'

        contentHtml = contentHtml.replace('<tr><td>빌링스케쥴자동입력</td></tr>', tempStr)

    # 2. 매출발행
    if formTitle == '매출발행':
        contentHtml = contentHtml.replace('계약명자동입력', contractName)
        contentHtml = contentHtml.replace('매출처자동입력', revenueCompany)
        contentHtml = contentHtml.replace('매출액자동입력', format(revenuePrice, ',') + '원')
        contentHtml = contentHtml.replace('GP자동입력', format(profitPrice, ',') + '원 (' + str(profitRatio) + '%)')
        contentHtml = contentHtml.replace('매입처자동입력', purchaseCompany)
        contentHtml = contentHtml.replace('매입액자동입력', format(purchasePrice, ',') + '원')
        contentHtml = contentHtml.replace('수주통보서링크', orderPaper)
        contentHtml = contentHtml.replace('납품,구축,검수확인서링크', confirmPaper)

    # 3. 선발주
    if formTitle == '선발주품의서':
        contentHtml = contentHtml.replace('계약명자동입력', contractName)
        contentHtml = contentHtml.replace('매출처자동입력', revenueCompany)
        contentHtml = contentHtml.replace('매출액자동입력', format(revenuePrice, ',') + '원')
        contentHtml = contentHtml.replace('GP자동입력', format(profitPrice, ',') + '원 (' + str(profitRatio) + '%)')

        if request.method == 'POST':
            files = Purchasefile.objects.filter(contractId=contract, fileCategory='매입견적서')
            purchaseIds = json.loads(request.POST['purchaseIds'])
            purchaseInAdvance = purchases.filter(purchaseId__in=purchaseIds)
            purchaseCompany = ''
            purchaseEstimate = ''
            for company in purchaseInAdvance.values('purchaseCompany__companyNameKo').distinct():
                companyName = company['purchaseCompany__companyNameKo']
                purchaseCompany += (companyName + ', ')
                companyObj = Company.objects.get(companyNameKo=companyName)
                lastFile = files.filter(purchaseCompany=companyObj)
                if lastFile:
                    maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
                    lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
                    purchaseEstimate += '&nbsp;&nbsp; ' + companyName + ' : ' + \
                                        '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a><br>'
                else:
                    purchaseEstimate += '&nbsp;&nbsp; ' + companyName + ' : ' + '첨부파일 없음<br>'
            purchaseCompany = purchaseCompany[:-2]

            purchasePrice = purchaseInAdvance.aggregate(Sum('purchasePrice'))['purchasePrice__sum']
            contentHtml = contentHtml.replace('매입처자동입력', purchaseCompany)
            contentHtml = contentHtml.replace('매입액자동입력', format(purchasePrice, ',') + '원')
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


@login_required
def view_documentemail(request, documentId):
    if request.method == 'POST':
        document = Document.objects.get(documentId=documentId)
        empEmail = request.POST['empEmail']
        address = request.POST['address']

        empEmail ='{}@{}'.format(empEmail, address)
        if empEmail:
            result = mail_document(empEmail, request.user.employee.empEmail, document)

        if result == 'Y':
            ApprovalLog.objects.create(
                empId=Employee(empId=request.user.employee.empId),
                toEmail=empEmail,
                approvalDatetime=datetime.datetime.now(),
                documentId=document,
            )
        else:
            ApprovalLog.objects.create(
                empId=Employee(empId=request.user.employee.empId),
                toEmail=empEmail,
                approvalDatetime=datetime.datetime.now(),
                documentId=document,
                approvalStatus='전송실패',
                approvalError=result,
            )

        return redirect('approval:viewdocument', document.documentId)


@csrf_exempt
@login_required
def counting_asjson(request):
    empId = request.user.employee.empId
    documentsIngWait = []
    tempDocumentsId = Approval.objects.filter(
        documentId__documentStatus='진행',
        approvalEmp=request.user.employee,
    ).values_list('documentId__documentId', flat=True)

    for documentId in tempDocumentsId:
        # 진행, 대기
        if empId in who_approval(documentId)['do']:
            documentsIngWait.append(documentId)

    returnIngWait = Document.objects.filter(
        documentId__in=documentsIngWait
    ).annotate(
        empName=F('writeEmp__empName'),
        formNumber=F('formId__formNumber'),
        formTitle=F('formId__formTitle'),
        displayStatus=Value('결재대기', output_field=CharField())
    ).aggregate(Count('empName'))
    result = returnIngWait['empName__count']

    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')

