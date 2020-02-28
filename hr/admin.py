from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Position, Employee, Attendance, Punctuality, Department, AdminEmail, AdminVacation, ReturnVacation, Alert


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('positionId', 'positionRank', 'positionName', 'positionSalary')
    list_filter = ('positionId', 'positionRank', 'positionName', 'positionSalary')
    list_display_links = ['positionId', 'positionRank', 'positionName', 'positionSalary']


class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = '사원정보'


class UserAdmin(BaseUserAdmin):
    inlines = (EmployeeInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('attendanceId', 'attendanceDate', 'attendanceTime', 'empId', 'attendanceType')
    list_filter = ('attendanceDate','empId')
    list_display_links = ['attendanceId', 'attendanceDate', 'attendanceTime', 'empId', 'attendanceType']


@admin.register(Punctuality)
class PunctualityAdmin(admin.ModelAdmin):
    list_display = ('punctualityId', 'empId', 'punctualityDate', 'punctualityType', 'comment')
    list_filter = ('punctualityDate', 'punctualityType' , 'comment')
    list_display_links = ['punctualityId', 'empId', 'punctualityDate', 'punctualityType', 'comment']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('deptId', 'deptName', 'deptManager', 'deptLevel', 'parentDept', 'startDate', 'endDate', 'departmentStatus')
    list_filter = ('deptName', 'departmentStatus')
    list_display_links = ['deptId', 'deptName', 'deptManager', 'deptLevel', 'parentDept', 'startDate', 'endDate', 'departmentStatus']

@admin.register(AdminEmail)
class AdminEmailAdmin(admin.ModelAdmin):
    list_display = ('adminId', 'smtpServer', 'smtpPort', 'smtpEmail', 'smtpDatetime', 'smtpStatus', 'smtpSecure')
    list_filter = ('smtpSecure', 'smtpStatus')
    list_display_links = ['adminId', 'smtpServer', 'smtpPort', 'smtpEmail', 'smtpDatetime', 'smtpStatus', 'smtpSecure']

@admin.register(AdminVacation)
class AdminVacationAdmin(admin.ModelAdmin):
    list_display = ('vacationId', 'empId', 'vacationType', 'vacationDays', 'creationDateTime', 'expirationDate', 'comment')
    list_filter = ('empId', 'vacationType')
    list_display_links = ['vacationId', 'empId', 'vacationType', 'vacationDays', 'creationDateTime', 'expirationDate', 'comment']


@admin.register(ReturnVacation)
class ReturnVacationAdmin(admin.ModelAdmin):
    list_display = ('returnId', 'returnDateTime', 'empId', 'vacationId', 'comment')
    list_filter = ('returnDateTime', 'empId', 'vacationId')
    list_display_links = ['returnId', 'returnDateTime', 'empId', 'vacationId', 'comment']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alertId', 'empId', 'text', 'url', 'createdDatetime', 'clickedDatetime')
    list_filter = ('empId', )
    list_display_links = ['alertId', 'empId', 'text', 'url', 'createdDatetime', 'clickedDatetime']