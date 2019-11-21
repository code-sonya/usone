from .models import Approvalform, Approval
from django.db.models import Q, Min, Max

from .models import Approvalform, Approval
from service.models import Employee
from django.db.models import Q


def data_format(formId, user):
    approvalform = Approvalform.objects.filter(Q(formId=formId))
    apply = approvalform.filter(approvalCategory='신청').values('approvalEmp')
    process = approvalform.filter(approvalCategory='승인').values('approvalEmp')
    reference = approvalform.filter(approvalCategory='참조').values('approvalEmp')
    approval = approvalform.filter(approvalCategory='결재').values('approvalEmp')
    agreement = approvalform.filter(approvalCategory='합의').values('approvalEmp')
    financial = approvalform.filter(approvalCategory='재무합의').values('approvalEmp')
    employee = Employee.objects.get(user=user)
    empId = str(employee.empId)
    if apply:
        applylst = []
        for a in apply:
            applylst.append(str(a['approvalEmp']))
        if empId in applylst:
            applylst.remove(empId)
        applylst.insert(0, empId)
        apply = ','.join(applylst)
    else:
        apply = [empId]
    if process:
        processlst = []
        for a in process:
            processlst.append(str(a['approvalEmp']))
        if empId in processlst:
            processlst.remove(empId)
        process = ','.join(processlst)
    if reference:
        referencelst = []
        for a in reference:
            referencelst.append(str(a['approvalEmp']))
        if empId in referencelst:
            referencelst.remove(empId)
        reference = ','.join(referencelst)
    if approval:
        approvallst = []
        for a in approval:
            approvallst.append(str(a['approvalEmp']))
        if empId in approvallst:
            approvallst.remove(empId)
        approvallst.insert(0, empId)
        approval = ','.join(approvallst)
    else:
        approval = [empId]
    if agreement:
        agreementlst = []
        for a in agreement:
            agreementlst.append(str(a['approvalEmp']))
        if empId in agreementlst:
            agreementlst.remove(empId)
        agreement = ','.join(agreementlst)
    if financial:
        financiallst = []
        for a in financial:
            financiallst.append(str(a['approvalEmp']))
        if empId in financiallst:
            financiallst.remove(empId)
        financial = ','.join(financiallst)

    return apply, process, reference, approval, agreement, financial


def who_approval(documentId):
    # 결재 한 사람(done), 결재 차례(do), 나중에 결재(will)
    done = []
    do = []
    will = []
    check = []

    # 문서의 결재들
    approvals = Approval.objects.filter(documentId__documentId=documentId)

    # 1. 신청(apply) -> 승인(process)
    apply = approvals.filter(approvalCategory='신청')

    if apply:
        process = approvals.filter(approvalCategory='승인')

        # 완료 (done)
        for a in apply.filter(approvalStatus='완료'):
            done.append(a.approvalEmp.empId)
        for p in process.filter(approvalStatus='완료'):
            done.append(p.approvalEmp.empId)

        # 신청 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
        if apply.filter(approvalStatus='대기'):
            minStep = apply.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
            do.append(apply.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)
            # minStep 뒷사람들은 예정 (will)
            for a in apply.filter(approvalStatus='대기', approvalStep__gt=minStep):
                will.append(a.approvalEmp.empId)
            for p in process.filter(approvalStatus='대기'):
                will.append(p.approvalEmp.empId)

        # 승인 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
        elif process.filter(approvalStatus='대기'):
            minStep = process.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
            do.append(process.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)
            # minStep 뒷사람들은 예정 (will)
            for p in process.filter(approvalStatus='대기', approvalStep__gt=minStep):
                will.append(p.approvalEmp.empId)

    # 2. 결재(initApproval) -> 합의(agreement) -> 재무합의(financial) -> 최종결재(finalApproval)
    approval = approvals.filter(approvalCategory='결재')

    if approval:
        approvalMaxStep = approval.aggregate(Max('approvalStep'))['approvalStep__max']
        initApproval = approval.exclude(approvalStep=approvalMaxStep)
        agreement = approvals.filter(approvalCategory='합의')
        financial = approvals.filter(approvalCategory='재무합의')
        finalApproval = approval.get(approvalStep=approvalMaxStep)

        # 완료 (done)
        for a in approval.filter(approvalStatus='완료'):
            done.append(a.approvalEmp.empId)
        for a in agreement.filter(approvalStatus='완료'):
            done.append(a.approvalEmp.empId)
        for f in financial.filter(approvalStatus='완료'):
            done.append(f.approvalEmp.empId)
        if finalApproval.approvalStatus == '완료':
            done.append(finalApproval.approvalEmp.empId)

        # 결재 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
        if initApproval.filter(approvalStatus='대기'):
            minStep = initApproval.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
            do.append(initApproval.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)
            # minStep 뒷사람들은 예정 (will)
            for a in initApproval.filter(approvalStatus='대기', approvalStep__gt=minStep):
                will.append(a.approvalEmp.empId)
            for a in agreement.filter(approvalStatus='대기'):
                will.append(a.approvalEmp.empId)
            for f in financial.filter(approvalStatus='대기'):
                will.append(f.approvalEmp.empId)
            will.append(finalApproval.approvalEmp.empId)

        # 승인 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
        elif agreement.filter(approvalStatus='대기') or financial.filter(approvalStatus='대기'):
            if agreement.filter(approvalStatus='대기'):
                minStep = agreement.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
                do.append(agreement.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)
                # minStep 뒷사람들은 예정 (will)
                for a in agreement.filter(approvalStatus='대기', approvalStep__gt=minStep):
                    will.append(a.approvalEmp.empId)

            if financial.filter(approvalStatus='대기'):
                minStep = financial.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
                do.append(financial.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)
                # minStep 뒷사람들은 예정 (will)
                for f in financial.filter(approvalStatus='대기', approvalStep__gt=minStep):
                    will.append(f.approvalEmp.empId)

            will.append(finalApproval.approvalEmp.empId)

        elif finalApproval.approvalStatus == '대기':
            do.append(finalApproval.approvalEmp.empId)

    # 3. 참조
    reference = approvals.filter(approvalCategory='참조')

    for r in reference:
        if r.approvalStatus == '완료':
            done.append(r.approvalEmp.empId)
        if r.approvalStatus == '대기':
            check.append(r.approvalEmp.empId)

    return {'done': done, 'do': do, 'will': will, 'check': check}


