from django.contrib import admin
from .models import OverHour, Car, Oil, Fuel, ExtraPay


@admin.register(ExtraPay)
class ExtraPayAdmin(admin.ModelAdmin):
    list_display = ('extraPayId', 'empName', 'overHourDate', 'compensatedHour', 'payStatus')
    list_filter = ('empName', 'overHourDate', 'compensatedHour', 'payStatus')
    list_display_links = ['extraPayId', 'empName', 'overHourDate', 'compensatedHour', 'payStatus']


@admin.register(OverHour)
class OverHourAdmin(admin.ModelAdmin):
    list_display = ('overHourId', 'empName', 'overHourStartDate', 'overHourEndDate', 'overHour', 'extraPayId', 'overHourStatus')
    list_filter = ('empName', 'overHourStartDate', 'overHourEndDate', 'overHourStatus')
    list_display_links = ['overHourId', 'empName', 'overHourStartDate', 'overHourEndDate', 'overHourStatus']


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
    list_display = ('fuelId', 'serviceId', 'fuelStatus')
    list_filter = ('fuelId',)
    list_display_links = ['fuelId', 'serviceId', 'fuelStatus']
