

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