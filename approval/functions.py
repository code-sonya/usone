from .models import Approvalform, Approval
from django.db.models import Q, Min, Max

from .models import Approvalform, Approval, Documentfile
from service.models import Employee
from hr.models import AdminEmail
from django.db.models import Q
import smtplib
from email import encoders
from smtplib import SMTP_SSL
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from django.template import loader


def data_format(ID, user, approvalFormat, document, model):
    if model == "approvalform":
        approvalform = Approvalform.objects.filter(Q(formId=ID))
        apply = approvalform.filter(approvalCategory='신청').values('approvalEmp')
        process = approvalform.filter(approvalCategory='승인').values('approvalEmp')
        reference = approvalform.filter(approvalCategory='참조').values('approvalEmp')
        approval = approvalform.filter(approvalCategory='결재').values('approvalEmp')
        agreement = approvalform.filter(approvalCategory='합의').values('approvalEmp')
        financial = approvalform.filter(approvalCategory='재무합의').values('approvalEmp')
    elif model == "approval":
        approvals = Approval.objects.filter(Q(documentId=ID))
        apply = approvals.filter(approvalCategory='신청').values('approvalEmp')
        process = approvals.filter(approvalCategory='승인').values('approvalEmp')
        reference = approvals.filter(approvalCategory='참조').values('approvalEmp')
        approval = approvals.filter(approvalCategory='결재').values('approvalEmp')
        agreement = approvals.filter(approvalCategory='합의').values('approvalEmp')
        financial = approvals.filter(approvalCategory='재무합의').values('approvalEmp')
    else:
        apply = ''
        process = ''
        reference = ''
        approval = ''
        agreement = ''
        financial = ''

    employee = Employee.objects.get(user=user)
    empId = str(employee.empId)
    if apply:
        applylst = []
        for a in apply:
            applylst.append(str(a['approvalEmp']))
        if document == 'Y':
            if empId in applylst:
                applylst.remove(empId)
            applylst.insert(0, empId)
        apply = ','.join(applylst)
    else:
        if approvalFormat == '신청' and document == 'Y':
            apply = empId
    if process:
        processlst = []
        for a in process:
            processlst.append(str(a['approvalEmp']))
        if document == 'Y':
            if empId in processlst:
                processlst.remove(empId)
        process = ','.join(processlst)
    if reference:
        referencelst = []
        for a in reference:
            referencelst.append(str(a['approvalEmp']))
        if document == 'Y':
            if empId in referencelst:
                referencelst.remove(empId)
        reference = ','.join(referencelst)
    if approval:
        approvallst = []
        for a in approval:
            approvallst.append(str(a['approvalEmp']))
        if document == 'Y':
            if empId in approvallst:
                approvallst.remove(empId)
            approvallst.insert(0, empId)
        approval = ','.join(approvallst)
    else:
        if approvalFormat == '결재' and document == 'Y':
            approval = empId
    if agreement:
        agreementlst = []
        for a in agreement:
            agreementlst.append(str(a['approvalEmp']))
        if document == 'Y':
            if empId in agreementlst:
                agreementlst.remove(empId)
        agreement = ','.join(agreementlst)
    if financial:
        financiallst = []
        for a in financial:
            financiallst.append(str(a['approvalEmp']))
        if document == 'Y':
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

    # 2. 기안(initApproval) -> 합의(agreement) -> 재무합의(financial) -> 결재(finalApproval)
    # approval = approvals.filter(approvalCategory='결재')
    #
    # if approval:
    #     approvalMinStep = approval.aggregate(Min('approvalStep'))['approvalStep__min']
    #     initApproval = approval.filter(approvalStep=approvalMinStep)
    #     agreement = approvals.filter(approvalCategory='합의')
    #     financial = approvals.filter(approvalCategory='재무합의')
    #     finalApproval = approval.exclude(approvalStep=approvalMinStep)
    #
    #     # 완료 (done)
    #     for a in approval.filter(approvalStatus='완료'):
    #         done.append(a.approvalEmp.empId)
    #     for a in agreement.filter(approvalStatus='완료'):
    #         done.append(a.approvalEmp.empId)
    #     for f in financial.filter(approvalStatus='완료'):
    #         done.append(f.approvalEmp.empId)
    #
    #     # 기안자가 기안시 결재가 안됐을 경우, 기안자가 결재 차례 (이 상태가 오면 버그임.)
    #     if initApproval.filter(approvalStatus='대기'):
    #         minStep = initApproval.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
    #         do.append(initApproval.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)
    #
    #         # minStep 뒷사람들은 예정 (will)
    #         for i in initApproval.filter(approvalStatus='대기', approvalStep__gt=minStep):
    #             will.append(i.approvalEmp.empId)
    #         for a in agreement.filter(approvalStatus='대기'):
    #             will.append(a.approvalEmp.empId)
    #         for f in financial.filter(approvalStatus='대기'):
    #             will.append(f.approvalEmp.empId)
    #         for f in finalApproval.filter(approvalStatus='대기'):
    #             will.append(f.approvalEmp.empId)
    #
    #     # 합의 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
    #     elif agreement.filter(approvalStatus='대기'):
    #         minStep = agreement.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
    #         do.append(agreement.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)
    #
    #         # minStep 뒷사람들은 예정 (will)
    #         for a in agreement.filter(approvalStatus='대기', approvalStep__gt=minStep):
    #             will.append(a.approvalEmp.empId)
    #         for f in financial.filter(approvalStatus='대기'):
    #             will.append(f.approvalEmp.empId)
    #         for f in finalApproval.filter(approvalStatus='대기'):
    #             will.append(f.approvalEmp.empId)
    #
    #     # 재무합의 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
    #     elif financial.filter(approvalStatus='대기'):
    #         minStep = financial.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
    #         do.append(financial.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)
    #
    #         # minStep 뒷사람들은 예정 (will)
    #         for f in financial.filter(approvalStatus='대기', approvalStep__gt=minStep):
    #             will.append(f.approvalEmp.empId)
    #         for f in finalApproval.filter(approvalStatus='대기'):
    #             will.append(f.approvalEmp.empId)
    #
    #     # 결재 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
    #     elif finalApproval.filter(approvalStatus='대기'):
    #         minStep = finalApproval.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
    #         do.append(finalApproval.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)
    #
    #         # minStep 뒷사람들은 예정 (will)
    #         for f in finalApproval.filter(approvalStatus='대기'):
    #             will.append(f.approvalEmp.empId)

    # 2. 기안(initApproval) -> 합의(agreement) -> 나머지결재(otherApproval) -> 재무합의(financial) -> 최종결재(finalApproval)
    approval = approvals.filter(approvalCategory='결재')

    if approval:
        approvalMinStep = approval.aggregate(Min('approvalStep'))['approvalStep__min']
        approvalMaxStep = approval.aggregate(Max('approvalStep'))['approvalStep__max']

        initApproval = approval.filter(approvalStep=approvalMinStep)
        agreement = approvals.filter(approvalCategory='합의')
        otherApproval = approval.exclude(approvalStep=approvalMinStep).exclude(approvalStep=approvalMaxStep)
        financial = approvals.filter(approvalCategory='재무합의')
        finalApproval = approval.filter(approvalStep=approvalMaxStep)

        # 완료 (done)
        for a in approval.filter(approvalStatus='완료'):
            done.append(a.approvalEmp.empId)
        for a in agreement.filter(approvalStatus='완료'):
            done.append(a.approvalEmp.empId)
        for f in financial.filter(approvalStatus='완료'):
            done.append(f.approvalEmp.empId)

        # 기안자가 기안시 결재가 안됐을 경우, 기안자가 결재 차례 (이 상태가 오면 버그임.)
        if initApproval.filter(approvalStatus='대기'):
            minStep = initApproval.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
            do.append(initApproval.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)

            # minStep 뒷사람들은 예정 (will)
            for i in initApproval.filter(approvalStatus='대기', approvalStep__gt=minStep):
                will.append(i.approvalEmp.empId)
            for a in agreement.filter(approvalStatus='대기'):
                will.append(a.approvalEmp.empId)
            for o in otherApproval.filter(approvalStatus='대기'):
                will.append(o.approvalEmp.empId)
            for f in financial.filter(approvalStatus='대기'):
                will.append(f.approvalEmp.empId)
            for f in finalApproval.filter(approvalStatus='대기'):
                will.append(f.approvalEmp.empId)

        # 합의 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
        elif agreement.filter(approvalStatus='대기'):
            minStep = agreement.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
            do.append(agreement.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)

            # minStep 뒷사람들은 예정 (will)
            for a in agreement.filter(approvalStatus='대기', approvalStep__gt=minStep):
                will.append(a.approvalEmp.empId)
            for o in otherApproval.filter(approvalStatus='대기'):
                will.append(o.approvalEmp.empId)
            for f in financial.filter(approvalStatus='대기'):
                will.append(f.approvalEmp.empId)
            for f in finalApproval.filter(approvalStatus='대기'):
                will.append(f.approvalEmp.empId)

        # 나머지결재 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
        elif otherApproval.filter(approvalStatus='대기'):
            minStep = otherApproval.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
            do.append(otherApproval.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)

            # minStep 뒷사람들은 예정 (will)
            for o in otherApproval.filter(approvalStatus='대기', approvalStep__gt=minStep):
                will.append(o.approvalEmp.empId)
            for f in financial.filter(approvalStatus='대기'):
                will.append(f.approvalEmp.empId)
            for f in finalApproval.filter(approvalStatus='대기'):
                will.append(f.approvalEmp.empId)

        # 재무합의 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
        elif financial.filter(approvalStatus='대기'):
            minStep = financial.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
            do.append(financial.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)

            # minStep 뒷사람들은 예정 (will)
            for f in financial.filter(approvalStatus='대기', approvalStep__gt=minStep):
                will.append(f.approvalEmp.empId)
            for f in finalApproval.filter(approvalStatus='대기'):
                will.append(f.approvalEmp.empId)

        # 결재 중 대기가 있는 경우, 대기 인원 중 step 가장 작은 사람이 결재 차례 (do)
        elif finalApproval.filter(approvalStatus='대기'):
            minStep = finalApproval.filter(approvalStatus='대기').aggregate(Min('approvalStep'))['approvalStep__min']
            do.append(finalApproval.get(approvalStatus='대기', approvalStep=minStep).approvalEmp.empId)

            # minStep 뒷사람들은 예정 (will)
            for f in finalApproval.filter(approvalStatus='대기'):
                will.append(f.approvalEmp.empId)

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
    apply = approvals.filter(approvalCategory='신청').order_by('approvalStep').values(
        'approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalEmp__empStamp',
        'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime'
    )
    process = approvals.filter(approvalCategory='승인').order_by('approvalStep').values(
        'approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalEmp__empStamp',
        'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime'
    )
    reference = approvals.filter(approvalCategory='참조').order_by('approvalStep').values(
        'approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalEmp__empStamp',
        'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime'
    )
    approval = approvals.filter(approvalCategory='결재').order_by('approvalStep').values(
        'approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalEmp__empStamp',
        'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime'
    )
    agreement = approvals.filter(approvalCategory='합의').order_by('approvalStep').values(
        'approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalEmp__empStamp',
        'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime'
    )
    financial = approvals.filter(approvalCategory='재무합의').order_by('approvalStep').values(
        'approvalId', 'approvalEmp', 'approvalEmp__empName', 'approvalEmp__empPosition__positionName', 'approvalEmp__empStamp',
        'approvalStep', 'approvalCategory', 'approvalStatus', 'approvalDatetime'
    )

    if apply:
        applylst = []
        for a in apply:
            applylst.append(a)
        if len(apply) % 9 != 0:
            for i in range(9 - (len(apply) % 9)):
                applylst.append({})
        apply = [{'name': '신청', 'data': applylst, 'count': len(apply)}]
    else:
        apply = [{'name': '신청', 'data': [{} for i in range(9)], 'count': 0}]
    if process:
        processlst = []
        for p in process:
            processlst.append(p)
        if len(process) % 9 != 0:
            for i in range(9 - (len(process) % 9)):
                processlst.append({})
        process = [{'name': '승인', 'data': processlst, 'count': len(process)}]
    else:
        process = [{'name': '승인', 'data': [{} for i in range(9)], 'count': 0}]
    if reference:
        referencelst = []
        for r in reference:
            referencelst.append(r)
        if len(reference) % 9 != 0:
            for i in range(9 - (len(reference) % 9)):
                referencelst.append({})
        reference = [{'name': '참조', 'data': referencelst, 'count': len(reference)}]
    else:
        reference = [{'name': '참조', 'data': [{} for i in range(9)], 'count': 0}]

    if approval:
        approvallst = []
        for a in approval:
            approvallst.append(a)
        if len(approval) % 9 != 0:
            for i in range(9 - (len(approval) % 9)):
                approvallst.append({})
        approval = [{'name': '결재', 'data': approvallst, 'count': len(approval)}]
    else:
        approval = [{'name': '결재', 'data': [{} for i in range(9)], 'count': 0}]

    if agreement:
        agreementlst = []
        for a in agreement:
            agreementlst.append(a)
        if len(agreement) % 9 != 0:
            for i in range(9 - (len(agreement) % 9)):
                agreementlst.append({})
        agreement = [{'name': '합의', 'data': agreementlst, 'count': len(agreement)}]
    else:
        agreement = [{'name': '합의', 'data': [{} for i in range(9)], 'count': 0}]
    if financial:
        financiallst = []
        for f in financial:
            financiallst.append(f)
        if len(financial) % 9 != 0:
            for i in range(9 - (len(financial) % 9)):
                financiallst.append({})
        financial = [{'name': '재무합의', 'data': financiallst, 'count': len(financial)}]
    else:
        financial = [{'name': '재무합의', 'data': [{} for i in range(9)], 'count': 0}]

    return apply, process, reference, approval, agreement, financial