def template_format(documentId):
    approvals = Approval.objects.filter(Q(documentId__documentId=documentId))
    apply = approvals.filter(approvalCategory='신청')\
        .order_by('approvalStep')\
        .values('approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    process = approvals.filter(approvalCategory='승인')\
        .order_by('approvalStep')\
        .values('approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    reference = approvals.filter(approvalCategory='참조')\
        .order_by('approvalStep')\
        .values('approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    approval = approvals.filter(approvalCategory='결재')\
        .order_by('approvalStep')\
        .values('approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    agreement = approvals.filter(approvalCategory='합의')\
        .order_by('approvalStep')\
        .values('approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')
    financial = approvals.filter(approvalCategory='재무합의')\
        .order_by('approvalStep')\
        .values('approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime')

    if apply:
        applylst = []
        for a in apply:
            applylst.append(a)
        if len(apply) % 9 != 0:
            for i in range(9-(len(apply) % 9)):
                applylst.append({})
        apply = [{'name': '신청', 'data': applylst}]
    else:
        apply = [{'name': '신청', 'data': [{} for i in range(9)]}]
    if process:
        processlst = []
        for p in process:
            processlst.append(p)
        if len(process) % 9 != 0:
            for i in range(9-(len(process) % 9)):
                processlst.append({})
        process = [{'name': '승인', 'data': processlst}]
    else:
        process = [{'name': '승인', 'data': [{} for i in range(9)]}]
    if reference:
        referencelst = []
        for r in reference:
            referencelst.append(r)
        if len(reference) % 9 != 0:
            for i in range(9-(len(reference) % 9)):
                referencelst.append({})
        reference = [{'name': '참조', 'data': referencelst}]
    else:
        reference = [{'name': '참조', 'data': [{} for i in range(9)]}]

    if approval:
        approvallst = []
        for a in approval:
            approvallst.append(a)
        if len(approval) % 9 != 0:
            for i in range(9-(len(approval) % 9)):
                approvallst.append({})
        approval = [{'name': '결재', 'data': approvallst}]
    else:
        approval = [{'name': '결재', 'data': [{} for i in range(9)]}]

    if agreement:
        agreementlst = []
        for a in agreement:
            agreementlst.append(a)
        if len(agreement) % 9 != 0:
            for i in range(9-(len(agreement) % 9)):
                agreementlst.append({})
        agreement = [{'name': '합의', 'data': agreementlst}]
    else:
        agreement = [{'name': '합의', 'data': [{} for i in range(9)]}]
    if financial:
        financiallst = []
        for f in financial:
            financiallst.append(f)
        if len(financial) % 9 != 0:
            for i in range(9-(len(financial) % 9)):
                financiallst.append({})
        financial = [{'name': '재무합의', 'data': financiallst}]
    else:
        financial = [{'name': '재무합의', 'data': [{} for i in range(9)]}]


    return apply, process, reference, approval, agreement, financial
