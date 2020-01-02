from django.contrib.auth.models import User
from django.db.models import Q, Max, Min, Count
from .models import Attendance, Employee, Punctuality, AdminEmail, Department
from service.models import Servicereport, Vacation
from scheduler.models import Eventday
import datetime
import smtplib
from smtplib import SMTP_SSL
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def employee_empPosition(positionNumber):
    if positionNumber == 1:
        positionName = '이사'
    elif positionNumber == 2:
        positionName = '부장'
    elif positionNumber == 3:
        positionName = '차장'
    elif positionNumber == 4:
        positionName = '과장'
    elif positionNumber == 5:
        positionName = '대리'
    elif positionNumber == 6:
        positionName = '사원'
    else:
        positionName = '미정'

    return positionName


def is_holiday(date):
    event = Eventday.objects.filter(Q(eventDate=date) & Q(eventType='휴일'))
    if event.count():
        return True
    else:
        return False


def save_punctuality(dateList):
    users = User.objects.filter(Q(employee__empStatus='Y')).exclude(Q(employee__empPosition=0) | Q(employee__empDeptName='미정')) \
        .values('employee__empId', 'employee__empName', 'employee__empDeptName', 'employee__empPosition', 'employee__empRank', 'employee__dispatchCompany') \
        .order_by('employee__empDeptName', 'employee__empPosition', 'employee__empRank')

    for date in dateList:
        if datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:10])).weekday() not in [5, 6] and is_holiday(date) == False:
            Date_min = datetime.datetime.combine(datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:10])), datetime.datetime.min.time())
            Date_max = datetime.datetime.combine(datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:10])), datetime.datetime.max.time())
            print(Date_min, Date_max)
            for user in users:
                # 기본
                user['status'] = '-'
                user['date'] = date
                user['comment'] = ''

                # 직급
                positionName = employee_empPosition(user['employee__empPosition'])
                user['positionName'] = positionName
                vacation = Vacation.objects.filter(Q(vacationDate=date) & Q(empId_id=user['employee__empId'])).first()

                # 업로드된 데이터 날짜의 employee 첫번째 지문 기록
                attendance = Attendance.objects.filter(Q(attendanceDate=date) & Q(empId_id=user['employee__empId'])).order_by('attendanceTime').first()
                service = Servicereport.objects.filter(Q(empId_id=user['employee__empId']) & Q(directgo='Y') & (Q(serviceStartDatetime__lte=Date_max) & Q(serviceEndDatetime__gte=Date_min)))
                sangju = Servicereport.objects.filter(Q(empId_id=user['employee__empId']) & Q(directgo='N') & Q(serviceType__typeName__icontains='상주') & (Q(serviceStartDatetime__lte=Date_max) & Q(serviceEndDatetime__gte=Date_min)))
                # print("service:", service, "sangju:", sangju)
                # 휴가
                if vacation:
                    # 일차 or 오전반차
                    if vacation.vacationType == '일차' or vacation.vacationType == '오전반차':
                        user['status'] = vacation.vacationType

                    # 오후반차
                    else:
                        # service = Servicereport.objects.filter(Q(serviceDate=date) & Q(empId=user['employee__empId']) & Q(directgo='Y')).first()
                        # 오후반차이고 상주일때
                        if sangju:
                            if sangju.first().serviceType.typeName == '상주':
                                user['status'] = '상주'
                                user['comment'] = str(sangju.first().companyName) + ' / 오후반차'

                        elif service:
                            # 오후반차이고 직출 교육일때
                            user['status'] = '직출'
                            if service.first().serviceType.typeName == '교육':
                                user['comment'] = '교육 / 오후반차'
                            # 오후반차이고 직출일때
                            else:
                                user['comment'] = str(service.first().companyName) + ' / 오후반차'

                        # 오후반차이고 직출이나 상주가 아닐 때
                        else:
                            # 첫번째 지문기록이 있을 때
                            if attendance:
                                if attendance.attendanceTime >= datetime.time(9, 1, 0):
                                    user['status'] = '지각'
                                    user['comment'] = '오후반차'
                                else:
                                    user['status'] = '출근'
                                    user['comment'] = '오후반차'

                else:
                    if sangju:
                        if sangju.first().serviceType.typeName == '상주':
                            user['status'] = '상주'
                            user['comment'] = str(sangju.first().companyName)
                    elif service:
                        # 오후반차이고 직출 교육일때
                        user['status'] = '직출'
                        if service.first().serviceType.typeName == '교육':
                            user['comment'] = '교육'
                        # 오후반차이고 직출일때
                        else:
                            user['comment'] = str(service.first().companyName)
                    else:
                        # 첫번째 지문기록이 있을 때
                        if attendance:
                            if attendance.attendanceTime >= datetime.time(9, 1, 0):
                                user['status'] = '지각'
                            else:
                                user['status'] = '출근'

            for user in users:
                punctuality = Punctuality.objects.filter(Q(empId=user['employee__empId']) & Q(punctualityDate=user['date']))
                # 해당날짜에 근태 정보가 있음
                if punctuality.first():
                    # 비고란에 값 있음
                    if punctuality.first().comment:
                        print('비고란에 값 있음')
                    # 비고란에 값 없음
                    else:
                        punctuality = punctuality.first()
                        # 기존과 근태 정보가 다를 때
                        if punctuality.punctualityType != user['status']:
                            print('근태 정보가 다를 때')
                            punctuality.punctualityType = user['status']
                            punctuality.save()
                        elif punctuality.punctualityType == user['status'] and punctuality.comment != user['comment']:
                            # 기존과 근태 정보는 같은데 비고란이 다를때
                            print(user['comment'])
                            punctuality.punctualityType = user['status']
                            punctuality.comment = user['comment']
                            punctuality.save()
                        else:
                            print('변경없음')
                # 해당 날짜에 근태 정보가 없음
                else:
                    print('해당 날짜에 근태 정보가 없음')
                    employee = Employee.objects.get(empId=user['employee__empId'])
                    if user['comment'] != '':
                        print('comment값있음')
                        Punctuality.objects.create(empId=employee, punctualityDate=user['date'], punctualityType=user['status'], comment=user['comment'])
                    else:
                        Punctuality.objects.create(empId=employee, punctualityDate=user['date'], punctualityType=user['status'])

    return 0