def intcomma(num):
    num = int(num or 0)
    result = format(num, ',')
    if result == '0':
        result = ''
    return result


def mail_approval(employee, document, type):
    # smtp 정보
    email = AdminEmail.objects.filter(Q(smtpStatus='정상')).aggregate(Max('adminId'))
    email = AdminEmail.objects.get(Q(adminId=email['adminId__max']))
    # 결재요청 메일 전송
    try:
        if type == "결재요청":
            title = "'{}' 결재 요청".format(document.title)
            html = approvalhtml(document)
        elif type == "결재완료":
            title = "'{}' 결재 완료".format(document.title)
            html = approvaldonehtml(document)
        elif type == "결재반려":
            title = "'{}' 결재 반려".format(document.title)
            html = rejectdonehtml(document)

        toEmail = employee.empEmail
        fromEmail = 'usails@unioneinc.co.kr'

        msg = MIMEMultipart("alternative")
        msg["From"] = fromEmail
        msg["To"] = toEmail
        msg["Subject"] = Header(s=title, charset="utf-8")
        msg.attach(MIMEText(html, "html", _charset="utf-8"))

        if email.smtpSecure == 'TLS':
            smtp = smtplib.SMTP(email.smtpServer, email.smtpPort)
            smtp.login(email.smtpEmail, email.smtpPassword)
            smtp.sendmail(fromEmail, toEmail, msg.as_string())
            smtp.close()
        elif email.smtpSecure == 'SSL':
            smtp = SMTP_SSL("{}:{}".format(email.smtpServer, email.smtpPort))
            smtp.login(email.smtpEmail, email.smtpPassword)
            smtp.sendmail(fromEmail, toEmail, msg.as_string())
            smtp.close()

        return {'result': 'ok'}
    except Exception as e:
        print(e)
        return {'result': e}


