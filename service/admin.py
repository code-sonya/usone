from django.contrib import admin
from .models import Servicereport, Serviceform, Vacation, Geolocation, Servicetype, Vacationcategory, Report, Participant


@admin.register(Servicereport)
class ServicereportAdmin(admin.ModelAdmin):
    list_display = ('serviceId', 'serviceDate', 'empDeptName', 'empName', 'companyName', 'serviceType', 'serviceTitle')
    list_filter = ('empDeptName', 'empName', 'companyName', )
    list_display_links = ['serviceId', 'serviceDate', 'empName', 'companyName']


@admin.register(Serviceform)
class ServiceformAdmin(admin.ModelAdmin):
    list_display = ('empId', 'companyName', 'serviceType', 'serviceTitle')
    list_filter = ('empId',)
    list_display_links = ['empId']


@admin.register(Vacation)
class VacationAdmin(admin.ModelAdmin):
    list_display = ('empId', 'empDeptName', 'empName', 'vacationDate', 'vacationType')
    list_filter = ('empId',)
    list_display_links = ['empId']


@admin.register(Geolocation)
class GeolocationAdmin(admin.ModelAdmin):
    list_display = ('geolocationId', 'serviceId', 'startLatitude', 'startLongitude', 'endLatitude', 'endLongitude')
    list_filter = ('geolocationId',)
    list_display_links = ['geolocationId', 'serviceId', 'startLatitude', 'startLongitude', 'endLatitude', 'endLongitude']


@admin.register(Servicetype)
class ServicetypeAdmin(admin.ModelAdmin):
    list_display = ('typeId', 'typeName', 'orderNumber', 'dashboardStatus', 'punctualityStatus')
    list_filter = ('typeName',)
    list_display_links = ['typeId', 'typeName', 'orderNumber']


@admin.register(Vacationcategory)
class VacationcategoryAdmin(admin.ModelAdmin):
    list_display = ('categoryId', 'categoryName')
    list_filter = ('categoryName',)
    list_display_links = ['categoryId', 'categoryName']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('reportId', 'category', 'reportDate', 'writeDatetime', 'modifyDatetime')
    list_filter = ('category',)
    list_display_links = ['reportId', 'category', 'reportDate', 'writeDatetime', 'modifyDatetime']


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('participantId', 'reportId', 'empId')
    list_filter = ('participantId', 'reportId', 'empId')
    list_display_links = ['participantId', 'reportId', 'empId']
