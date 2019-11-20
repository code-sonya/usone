
from .models import Approvalform
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