def check_absence(id, startdate, enddate, contain):
    if contain == False:
        punctuality = Punctuality.objects.filter(Q(punctualityDate__gte=startdate) & Q(punctualityDate__lte=enddate) & Q(empId_id=id) & Q(punctualityType='지각'))
    else:
        punctuality = Punctuality.objects.filter(Q(punctualityDate__gte=startdate) & Q(punctualityDate__lt=enddate) & Q(empId_id=id) & Q(punctualityType='지각'))
    return punctuality


def year_absence(year):
    users = User.objects.filter(Q(employee__empStatus='Y')).exclude(Q(employee__empDeptName='임원') | Q(employee__empDeptName='미정')) \
        .values('employee__empId', 'employee__empName', 'employee__empDeptName', 'employee__empPosition', 'employee__empRank', 'employee__dispatchCompany') \
        .order_by('employee__empDeptName', 'employee__empPosition', 'employee__empRank')

    for user in users:
        user['employeePositionName'] = employee_empPosition(user['employee__empPosition'])
        q1absence = check_absence(user['employee__empId'], '{}-01-01'.format(year), '{}-04-01'.format(year), True)
        q2absence = check_absence(user['employee__empId'], '{}-04-01'.format(year), '{}-07-01'.format(year), True)
        q3absence = check_absence(user['employee__empId'], '{}-07-01'.format(year), '{}-10-01'.format(year), True)
        q4absence = check_absence(user['employee__empId'], '{}-10-01'.format(year), '{}-01-01'.format(str(int(year) + 1)), True)

        user['yearabsenceCount'] = 0
        if q1absence:
            user['q1absenceDate'] = []
            for a in q1absence:
                user['q1absenceDate'].append(a.punctualityDate)
            user['q1absenceCount'] = len(q1absence)
            user['yearabsenceCount'] += len(q1absence)

        if q2absence:
            user['q2absenceDate'] = []
            for a in q2absence:
                user['q2absenceDate'].append(a.punctualityDate)
            user['q2absenceCount'] = len(q2absence)
            user['yearabsenceCount'] += len(q2absence)

        if q3absence:
            user['q3absenceDate'] = []
            for a in q3absence:
                user['q3absenceDate'].append(a.punctualityDate)
            user['q3absenceCount'] = len(q3absence)
            user['yearabsenceCount'] += len(q3absence)

        if q4absence:
            user['q4absenceDate'] = []
            for a in q4absence:
                user['q4absenceDate'].append(a.punctualityDate)
            user['q4absenceCount'] = len(q4absence)
            user['yearabsenceCount'] += len(q4absence)

    team1 = []
    team2 = []
    team3 = []
    team4 = []
    team5 = []
    team6 = []
    for user in users:
        if user['employee__empDeptName'] == '경영지원본부':
            team1.append(user)
        elif user['employee__empDeptName'] == '영업1팀':
            team2.append(user)
        elif user['employee__empDeptName'] == '영업2팀':
            team3.append(user)
        elif user['employee__empDeptName'] == '인프라서비스사업팀':
            team4.append(user)
        elif user['employee__empDeptName'] == '솔루션지원팀':
            team5.append(user)
        elif user['employee__empDeptName'] == 'DB지원팀':
            team6.append(user)

    userList = (team1, team2, team3, team4, team5, team6)
    return userList


