
from .models import Approvalform, Approval
from django.db.models import Q
def data_format(formId):
    approvalform = Approvalform.objects.filter(Q(formId=formId))
    apply, process, reference, approval, agreement, financial = approvalform.filter(approvalCategory='신청').values('approvalEmp'), \
                                                                approvalform.filter(approvalCategory='승인').values('approvalEmp'), \
                                                                approvalform.filter(approvalCategory='참조').values('approvalEmp'), \
                                                                approvalform.filter(approvalCategory='결재').values('approvalEmp'), \
                                                                approvalform.filter(approvalCategory='합의').values('approvalEmp'), \
                                                                approvalform.filter(approvalCategory='재무합의').values('approvalEmp')
    if apply:
        applylst = []
        for a in apply:
            applylst.append(str(a['approvalEmp']))

        apply = ','.join(applylst)
    if process:
        processlst = []
        for a in process:
            processlst.append(str(a['approvalEmp']))
        process = ','.join(processlst)
    if reference:
        referencelst = []
        for a in reference:
            referencelst.append(str(a['approvalEmp']))

        reference = ','.join(referencelst)
    if approval:
        approvallst = []
        for a in approval:
            approvallst.append(str(a['approvalEmp']))

        approval = ','.join(approvallst)
    if agreement:
        agreementlst = []
        for a in agreement:
            agreementlst.append(str(a['approvalEmp']))

        agreement = ','.join(agreementlst)
    if financial:
        financiallst = []
        for a in financial:
            financiallst.append(str(a['approvalEmp']))

        financial = ','.join(financiallst)

    return apply, process, reference, approval, agreement, financial

def template_format(documentId):
    approvals = Approval.objects.filter(Q(documentId__documentId=documentId))
    apply = approvals.filter(approvalCategory='신청')\
        .order_by('approvalStep')\
        .values('approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    process = approvals.filter(approvalCategory='승인')\
        .order_by('approvalStep')\
        .values('approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    reference = approvals.filter(approvalCategory='참조')\
        .order_by('approvalStep')\
        .values('approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    approval = approvals.filter(approvalCategory='결재')\
        .order_by('approvalStep')\
        .values('approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    agreement = approvals.filter(approvalCategory='합의')\
        .order_by('approvalStep')\
        .values('approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    financial = approvals.filter(approvalCategory='재무합의')\
        .order_by('approvalStep')\
        .values('approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')

    print(apply, process, reference, approval, agreement, financial)
    if apply:
        applylst = []
        for a in apply:
            applylst.append(a)
        if len(apply) % 9 != 0:
            for i in range(9-(len(apply) % 9)):
                applylst.append({})
        apply = applylst
    if process:
        processlst = []
        for p in process:
            processlst.append(p)
        if len(process) % 9 != 0:
            for i in range(9-(len(process) % 9)):
                processlst.append({})
        process = processlst
    if reference:
        referencelst = []
        for r in reference:
            referencelst.append(r)
        if len(reference) % 9 != 0:
            for i in range(9-(len(reference) % 9)):
                referencelst.append({})
        reference = referencelst
    if approval:
        approvallst = []
        for a in approval:
            approvallst.append(a)
        if len(approval) % 9 != 0:
            for i in range(9-(len(approval) % 9)):
                approvallst.append({})
        approval = approvallst
    if agreement:
        agreementlst = []
        for a in agreement:
            agreementlst.append(a)
        if len(agreement) % 9 != 0:
            for i in range(9-(len(agreement) % 9)):
                agreementlst.append({})
        agreement = agreementlst
    if financial:
        financiallst = []
        for f in financial:
            financiallst.append(f)
        if len(financial) % 9 != 0:
            for i in range(9-(len(financial) % 9)):
                financiallst.append({})
        financial = financiallst

    return apply, process, reference, approval, agreement, financial

