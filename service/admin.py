from django.contrib import admin
from .models import Servicereport, Serviceform, Vacation, Geolocation, Car, Oil, Fuel


@admin.register(Servicereport)
class ServicereportAdmin(admin.ModelAdmin):
    list_display = ('serviceDate', 'empDeptName', 'empName', 'companyName', 'serviceType', 'serviceTitle', 'serviceOverHour')
    list_filter = ('empDeptName', 'empName', 'companyName', )
    list_display_links = ['serviceDate', 'empName', 'companyName']


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


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('carId', 'oilType', 'carType', 'kpl')
    list_filter = ('carId', 'oilType', 'carType', 'kpl')
    list_display_links = ['carId', 'oilType', 'carType', 'kpl']


@admin.register(Oil)
class OilAdmin(admin.ModelAdmin):
    list_display = ('oilId', 'oilDate', 'carId', 'oilMoney', 'mpk')
    list_filter = ('oilId', 'oilDate', 'carId', 'oilMoney', 'mpk')
    list_display_links = ['oilId', 'oilDate', 'carId', 'oilMoney', 'mpk']


@admin.register(Fuel)
class FuelAdmin(admin.ModelAdmin):
    list_display = ('fuelId', 'serviceId', 'distance1', 'distance2', 'totalDistance', 'fuelStatus')
    list_filter = ('fuelId', 'serviceId', 'distance1', 'distance2', 'totalDistance', 'fuelStatus')
    list_display_links = ['fuelId', 'serviceId', 'distance1', 'distance2', 'totalDistance', 'fuelStatus']