def adminemail_test(smtpEmail, smtpPassword, smtpServer, smtpPort, smtpSecure):
    # 관리자 이메일등록 확인
    try:
        title = "관리자이메일등록"
        html = "관리자 이메일등록이 완료되었습니다."
        toEmail = "slkim@unioneinc.co.kr"
        fromEmail = smtpEmail

        msg = MIMEMultipart("alternative")
        msg["From"] = fromEmail
        msg["To"] = toEmail
        msg["Subject"] = Header(s=title, charset="utf-8")
        msg.attach(MIMEText(html, "html", _charset="utf-8"))


        if smtpSecure == 'SSL':
            smtp = SMTP_SSL("{}:{}".format(smtpServer, smtpPort))
            smtp.login(smtpEmail, smtpPassword)
            smtp.sendmail(fromEmail, toEmail, msg.as_string())
            smtp.close()
        elif smtpSecure == 'TLS':
            smtp = smtplib.SMTP(smtpServer, smtpPort)
            smtp.ehlo()
            smtp.starttls()  # TLS 사용시 필요
            smtp.login(smtpEmail, smtpPassword)
            smtp.sendmail(fromEmail, toEmail, msg.as_string())
            smtp.close()
        return 'Y'
    except Exception as e:
        return e


def siteMap():
    departments = Department.objects.all().order_by('deptName')
    deptLevel_min = departments.aggregate(Min('deptLevel'))['deptLevel__min']
    deptLevel_max = departments.aggregate(Max('deptLevel'))['deptLevel__max']
    deptLevelList = []
    for level in range(deptLevel_min, deptLevel_max+1):
        print("level: ", level)
        if deptLevel_min == level:
            deptList = {'level': str(level), 'data': []}
            for dept in departments.filter(Q(deptLevel=level)):
                colspan = siteMapCol(departments, departments, level, deptLevel_max, [dept.deptId])
                deptdict = dict()
                deptdict['colspan'] = colspan
                deptdict['level'] = level
                deptdict['deptName'] = dept.deptName
                if dept.deptManager:
                    deptdict['deptManager'] = dept.deptManager.empName
                    deptdict['deptManagerPosition'] = dept.deptManager.empPosition.positionName
                deptList['data'].append(deptdict)
            deptLevelList.append(deptList)

        else:
            deptList = {'level': str(level), 'data': []}
            parentDeptList = list(departments.filter(Q(deptLevel=level-1)).values_list('deptId', flat=True))
            for parentDept in parentDeptList:
                department = departments.filter(Q(deptLevel=level) & Q(parentDept=parentDept))
                for dept in department:
                    colspan = siteMapCol(departments, department, level, level+1, [dept.deptId])
                    deptdict = dict()
                    deptdict['colspan'] = colspan
                    deptdict['level'] = level
                    deptdict['deptName'] = dept.deptName
                    if dept.deptManager:
                        deptdict['deptManager'] = dept.deptManager.empName
                        deptdict['deptManagerPosition'] = dept.deptManager.empPosition.positionName
                    deptList['data'].append(deptdict)
            deptLevelList.append(deptList)
    return deptLevelList


def siteMapCol(departments, department, deptLevel, deptLevel_max, deptId):
    if deptLevel_max == deptLevel:
        print('department:', department)
        colspan = department.aggregate(Count('deptId'))['deptId__count']
        if colspan == 0:
            return 1
        return colspan
    else:
        department = departments.filter(Q(parentDept__in=deptId))
        deptId = list(department.values_list('deptId', flat=True))
        return siteMapCol(departments, department, deptLevel + 1, deptLevel_max, deptId)

