from django.contrib import admin
from .models import Center, CenterManager, CenterManagerEmp, CheckList, ConfirmCheckList, WarehouseMainCategory, WarehouseSubCategory, Warehouse, \
    Product, Size, Sale, Affiliate, DailyReport, Display


@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ('centerId', 'centerName', 'centerStatus')
    list_filter = ('centerId', 'centerName', 'centerStatus')
    list_display_links = ['centerId', 'centerName', 'centerStatus']


@admin.register(CenterManager)
class CenterManagerAdmin(admin.ModelAdmin):
    list_display = ('centerManagerId', 'writeEmp', 'createdDatetime', 'startDate', 'endDate', 'centerManagerStatus')
    list_filter = ('writeEmp', 'centerManagerStatus')
    list_display_links = ['centerManagerId', 'writeEmp', 'createdDatetime', 'startDate', 'endDate', 'centerManagerStatus']


@admin.register(CenterManagerEmp)
class CenterManagerEmpAdmin(admin.ModelAdmin):
    list_display = ('managerId', 'empId', 'manageArea', 'additionalArea', 'cleanupArea')
    list_filter = ('empId', 'manageArea')
    list_display_links = ['managerId', 'empId', 'manageArea', 'additionalArea', 'cleanupArea']


@admin.register(CheckList)
class CheckListAdmin(admin.ModelAdmin):
    list_display = ('checkListId', 'checkListName', 'checkListStatus')
    list_filter = ('checkListName', 'checkListStatus')
    list_display_links = ['checkListId', 'checkListName', 'checkListStatus']


@admin.register(ConfirmCheckList)
class ConfirmCheckListAdmin(admin.ModelAdmin):
    list_display = ('confirmId', 'empId', 'confirmDate', 'checkListId', 'checkListStatus', 'comment', 'centerId')
    list_filter = ('checkListId', 'checkListStatus')
    list_display_links = ['confirmId', 'confirmDate', 'checkListId', 'checkListStatus', 'comment']


@admin.register(WarehouseMainCategory)
class WarehouseMainCategoryAdmin(admin.ModelAdmin):
    list_display = ('categoryId', 'categoryName', 'categoryStatus')
    list_filter = ('categoryName', 'categoryStatus')
    list_display_links = ['categoryId', 'categoryName', 'categoryStatus']


@admin.register(WarehouseSubCategory)
class WarehouseSubCategoryAdmin(admin.ModelAdmin):
    list_display = ('categoryId', 'categoryName', 'categoryStatus')
    list_filter = ('categoryName', 'categoryStatus')
    list_display_links = ['categoryId', 'categoryName', 'categoryStatus']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('mainCategory', 'subCategory', 'warehouseDrawing')
    list_filter = ('mainCategory', 'subCategory', 'warehouseDrawing')
    list_display_links = ['mainCategory', 'subCategory', 'warehouseDrawing']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('productId', 'modelName', 'productName', 'unitPrice', 'position', 'productPicture')
    list_filter = ('modelName', 'productName', 'position')
    list_display_links = ['productId', 'modelName', 'productName', 'unitPrice', 'position', 'productPicture']


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('sizeId', 'productId', 'size')
    list_filter = ('productId', 'size')
    list_display_links = ['sizeId', 'productId', 'size']


@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    list_display = ('affiliateId', 'affiliateName')
    list_filter = ('affiliateId', 'affiliateName')
    list_display_links = ['affiliateId', 'affiliateName']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('saleDate', 'affiliate', 'client', 'product', 'size', 'unitPrice', 'quantity', 'salePrice', 'createdDate')
    list_filter = ('affiliate', 'client', 'product')
    list_display_links = ['saleDate', 'affiliate', 'client', 'product', 'size', 'unitPrice', 'quantity', 'salePrice', 'createdDate']


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('dailyreportId', 'workDate', 'writeEmp', 'title', 'writeDatetime', 'modifyDatetime')
    list_filter = ('writeEmp', )
    list_display_links = ['dailyreportId', 'workDate', 'writeEmp', 'title', 'writeDatetime', 'modifyDatetime']


@admin.register(Display)
class DisplayAdmin(admin.ModelAdmin):
    list_display = ('displayId', 'postDate', 'product', 'size', 'quantity', 'comment')
    list_filter = ('product',)
    list_display_links = ['displayId', 'postDate', 'product', 'size', 'quantity', 'comment']
