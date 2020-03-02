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
from sales.models import Contract, Revenue, Purchase, Contractfile, Purchasefile, Contractitem, Purchasecontractitem
from client.models import Company
from hr.models import AdminEmail
from service.models import Vacation
from extrapay.models import ExtraPay
from .models import Documentcategory, Documentform, Documentfile, Document, Approvalform, Relateddocument, Approval, Documentcomment
from logs.models import ApprovalLog
from .functions import data_format, who_approval, template_format, mail_approval, mail_document, intcomma
from hr.functions import siteMap
from sales.functions import detailPurchase, summary

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

        if request.POST['documentStatus'] == '진행':
            whoApproval = who_approval(document.documentId)
            if len(whoApproval['do']) == 0:
                document.documentStatus = '완료'
                document.approveDatetime = datetime.datetime.now()
                document.save()
                return redirect("approval:showdocumentdone")
            else:
                for empId in whoApproval['do']:
                    employee = Employee.objects.get(empId=empId)
                    mail_approval(employee, document, "결재요청")
                for empId in whoApproval['check']:
                    employee = Employee.objects.get(empId=empId)
                    mail_approval(employee, document, "참조문서")

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

        deptLevelList = siteMap()

        context = {
            'empNames': empNames,
            'deptLevelList': deptLevelList,
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

        # 계약 수정 권한
        if request.POST['formTitle'] == '수주통보서':
            contract = Contract.objects.get(contractId=document.contractId.contractId)
            contract.modifyContract = 'N'
            contract.save()

        # 보존연한 숫자로 변환
        if request.POST['preservationYear'] == '영구':
            document.preservationYear = 9999
        else:
            document.preservationYear = request.POST['preservationYear'][:-1]

        document.securityLevel = request.POST['securityLevel'][0]
        document.title = request.POST['title']
        # 문서 전처리 (\n 없애고, '를 "로 변경)
        HTML = request.POST['contentHtml']
        HTML = HTML.replace('\'', '"')
        HTML = HTML.replace('\r', '')
        HTML = HTML.replace('\n', '')
        document.contentHtml = HTML
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
        if request.POST['documentStatus'] == '진행':
            whoApproval = who_approval(document.documentId)
            if len(whoApproval['do']) == 0:
                document.documentStatus = '완료'
                document.save()
                return redirect("approval:showdocumentdone")
            else:
                for empId in whoApproval['do']:
                    employee = Employee.objects.get(empId=empId)
                    mail_approval(employee, document, "결재요청")
                for empId in whoApproval['check']:
                    employee = Employee.objects.get(empId=empId)
                    mail_approval(employee, document, "참조문서")

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
def delete_document(request, documentId):
    document = Document.objects.get(documentId=documentId)
    document.documentStatus = '삭제'
    document.save()
    return redirect("approval:showdocumenttemp")


@login_required
def admin_delete_document(request, documentId):
    document = Document.objects.get(documentId=documentId)
    document.documentStatus = '삭제'
    document.save()

    if document.formId.formTitle == '휴가신청서':
        vacations = Vacation.objects.filter(documentId=document)
        vacationDay = 0
        for vacation in vacations:
            if vacation.vacationType == '일차':
                vacationDay += 1
            else:
                vacationDay += 0.5

        emp = document.writeEmp
        categoryName = vacations.first().vacationCategory.categoryName
        if categoryName == '연차':
            emp.empAnnualLeave += vacationDay
            emp.save()
        elif categoryName == '근속연차':
            emp.empSpecialLeave += vacationDay
            emp.save()
        elif categoryName == '금차':
            emp.empSpecialLeave2 += vacationDay
            emp.save()
        elif categoryName == '대체휴무':
            emp.empSpecialLeave3 += vacationDay
            emp.save()
        vacations.delete()

    return redirect("approval:showdocumentadmindone")


@login_required
def draft_cancel(request, documentId):
    now = datetime.datetime.now()
    beforeDocument = Document.objects.get(documentId=documentId)

    # 계약 수정 권한
    if beforeDocument.formId.formTitle == '수주통보서':
        contract = Contract.objects.get(contractId=beforeDocument.contractId.contractId)
        contract.modifyContract = 'Y'
        contract.save()

    # 기존 문서 삭제 처리
    beforeDocument.documentStatus = '삭제'
    beforeDocument.save()

    if beforeDocument.formId.copyAuth == 'Y':
        # 기존 문서 복사
        document = Document.objects.get(documentId=documentId)
        document.pk = None

        # 문서번호 자동생성 (yymmdd-000)
        yymmdd = str(datetime.date.today()).replace('-', '')[2:]
        todayDocumentCount = len(Document.objects.filter(documentNumber__contains=yymmdd))
        documentNumber = yymmdd + '-' + str(todayDocumentCount + 1).rjust(3, '0')
        document.documentNumber = documentNumber
        # 작성, 수정시간은 현재시간
        document.writeDatetime = now
        document.modifyDatetime = now
        # 기안, 완료일시는 Null
        document.draftDatetime = None
        document.ApproveDatetime = None
        # 문서상태는 임시문서
        document.documentStatus = '임시'
        document.save()

        # 결재선 복사
        approvals = Approval.objects.filter(documentId=beforeDocument)
        for approval in approvals:
            approval.pk = None
            approval.documentId = document
            approval.approvalStatus = '대기'
            approval.approvalDatetime = None
            approval.save()

        return redirect("approval:showdocumenttemp")

    else:
        if beforeDocument.formId.formTitle == '휴가신청서':
            vacations = Vacation.objects.filter(documentId=beforeDocument)
            vacations.update(vacationStatus='R')
            vacationDay = 0
            for vacation in vacations:
                if vacation.vacationType == '일차':
                    vacationDay += 1
                else:
                    vacationDay += 0.5

            emp = beforeDocument.writeEmp
            categoryName = vacations.first().vacationCategory.categoryName
            if categoryName == '연차':
                emp.empAnnualLeave += vacationDay
                emp.save()
            elif categoryName == '근속연차':
                emp.empSpecialLeave += vacationDay
                emp.save()
            elif categoryName == '금차':
                emp.empSpecialLeave2 += vacationDay
                emp.save()
            elif categoryName == '대체휴무':
                emp.empSpecialLeave3 += vacationDay
                emp.save()
            vacations.delete()

            return redirect("service:showvacations")
        return redirect("approval:showdocumenting")


@login_required
def copy_document(request, documentId):
    now = datetime.datetime.now()
    beforeDocument = Document.objects.get(documentId=documentId)

    document = Document.objects.get(documentId=documentId)
    document.pk = None
    # 문서번호 자동생성 (yymmdd-000)
    yymmdd = str(datetime.date.today()).replace('-', '')[2:]
    todayDocumentCount = len(Document.objects.filter(documentNumber__contains=yymmdd))
    documentNumber = yymmdd + '-' + str(todayDocumentCount + 1).rjust(3, '0')
    document.documentNumber = documentNumber
    # 작성, 수정시간은 현재시간
    document.writeDatetime = now
    document.modifyDatetime = now
    # 기안, 완료일시는 Null
    document.draftDatetime = None
    document.ApproveDatetime = None
    # 문서상태는 임시문서
    document.documentStatus = '임시'
    document.save()

    # 결재선 복사
    approvals = Approval.objects.filter(documentId=beforeDocument)
    for approval in approvals:
        approval.pk = None
        approval.documentId = document
        approval.approvalStatus = '대기'
        approval.approvalDatetime = None
        approval.save()

    return redirect("approval:modifydocument", document.documentId)


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
            copyAuth=request.POST['copyAuth'],
            mailAuth=request.POST['mailAuth']
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
        form.copyAuth = request.POST['copyAuth']
        form.mailAuth = request.POST['mailAuth']
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
            ).distinct().order_by('firstCategory')
        elif request.GET['category'] == 'second':
            documentCategory = Documentcategory.objects.filter(
                firstCategory=request.GET['firstCategory']
            ).values(
                'secondCategory'
            ).distinct().order_by('secondCategory')
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
            ).order_by(
                'formNumber'
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
        documentsIng = []  # 진행, 관리자
        documentsDone = []  # 완료, 관리자
        documentsReject = []  # 반려, 관리자

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
            # C등급 문서는 전체 조회
            tempDocumentsId = Approval.objects.filter(
                documentId__documentStatus='완료',
                documentId__securityLevel='C',
            ).values_list('documentId__documentId', flat=True)

            for documentId in tempDocumentsId:
                document = Document.objects.get(documentId=documentId)
                if document.preservationDate() > datetime.datetime.now():
                    documentsDoneView.append(documentId)

            # B등급 문서는 임원 조회
            if request.user.employee.empPosition.positionName == '임원':
                tempDocumentsId = Approval.objects.filter(
                    documentId__documentStatus='완료',
                    documentId__securityLevel='B',
                ).values_list('documentId__documentId', flat=True)

                for documentId in tempDocumentsId:
                    document = Document.objects.get(documentId=documentId)
                    if document.preservationDate() > datetime.datetime.now():
                        documentsDoneView.append(documentId)

            # A등급 문서는 대표이사 조회
            if request.user.employee.empId <= 2:
                tempDocumentsId = Approval.objects.filter(
                    documentId__documentStatus='완료',
                    documentId__securityLevel='A',
                ).values_list('documentId__documentId', flat=True)

                for documentId in tempDocumentsId:
                    document = Document.objects.get(documentId=documentId)
                    if document.preservationDate() > datetime.datetime.now():
                        documentsDoneView.append(documentId)

            # 조회 문서 중 기존 문서에 있는 것은 제외
            documentsDoneView = list(
                set(documentsDoneView) - set(documentsDoneWrite) - set(documentsDoneApproval) - set(documentsDoneCheck) - set(documentsDoneReject)
            )

        # 임시문서
        if category == '임시':
            documentsTemp = list(Document.objects.filter(
                documentStatus='임시',
                writeEmp=request.user.employee
            ).values_list('documentId', flat=True))

        # option 적용
        if 'option' in request.GET.keys():
            option = request.GET['option']
            if category == '진행':
                if option == '결재완료':
                    documentsIngWait = []  # 진행, 결재대기
                    documentsIngWill = []  # 진행, 결재예정
                    documentsIngCheck = []  # 진행, 참조문서
                if option == '결재대기':
                    documentsIngDone = []  # 진행, 진행중
                    documentsIngWill = []  # 진행, 결재예정
                    documentsIngCheck = []  # 진행, 참조문서
                if option == '결재예정':
                    documentsIngDone = []  # 진행, 진행중
                    documentsIngWait = []  # 진행, 결재대기
                    documentsIngCheck = []  # 진행, 참조문서
                if option == '참조문서':
                    documentsIngDone = []  # 진행, 진행중
                    documentsIngWait = []  # 진행, 결재대기
                    documentsIngWill = []  # 진행, 결재예정
            if category == '완료':
                if option == '반려제외':
                    documentsDoneReject = []
                if option == '기안문서':
                    documentsDoneApproval = []  # 완료, 결재문서
                    documentsDoneCheck = []  # 완료, 참조문서
                    documentsDoneReject = []  # 완료, 반려문서
                    documentsDoneView = []  # 완료, 조회가능
                if option == '결재문서':
                    documentsDoneWrite = []  # 완료, 기안문서
                    documentsDoneCheck = []  # 완료, 참조문서
                    documentsDoneReject = []  # 완료, 반려문서
                    documentsDoneView = []  # 완료, 조회가능
                if option == '참조문서':
                    documentsDoneWrite = []  # 완료, 기안문서
                    documentsDoneApproval = []  # 완료, 결재문서
                    documentsDoneReject = []  # 완료, 반려문서
                    documentsDoneView = []  # 완료, 조회가능
                if option == '반려문서':
                    documentsDoneWrite = []  # 완료, 기안문서
                    documentsDoneApproval = []  # 완료, 결재문서
                    documentsDoneCheck = []  # 완료, 참조문서
                    documentsDoneView = []  # 완료, 조회가능
                if option == '조회문서':
                    documentsDoneWrite = []  # 완료, 기안문서
                    documentsDoneApproval = []  # 완료, 결재문서
                    documentsDoneCheck = []  # 완료, 참조문서
                    documentsDoneReject = []  # 완료, 반려문서

        # 관리자 조회
        if category == '관리자진행':
            documentsIng = list(Document.objects.filter(documentStatus='진행').values_list('documentId', flat=True))  # 진행 문서 전체
        if category == '관리자완료':
            documentsDone = list(Document.objects.filter(documentStatus='완료').values_list('documentId', flat=True))  # 완료 문서 전체
        if category == '관리자반려':
            documentsReject = list(Document.objects.filter(documentStatus='반려').values_list('documentId', flat=True))  # 반려 문서 전체

        # 각 문서 분류별 displayStatus 설정
        returnIngDone = Document.objects.filter(
            documentId__in=documentsIngDone
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('진행', output_field=CharField()),
            displayStatus2=Value('결재완료', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnIngWait = Document.objects.filter(
            documentId__in=documentsIngWait
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('진행', output_field=CharField()),
            displayStatus2=Value('결재대기', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnIngWill = Document.objects.filter(
            documentId__in=documentsIngWill
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('진행', output_field=CharField()),
            displayStatus2=Value('결재예정', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnIngCheck = Document.objects.filter(
            documentId__in=documentsIngCheck
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('진행', output_field=CharField()),
            displayStatus2=Value('참조문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnDoneWrite = Document.objects.filter(
            documentId__in=documentsDoneWrite
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('완료', output_field=CharField()),
            displayStatus2=Value('기안문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnDoneApproval = Document.objects.filter(
            documentId__in=documentsDoneApproval
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('완료', output_field=CharField()),
            displayStatus2=Value('결재문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnDoneCheck = Document.objects.filter(
            documentId__in=documentsDoneCheck
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('완료', output_field=CharField()),
            displayStatus2=Value('참조문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnDoneReject = Document.objects.filter(
            documentId__in=documentsDoneReject
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('완료', output_field=CharField()),
            displayStatus2=Value('반려문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnDoneView = Document.objects.filter(
            documentId__in=documentsDoneView
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('완료', output_field=CharField()),
            displayStatus2=Value('조회문서', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnTemp = Document.objects.filter(
            documentId__in=documentsTemp
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('임시', output_field=CharField()),
            displayStatus2=Value('임시', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnIng = Document.objects.filter(
            documentId__in=documentsIng
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('진행', output_field=CharField()),
            displayStatus2=Value('관리자', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnDone = Document.objects.filter(
            documentId__in=documentsDone
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('완료', output_field=CharField()),
            displayStatus2=Value('관리자', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        returnReject = Document.objects.filter(
            documentId__in=documentsReject
        ).annotate(
            empName=F('writeEmp__empName'),
            formNumber=F('formId__formNumber'),
            formTitle=F('formId__formTitle'),
            displayStatus1=Value('반려', output_field=CharField()),
            displayStatus2=Value('관리자', output_field=CharField())
        ).values(
            'documentId', 'documentNumber', 'title', 'empName', 'draftDatetime',
            'formNumber', 'formTitle', 'documentStatus', 'modifyDatetime', 'displayStatus1', 'displayStatus2'
        )
        
        returnDocuments = returnIngDone.union(
            returnIngWait, returnIngWill, returnIngCheck,
            returnDoneWrite, returnDoneApproval, returnDoneCheck, returnDoneReject, returnDoneView,
            returnTemp, returnIng, returnDone, returnReject
        )

        structure = json.dumps(list(returnDocuments), cls=DjangoJSONEncoder)
        return HttpResponse(structure, content_type='application/json')


@login_required
def show_document_all(request):
    context = {
        'category': '전체',
        'title': '전체 문서함',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_ing(request):
    context = {
        'category': '진행',
        'title': '진행 문서함',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_done(request):
    context = {
        'category': '완료',
        'title': '완료 문서함',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_temp(request):
    context = {
        'category': '임시',
        'title': '임시 문서함',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_admin_ing(request):
    context = {
        'category': '관리자진행',
        'title': '전체진행문서함 (관리자)',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_admin_done(request):
    context = {
        'category': '관리자완료',
        'title': '전체완료문서함 (관리자)',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def show_document_admin_reject(request):
    context = {
        'category': '관리자반려',
        'title': '전체반려문서함 (관리자)',
    }
    return render(request, 'approval/showdocument.html', context)


@login_required
def view_document(request, documentId):
    document = Document.objects.get(documentId=documentId)
    files = Documentfile.objects.filter(documentId__documentId=documentId)
    related = Relateddocument.objects.filter(documentId__documentId=documentId)
    apply, process, reference, approval, agreement, financial = template_format(documentId)
    whoApproval = who_approval(documentId)
    # 문서가 진행 중이고, 기안자 이외에 나머지 사람들이 결재를 하지 않았다면, 기안 취소 가능
    done_approval = whoApproval['done']
    if document.documentStatus == '진행' and len(done_approval) == 1 and done_approval[0] == request.user.employee.empId:
        draftCancelStatus = True
    else:
        draftCancelStatus = False
    # 결재할 사람
    do_approval = whoApproval['do']
    # 참조할 사람
    check_approval = whoApproval['check']

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
    email = AdminEmail.objects.filter(adminId=email['adminId__max']).first()

    # 댓글 정보
    comments = Documentcomment.objects.filter(documentId=document)

    context = {
        'document': document,
        'files': files,
        'related': related,
        'empNames': empNames,
        'approvalList': [apply, process, approval, agreement, financial],
        'reference': reference,
        'draftCancelStatus': draftCancelStatus,
        'do_approval': do_approval,
        'check_approval': check_approval,
        'email': email,
        'comments': comments,
    }
    return render(request, 'approval/viewdocument.html', context)


@login_required
def post_document_comment(request):
    document = Document.objects.get(documentId=request.POST['documentId'])
    comment = request.POST['comment']
    Documentcomment.objects.create(
        documentId=document,
        author=request.user.employee,
        comment=comment,
        created=datetime.datetime.now(),
        updated=datetime.datetime.now(),
    )
    return redirect('approval:viewdocument', request.POST['documentId'])


@login_required
def approve_document(request, approvalId):
    now = datetime.datetime.now()

    approval = Approval.objects.get(approvalId=approvalId)
    approval.approvalStatus = '완료'
    approval.approvalDatetime = now
    approval.save()

    if approval.approvalCategory != "참조":
        whoApproval = who_approval(approval.documentId_id)
        if len(whoApproval['do']) == 0:
            document = Document.objects.get(documentId=approval.documentId_id)
            document.documentStatus = '완료'
            document.approveDatetime = now
            document.save()

            # 결재 완료 메일
            employee = Employee.objects.get(empId=document.writeEmp_id)
            mail_approval(employee, document, "결재완료")

            if document.formId.formTitle == '휴가신청서':
                Vacation.objects.filter(documentId=document).update(vacationStatus='Y')

            # 계약 수정 권한
            if document.formId.formTitle == '수정권한요청서':
                contract = Contract.objects.get(contractId=document.contractId.contractId)
                contract.modifyContract = 'Y'
                contract.save()
        else:
            for empId in whoApproval['do']:
                employee = Employee.objects.get(empId=empId)
                document = Document.objects.get(documentId=approval.documentId_id)

                # 결재 요청 메일
                mail_approval(employee, document, "결재요청")

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

    # 계약 수정 권한
    if document.formId.formTitle == '수주통보서':
        contract = Contract.objects.get(contractId=document.contractId.contractId)
        contract.modifyContract = 'Y'
        contract.save()

    # 반려 메일
    employee = Employee.objects.get(empId=document.writeEmp_id)
    mail_approval(employee, document, "결재반려")

    approvals = Approval.objects.filter(Q(documentId=approval.documentId_id) & Q(approvalStatus='대기'))
    approvals.update(approvalStatus='정지')

    if document.formId.formTitle == '휴가신청서':
        vacations = Vacation.objects.filter(documentId=document)
        vacations.update(vacationStatus='R')
        vacationDay = 0
        for vacation in vacations:
            if vacation.vacationType == '일차':
                vacationDay += 1
            else:
                vacationDay += 0.5

        emp = document.writeEmp
        categoryName = vacations.first().vacationCategory.categoryName
        if categoryName == '연차':
            emp.empAnnualLeave += vacationDay
            emp.save()
        elif categoryName == '근속연차':
            emp.empSpecialLeave += vacationDay
            emp.save()
        elif categoryName == '금차':
            emp.empSpecialLeave2 += vacationDay
            emp.save()
        elif categoryName == '대체휴무':
            emp.empSpecialLeave3 += vacationDay
            emp.save()

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
    elif documentType == '수정권한요청':
        formTitle = '수정권한요청서'

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

    # 수주통보서
    lastOrderNoti = Document.objects.filter(contractId=contract, formId__formTitle='수주통보서', documentStatus='완료')
    if lastOrderNoti:
        maxDraftDatetime = lastOrderNoti.aggregate(Max('draftDatetime'))['draftDatetime__max']
        lastOrderNoti = lastOrderNoti.get(draftDatetime=maxDraftDatetime)
        orderPaper = '<a href="/approval/viewdocument/' + str(lastOrderNoti.documentId) + '">' + lastOrderNoti.title + '</a>'
    else:
        orderPaper = '수주통보서 없음.'

    # 확인서(confirmPaper)
    lastFile = files.filter(fileCategory='납품,구축,검수확인서')
    if lastFile:
        maxUploadDatetime = lastFile.aggregate(Max('uploadDatetime'))['uploadDatetime__max']
        lastFile = lastFile.get(uploadDatetime=maxUploadDatetime)
        confirmPaper = '<a href="/media/' + str(lastFile.file) + '" download>' + lastFile.fileName + '</a>'
    else:
        confirmPaper = '확인서 없음.'

    contentHtml = formId.formHtml

    # 1. 수주통보서
    if formTitle == '수주통보서':
        # N차 수정 수주통보서
        N = len(Document.objects.filter(
            formId__categoryId__firstCategory='영업',
            formId__categoryId__secondCategory='일반',
            formId__formTitle='수주통보서',
            documentStatus='완료',
            contractId=contractId,
        ))
        if N:
            formTitle = str(N) + '차 수정 수주통보서'
            contentHtml = contentHtml.replace('수주통보서', formTitle)

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
        contentHtml = contentHtml.replace('산업군판매유형자동입력', contract.saleIndustry + ' · ' + contract.saleType)
        contentHtml = contentHtml.replace('대분류소분류자동입력',  contract.mainCategory + ' · ' + contract.subCategory)
        contentHtml = contentHtml.replace('계약일자동입력', str(contract.contractDate))
        if contract.contractStartDate or contract.contractEndDate:
            contentHtml = contentHtml.replace(
                '계약기간자동입력', str(contract.contractStartDate) + '~' + str(contract.contractEndDate)
            )
        else:
            contentHtml = contentHtml.replace('계약기간자동입력', '-')
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
        cogSummary = summary(contractId)
        contentHtml = contentHtml.replace('매출금액자동입력', intcomma(cogSummary['summaryRevenues']))
        contentHtml = contentHtml.replace('매출합계자동입력', intcomma(cogSummary['summaryRevenues']))
        contentHtml = contentHtml.replace('마진금액자동입력', intcomma(cogSummary['summaryProfit']))
        contentHtml = contentHtml.replace('마진합계자동입력', intcomma(cogSummary['summaryProfit']))
        contentHtml = contentHtml.replace('매입합계자동입력', intcomma(cogSummary['summaryPurchases']))

        contentHtml = contentHtml.replace('상품매입금액자동입력', intcomma(cogSummary['summaryProduct']))
        contentHtml = contentHtml.replace('유지보수매입금액자동입력', intcomma(cogSummary['summaryMaintenance']))
        contentHtml = contentHtml.replace('인력지원매입금액자동입력', intcomma(cogSummary['summarySupport']))
        contentHtml = contentHtml.replace('기타매입금액자동입력', intcomma(cogSummary['summaryEtc']))

        # 마진율분석
        contentHtml = contentHtml.replace('마진율자동입력', str(profitRatio) + '%')
        if (profitRatio - 15) > 0:
            contentHtml = contentHtml.replace('마진분석결과자동입력', '<span style="color: red;">' + str(profitRatio-15) + '%</span>')
        else:
            contentHtml = contentHtml.replace('마진분석결과자동입력', '<span style="color: blue;">' + str(profitRatio - 15) + '%</span>')

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
            if contract.saleTaxCustomerId.customerName:
                contentHtml = contentHtml.replace('세금담당자이름자동입력', contract.saleTaxCustomerId.customerName)
            else:
                contentHtml = contentHtml.replace('세금담당자이름자동입력', '-')
            if contract.saleTaxCustomerId.customerPhone:
                contentHtml = contentHtml.replace('세금담당자연락처자동입력', contract.saleTaxCustomerId.customerPhone)
            else:
                contentHtml = contentHtml.replace('세금담당자연락처자동입력', '-')
            if contract.saleTaxCustomerId.customerEmail:
                contentHtml = contentHtml.replace('세금담당자이메일자동입력', contract.saleTaxCustomerId.customerEmail)
            else:
                contentHtml = contentHtml.replace('세금담당자이메일자동입력', '-')
        else:
            contentHtml = contentHtml.replace('세금담당자이름자동입력', '')
            contentHtml = contentHtml.replace('세금담당자연락처자동입력', '')
            contentHtml = contentHtml.replace('세금담당자이메일자동입력', '')

        # 매출 매입 세부사항
        revenueItem = Contractitem.objects.filter(Q(contractId=contractId))
        purchaseItem = Purchasecontractitem.objects.filter(Q(contractId=contractId))

        if revenueItem:
            tempStr = ''
            sumRevenue = 0
            for item in revenueItem:
                sumRevenue += item.itemPrice
                if item.companyName:
                    companyName = item.companyName.companyNameKo
                else:
                    companyName = '-'
                tempStr += '''<tr style="height: 25px; font-size: 14px;">
                    <td style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + '매출' + '''</td>
                    <td style="text-align: left; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + companyName + '''</td>
                    <td style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + item.mainCategory + '''</td>
                    <td style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + item.subCategory + '''</td>
                    <td style="text-align: left; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + item.itemName + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + format(item.itemPrice, ',') + '''</td>
                </tr>'''
            tempStr += '''<tr style="height: 25px; font-size: 14px;">
                <td colspan="5" style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + 'TOTAL' + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                ''' + format(sumRevenue, ',') + '''</td>
            </tr>'''
            contentHtml = contentHtml.replace('<tr><td colspan="6">매출세부사항자동입력</td></tr>', tempStr)
        else:
            contentHtml = contentHtml.replace('<tr><td colspan="6">매출세부사항자동입력</td></tr>', '<tr><td colspan="6">매출세부사항없음</td></tr>')

        if purchaseItem:
            tempStr = ''
            sumPurchase = 0
            for item in purchaseItem:
                sumPurchase += item.itemPrice
                if item.companyName:
                    companyName = item.companyName.companyNameKo
                else:
                    companyName = '-'
                tempStr += '''<tr style="height: 25px; font-size: 14px;">
                    <td style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + '매입' + '''</td>
                    <td style="text-align: left; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + companyName + '''</td>
                    <td style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + item.mainCategory + '''</td>
                    <td style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + item.subCategory + '''</td>
                    <td style="text-align: left; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + item.itemName + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                    ''' + format(item.itemPrice, ',') + '''</td>
                </tr>'''
            tempStr += '''<tr style="height: 25px; font-size: 14px;">
                <td colspan="5" style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + 'TOTAL' + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">
                ''' + format(sumPurchase, ',') + '''</td>
            </tr>'''
            contentHtml = contentHtml.replace('<tr><td colspan="6">매입세부사항자동입력</td></tr>', tempStr)
        else:
            contentHtml = contentHtml.replace('<tr><td colspan="6">매입세부사항자동입력</td></tr>', '<tr><td colspan="6">매입세부사항없음</td></tr>')

        # Billing Schedule
        if len(purchases) > 0 or len(revenues) > 0:
            if len(purchases) == 0:
                pMinYear = {'predictBillingDate__year__min': datetime.date(2999, 12, 31)}
                pMaxYear = {'predictBillingDate__year__max': datetime.date(1999, 12, 31)}
            else:
                pMinYear = purchases.aggregate(Min('predictBillingDate__year'))
                pMaxYear = purchases.aggregate(Max('predictBillingDate__year'))
            if len(revenues) == 0:
                rMinYear = {'predictBillingDate__year__min': datetime.date(2999, 12, 31)}
                rMaxYear = {'predictBillingDate__year__max': datetime.date(1999, 12, 31)}
            else:
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

            yearList = []
            for y in range(minYear['predictBillingDate__year__min'].year, maxYear['predictBillingDate__year__max'].year + 1):
                yearList.append(y)

            monthList = []
            for y in yearList:
                dateList = []
                for d in range(1, 13):
                    dateList.append('{}-{}'.format(y, str(d).zfill(2)))
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
            tempStr += '<tr><td><table width="100%" style="border-collapse: collapse">'
            # 구분, 업체명, 날짜
            tempStr += '''
              <tr style="height: 25px; font-size: 11px;">
                <td style="text-align: center; background-color: #ebfaff; border: 1px solid grey; padding-left: 10px; padding-right: 10px;" width="6%">구분</td>
                <td style="text-align: center; background-color: #ebfaff; border: 1px solid grey; padding-left: 10px; padding-right: 10px;" width="16%">업체명</td>
            '''
            for month in year:
                tempStr += '''
                <td style="text-align: center; background-color: #ebfaff; border: 1px solid grey; padding-left: 10px; padding-right: 10px;" width="6%">''' + str(month) + '''</td>
                '''
            tempStr += '''
                <td style="text-align: center; background-color: #ebfaff; border: 1px solid grey; padding-left: 10px; padding-right: 10px;" width="6%">TOTAL</td>
              </tr>
            '''
            # 업체별 매출
            for billing in rBillingSchedule:
                if billing['list'] == year:
                    tempStr += '''
              <tr style="height: 25px; font-size: 11px;">
                <td style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">매출</td>
                <td style="text-align: left; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + billing['name'] + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['1']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['2']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['3']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['4']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['5']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['6']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['7']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['8']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['9']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['10']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['11']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['12']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                ''' + intcomma(billing['sum']) + '''</td>
              </tr>
                    '''
            # 매출 총합
            for sumBilling in sumrBillingSchedule:
                if sumBilling['list'] == year:
                    tempStr += '''
              <tr style="height: 25px; font-size: 11px;">
                <td colspan="2" style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">TOTAL</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['1']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['2']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['3']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['4']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['5']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['6']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['7']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['8']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['9']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['10']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['11']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['12']) + '''</td>
                <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro;">
                ''' + intcomma(sumBilling['sum']) + '''</td>
              </tr>
                    '''
            if pBillingSchedule:
                # 업체별 매입
                for billing in pBillingSchedule:
                    if billing['list'] == year:
                        tempStr += '''
                  <tr style="height: 25px; font-size: 11px;">
                    <td style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">매입</td>
                    <td style="text-align: left; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + billing['name'] + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['1']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['2']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['3']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['4']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['5']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['6']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['7']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['8']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['9']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['10']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['11']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px;">''' + intcomma(billing['12']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(billing['sum']) + '''</td>
                  </tr>
                        '''
                # 매입총합
                for sumBilling in sumpBillingSchedule:
                    if sumBilling['list'] == year:
                        tempStr += '''
                  <tr style="height: 25px; font-size: 11px; margin-bottom: 5px">
                    <td colspan="2" style="text-align: center; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">TOTAL</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['1']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['2']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['3']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['4']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['5']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['6']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['7']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['8']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['9']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['10']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['11']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
                    ''' + intcomma(sumBilling['12']) + '''</td>
                    <td style="text-align: right; border: 1px solid grey; padding-left: 10px; padding-right: 10px; background-color: gainsboro">
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
        if purchaseCompany:
            contentHtml = contentHtml.replace('매입처자동입력', purchaseCompany)
        else:
            contentHtml = contentHtml.replace('매입처자동입력', '')
        if purchasePrice:
            contentHtml = contentHtml.replace('매입액자동입력', format(purchasePrice, ',') + '원')
        else:
            contentHtml = contentHtml.replace('매입액자동입력', '')
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

    # 4. 수정권한 요청서
    if formTitle == '수정권한요청서':
        contentHtml = contentHtml.replace('계약명자동입력', contractName)


    # 문서 등록
    document = Document.objects.create(
        documentNumber=documentNumber,
        writeEmp=request.user.employee,
        formId=formId,
        preservationYear=formId.preservationYear,
        securityLevel=formId.securityLevel,
        title='[' + contract.contractName + '] ' + formTitle + ' 결재',
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
    if returnIngWait['empName__count']:
        result = returnIngWait['empName__count']
    else:
        result = 0
    structure = json.dumps(result, cls=DjangoJSONEncoder)
    return HttpResponse(structure, content_type='application/json')


@login_required
def delete_comment(request, commentId):
    comment = Documentcomment.objects.get(commentId=commentId)
    documentId = comment.documentId.documentId
    comment.delete()
    return redirect("approval:viewdocument", documentId)
