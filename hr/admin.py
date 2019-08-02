from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Position, Employee, Attendance, Punctuality


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('positionId', 'positionName', 'positionSalary')
    list_filter = ('positionId', 'positionName', 'positionSalary')
    list_display_links = ['positionId', 'positionName', 'positionSalary']


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