def mail_document(toEmail, fromEmail, document):
    # smtp 정보
    email = AdminEmail.objects.filter(Q(smtpStatus='정상')).aggregate(Max('adminId'))
    email = AdminEmail.objects.get(Q(adminId=email['adminId__max']))
    # 전자결재 공유 메일 전송
    try:
        title = "'{}' 문서 공유".format(document.title)
        html = documenthtml(document)
        toEmail = toEmail
        fromEmail = fromEmail

        msg = MIMEMultipart("alternative")
        msg["From"] = fromEmail
        msg["To"] = toEmail
        msg["Subject"] = Header(s=title, charset="utf-8")
        msg.attach(MIMEText(html, "html", _charset="utf-8"))
        print(email.smtpServer, email.smtpPort, email, email.smtpServer)
        if email.smtpSecure == 'TLS':
            smtp = smtplib.SMTP(email.smtpServer, email.smtpPort)
            smtp.login(email.smtpEmail, email.smtpPassword)
            smtp.sendmail(fromEmail, toEmail, msg.as_string())
            smtp.close()
        elif email.smtpSecure == 'SSL':
            print(email.smtpServer)
            smtp = SMTP_SSL(email.smtpServer, email.smtpPort)
            smtp.login(email.smtpEmail, email.smtpPassword)
            smtp.sendmail(fromEmail, toEmail, msg.as_string())
            smtp.close()
        return 'Y'
    except Exception as e:
        return e


