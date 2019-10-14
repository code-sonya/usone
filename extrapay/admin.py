from django.contrib import admin
from .models import OverHour, Car, Oil, Fuel


@admin.register(OverHour)
class OverHourAdmin(admin.ModelAdmin):
    list_display = ('overHourId', 'empName', 'overHourDate', 'sumOverHour', 'compensatedHour', 'payHour')
    list_filter = ('empName', 'overHourDate')
    list_display_links = ['overHourId', 'empName', 'overHourDate']


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
