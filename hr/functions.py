from django.contrib.auth.models import User
from django.db.models import Q
from .models import Attendance, Employee, Punctuality
from service.models import Servicereport, Vacation
from scheduler.models import Eventday
import datetime


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
    users = User.objects.filter(Q(employee__empStatus='Y')).exclude(Q(employee__empDeptName='임원') | Q(employee__empDeptName='미정')) \
        .values('employee__empId', 'employee__empName', 'employee__empDeptName', 'employee__empPosition', 'employee__empRank', 'employee__dispatchCompany') \
        .order_by('employee__empDeptName', 'employee__empPosition', 'employee__empRank')

    for date in dateList:
        print(date)
        if datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:10])).weekday() not in [5, 6] and is_holiday(date) == False:
            attendances = Attendance.objects.filter(attendanceDate=date).order_by('attendanceTime')
            for user in users:
                # 기본
                user['status'] = '-'
                user['date'] = date

                # 직급
                positionName = employee_empPosition(user['employee__empPosition'])
                user['positionName'] = positionName
                vacation = Vacation.objects.filter(Q(vacationDate=date) & Q(empId_id=user['employee__empId'])).first()

                # 상주
                if user['employee__dispatchCompany'] != '내근':
                    user['status'] = '상주'

                # 휴가
                elif vacation:
                    if vacation.vacationType == '일차' or vacation.vacationType == '오전반차':
                        user['status'] = vacation.vacationType
                    else:
                        for attendance in attendances:
                            if user['employee__empId'] == attendance.empId_id:
                                if attendance.attendanceTime >= datetime.time(9, 1, 0):
                                    user['status'] = '지각'
                                    break
                                else:
                                    user['status'] = '출근'
                                    break

                else:
                    service = Servicereport.objects.filter(Q(serviceDate=date) & Q(empId=user['employee__empId'])).order_by('serviceStartDatetime').first()
                    if service:
                        if service.directgo == 'Y':
                            user['status'] = '직출'
                        else:
                            for attendance in attendances:
                                if user['employee__empId'] == attendance.empId_id:
                                    if attendance.attendanceTime >= datetime.time(9, 1, 0):
                                        user['status'] = '지각'
                                        break
                                    else:
                                        user['status'] = '출근'
                                        break
                    else:
                        for attendance in attendances:
                            if user['employee__empId'] == attendance.empId_id:
                                if attendance.attendanceTime >= datetime.time(9, 1, 0):
                                    user['status'] = '지각'
                                    break
                                else:
                                    user['status'] = '출근'
                                    break

            for user in users:
                # 값이 달라진 row 만 insert
                if Punctuality.objects.filter(Q(empId=user['employee__empId']) & Q(punctualityDate=user['date']) & Q(punctualityType=user['status'])).first() == None:
                    # 비고란에 값이 있으면 안 바꿈. 수정이 일어난 경우
                    if Punctuality.objects.filter(Q(empId=user['employee__empId']) & Q(punctualityDate=user['date'])&Q(comment__isnull=True)).first() == None:
                        employee = Employee.objects.get(empId=user['employee__empId'])
                        Punctuality.objects.create(empId=employee, punctualityDate=user['date'], punctualityType=user['status'])


    return 0


def check_absence(id, startdate, enddate, contain):
    if contain == False:
        punctuality = Punctuality.objects.filter(Q(punctualityDate__gte=startdate) & Q(punctualityDate__lt=enddate) & Q(empId_id=id) & Q(punctualityType='지각'))
    else:
        punctuality = Punctuality.objects.filter(Q(punctualityDate__gte=startdate) & Q(punctualityDate__lte=enddate) & Q(empId_id=id) & Q(punctualityType='지각'))
    return punctuality

def year_absence(year):
    users = User.objects.filter(Q(employee__empStatus='Y')).exclude(Q(employee__empDeptName='임원') | Q(employee__empDeptName='미정')) \
        .values('employee__empId', 'employee__empName', 'employee__empDeptName', 'employee__empPosition', 'employee__empRank', 'employee__dispatchCompany') \
        .order_by('employee__empDeptName', 'employee__empPosition', 'employee__empRank')

    for user in users:
        user['employeePositionName'] = employee_empPosition(user['employee__empPosition'])
        q1absence = check_absence(user['employee__empId'],'{}-01-01'.format(year),'{}-04-01'.format(year), True)
        q2absence = check_absence(user['employee__empId'], '{}-04-01'.format(year), '{}-07-01'.format(year), True)
        q3absence = check_absence(user['employee__empId'], '{}-07-01'.format(year), '{}-10-01'.format(year), True)
        q4absence = check_absence(user['employee__empId'], '{}-10-01'.format(year), '{}-01-01'.format(str(int(year)+1)), True)

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

    team1 =[]
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
        elif user['employee__empDeptName'] == '솔루션사업팀':
            team5.append(user)
        elif user['employee__empDeptName'] == 'DB지원팀':
            team6.append(user)

    userList = (team1, team2, team3, team4, team5, team6 )

    return userList