def approvalhtml(document):
    url = "http://lop.unioneinc.co.kr:8031/"
    html = """
    <html lang="ko">
    <head>
    <meta charset="utf-8">
      <style type="text/css">
        @font-face {
          font-family: JejuGothic;
          src: url({% static '/mail/JejuGothic.ttf' %});
        }

        html {
          font-family: JejuGothic, serif;
        }

      </style>
    </head>
    <body>
      <div style="border: 2px solid white;width: 600px;height: 500px;text-align: center;">
        <div style="text-align: center;margin-top:50px">
         <strong style="font-size: 30px;">Usails 전자결재 요청</strong>
        </div>
        <br>
        <div style="text-align:center">
        <table>
          <tr>
            <td colspan="4">
              <table style="margin:30px;border: 1px solid #858796a3;border-collapse: collapse;">
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">문&nbsp; &nbsp;서 &nbsp; &nbsp;종&nbsp; &nbsp;류</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.formId.formTitle +"""</td>
                </tr>
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">문&nbsp; &nbsp;서 &nbsp; &nbsp;번&nbsp; &nbsp;호</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.documentNumber +"""</td>
                </tr>
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">문&nbsp; &nbsp;서 &nbsp; &nbsp;제&nbsp; &nbsp;목</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.title +"""</td>
                </tr>
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">기&nbsp; &nbsp; &nbsp; 안 &nbsp; &nbsp; &nbsp; 자</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.writeEmp.empName +"""</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr style="height: 60px">
            <td style="text-align: center;width: 550px">
              <span style="background-color:#4e73df;width:100px;font-size:17px;padding:10px;"><a href='"""+url+"""approval/viewdocument/"""+ str(document.documentId) +"""/' style="color:#fff">확인</a></button>
            </td>
          </tr>
        </table>
      </div>
      </div>
    </body>
    </html>
    """
    return html


def approvaldonehtml(document):
    url = "https://lop.unioneinc.co.kr/"
    html = """
    <html lang="ko">
    <head>
    <meta charset="utf-8">
      <style type="text/css">
        @font-face {
          font-family: JejuGothic;
          src: url({% static '/mail/JejuGothic.ttf' %});
        }

        html {
          font-family: JejuGothic, serif;
        }

      </style>
    </head>
    <body>
      <div style="border: 2px solid white;width: 600px;height: 500px;text-align: center;">
        <div style="text-align: center;margin-top:50px">
         <strong style="font-size: 30px;">Usails 전자결재 완료</strong>
        </div>
        <br>
        <div style="text-align:center">
        <div style="font-size:15px;text-align: center;color:#4e73df">※ 기안 하신 문서가 완료 되었습니다. ※</div>
        <table>
          <tr>
            <td colspan="4">
              <table style="margin:30px;border: 1px solid #858796a3;border-collapse: collapse;">
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">문&nbsp; &nbsp;서 &nbsp; &nbsp;종&nbsp; &nbsp;류</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.formId.formTitle +"""</td>
                </tr>
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">문&nbsp; &nbsp;서 &nbsp; &nbsp;번&nbsp; &nbsp;호</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.documentNumber +"""</td>
                </tr>
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">문&nbsp; &nbsp;서 &nbsp; &nbsp;제&nbsp; &nbsp;목</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.title +"""</td>
                </tr>
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">기&nbsp; &nbsp; &nbsp; 안 &nbsp; &nbsp; &nbsp; 자</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.writeEmp.empName +"""</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr style="height: 60px">
            <td style="text-align: center;width: 550px">
              <span style="background-color:#4e73df;width:100px;font-size:17px;padding:10px;"><a href='"""+url+"""approval/viewdocument/"""+ str(document.documentId) +"""/' style="color:#fff">확인</a></button>
            </td>
          </tr>
        </table>
      </div>
      </div>
    </body>
    </html>
    """
    return html


def rejectdonehtml(document):
    url = "https://lop.unioneinc.co.kr/"
    html = """
    <html lang="ko">
    <head>
    <meta charset="utf-8">
      <style type="text/css">
        @font-face {
          font-family: JejuGothic;
          src: url({% static '/mail/JejuGothic.ttf' %});
        }

        html {
          font-family: JejuGothic, serif;
        }

      </style>
    </head>
    <body>
      <div style="border: 2px solid white;width: 600px;height: 500px;text-align: center;">
        <div style="text-align: center;margin-top:50px">
         <strong style="font-size: 30px;">Usails 전자결재 반려</strong>
        </div>
        <br>
        <div style="text-align:center">
        <div style="font-size:15px;text-align: center;color:#e74a3b">※ 기안 하신 문서가 반려 되었습니다. ※</div>
        <table>
          <tr>
            <td colspan="4">
              <table style="margin:30px;border: 1px solid #858796a3;border-collapse: collapse;">
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">문&nbsp; &nbsp;서 &nbsp; &nbsp;종&nbsp; &nbsp;류</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.formId.formTitle +"""</td>
                </tr>
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">문&nbsp; &nbsp;서 &nbsp; &nbsp;번&nbsp; &nbsp;호</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.documentNumber +"""</td>
                </tr>
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">문&nbsp; &nbsp;서 &nbsp; &nbsp;제&nbsp; &nbsp;목</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.title +"""</td>
                </tr>
                <tr style="height: 50px">
                  <td colspan="1" style="border: 1px solid #858796a3;border-collapse: collapse;background-color:#ebfaff;width: 150px;text-align:center">기&nbsp; &nbsp; &nbsp; 안 &nbsp; &nbsp; &nbsp; 자</td>
                  <td colspan="3" style="border: 1px solid #858796a3;border-collapse: collapse;width: 400px;text-align:left;padding-left:10px">"""+ document.writeEmp.empName +"""</td>
                </tr>
              </table>
            </td>
          </tr>
          <tr style="height: 60px">
            <td style="text-align: center;width: 550px">
              <span style="background-color:#4e73df;width:100px;font-size:17px;padding:10px;"><a target="_blank" href='"""+url+"""approval/viewdocument/"""+ str(document.documentId) +"""/' style="color:#fff">확인</a></button>
            </td>
          </tr>
        </table>
      </div>
      </div>
    </body>
    </html>
    """
    return html


def documenthtml(document):
    url = "http://lop.unioneinc.co.kr:8031/"
    preservationYear = str(document.preservationYear)
    draftDatetime = ''
    approveDatetime = ''
    if document.preservationYear == 9999:
        preservationYear = '영구'
    if document.draftDatetime:
        draftDatetime = str(document.draftDatetime)[:16]
    if document.approveDatetime:
        approveDatetime = str(document.approveDatetime)[:16]

    files = Documentfile.objects.filter(documentId=document.documentId)

    html = """
    <html lang="ko">
    <head>
    <meta charset="utf-8">
      <style type="text/css">
        @font-face {
          font-family: JejuGothic;
          src: url({% static '/mail/JejuGothic.ttf' %});
        }

        html {
          font-family: JejuGothic, serif;
        }

      </style>
    </head>
    <body>
        <div style="text-align:center;width: 60%;margin-bottom:30px;font-size:30px;font-family:bold;">""" + document.formId.formTitle + """</div>
        <table style="table-layout: fixed;width: 60%;border-collapse: collapse;margin-bottom: 1rem;border: 1px solid #858796a3;">
          <tbody>
          <tr style="height:40px;border: 1px solid #858796a3;vertical-align: middle;padding: 8px 15px;">
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 10%;background-color: #f8f9fc;text-align: center;font-weight:bold;" colspan="1">문서 종류</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 40%;text-align: left;padding-left:10px;" colspan="4">
              """ + document.formId.categoryId.firstCategory + """ >
              """ + document.formId.categoryId.secondCategory + """ >
              """ + document.formId.formTitle + """
            </td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 10%;background-color: #f8f9fc;text-align: center;font-weight:bold;" colspan="1">문서 번호</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 40%;text-align: left;padding-left:10px;" colspan="4" colspan="4">""" + document.documentNumber + """</td>
          </tr>
          <tr style="height:40px;border: 1px solid #858796a3;vertical-align: middle;padding: 8px 15px;">
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 10%;background-color: #f8f9fc;text-align: center;font-weight:bold;" colspan="1">기안 부서</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 40%;text-align: left;padding-left:10px;" colspan="4" colspan="4">""" + document.writeEmp.empDeptName + """</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 10%;background-color: #f8f9fc;text-align: center;font-weight:bold;" colspan="1">기안자</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 40%;text-align: left;padding-left:10px;" colspan="4" colspan="4">""" + document.writeEmp.empName + """</td>
          </tr>
          <tr style="height:40px;border: 1px solid #858796a3;vertical-align: middle;padding: 8px 15px;">
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 10%;background-color: #f8f9fc;text-align: center;font-weight:bold;" colspan="1">보존 연한</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 40%;text-align: left;padding-left:10px;" colspan="4" colspan="4">
              """ + preservationYear + """
            </td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 10%;background-color: #f8f9fc;text-align: center;font-weight:bold;" colspan="1">보안 등급</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 40%;text-align: left;padding-left:10px;" colspan="4" colspan="4">""" + document.securityLevel + """등급</td>
          </tr>
          <tr style="height:40px;border: 1px solid #858796a3;vertical-align: middle;padding: 8px 15px;">
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 10%;background-color: #f8f9fc;text-align: center;font-weight:bold;" colspan="1">기안 일시</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 40%;text-align: left;padding-left:10px;" colspan="4" colspan="4">""" + draftDatetime + """</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 10%;background-color: #f8f9fc;text-align: center;font-weight:bold;" colspan="1">완료 일시</td>
            <td style="border: 1px solid #858796a3;vertical-align: middle;width: 40%;text-align: left;padding-left:10px;" colspan="4" colspan="4">""" + approveDatetime + """</td>
          </tr>
      </tbody>
    </table>

    <table style="table-layout: fixed;width: 100%;border-collapse: collapse;margin-bottom: 1rem;">
      <tr style="height:60px;vertical-align: middle;padding: 8px 15px;">
        <td>
          <h3>""" + document.title + """</h3>
        </td>
      </tr>
      <tr style="vertical-align: middle;padding: 8px 15px;">
        <td>
          """ + document.contentHtml + """
          <br>
        </td>
      </tr>
    </table>
    """

    if files:
        html += '<table width="60%"><tr><td><b>첨부파일</b></td></tr>'
        for f in files:
            html += '<tr><td><a target="_blank" href="'+url+'media/' + str(f.file) + '" download>' + f.fileName + ' (' + str(f.fileSize) + 'MB)</a></td></tr>'
        html += '</table>'

    html += "</div></body></html>"

    return html
