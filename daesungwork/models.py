from django.db import models
from hr.models import Employee
from django.utils import timezone
from client.models import Company


class Center(models.Model):
    centerId = models.AutoField(primary_key=True)
    centerName = models.CharField(max_length=30)
    centerStatus = models.CharField(max_length=10, default='Y')

    def __str__(self):
        return str(self.centerId)


class CenterManager(models.Model):
    centerManagerId = models.AutoField(primary_key=True)
    writeEmp = models.ForeignKey(Employee, on_delete=models.CASCADE)
    createdDatetime = models.DateTimeField(default=timezone.now)
    startDate = models.DateField(null=True, blank=True)
    endDate = models.DateField(null=True, blank=True)
    centerManagerStatus = models.CharField(max_length=10, default='Y')

    def __str__(self):
        return str(self.centerManagerId)


class CenterManagerEmp(models.Model):
    managerId = models.AutoField(primary_key=True)
    centerManagerId = models.ForeignKey(CenterManager, null=True, blank=True, on_delete=models.CASCADE)
    empId = models.ForeignKey(Employee, on_delete=models.CASCADE)
    manageArea = models.ForeignKey(Center, null=True, blank=True, on_delete=models.SET_NULL, related_name='manageArea')
    additionalArea = models.CharField(max_length=30, null=True, blank=True)
    cleanupArea = models.ForeignKey(Center, null=True, blank=True, on_delete=models.SET_NULL, related_name='cleanupArea')

    def __str__(self):
        return str(self.managerId)


class CheckList(models.Model):
    checkListId = models.AutoField(primary_key=True)
    checkListName = models.CharField(max_length=30)
    checkListStatus = models.CharField(max_length=10, default='Y')

    def __str__(self):
        return str(self.checkListId)


class ConfirmCheckList(models.Model):
    checkListStatusChoices = (('Y', '정상'), ('N', '이상'))
    confirmId = models.AutoField(primary_key=True)
    empId = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True, blank=True)
    centerId = models.ForeignKey(Center, on_delete=models.PROTECT, null=True, blank=True)
    confirmDate = models.DateField()
    checkListId = models.ForeignKey(CheckList, on_delete=models.PROTECT)
    checkListStatus = models.CharField(max_length=10, choices=checkListStatusChoices, default='Y')
    comment = models.CharField(max_length=50, null=True, blank=True)
    file = models.FileField(upload_to="checkList/")

    def __str__(self):
        return str(self.confirmId)


class WarehouseMainCategory(models.Model):
    categoryStatusChoices = (('Y', '사용'), ('N', '미사용'))
    categoryId = models.AutoField(primary_key=True)
    categoryName = models.CharField(max_length=20, unique=True)
    categoryStatus = models.CharField(max_length=20, choices=categoryStatusChoices, default='Y')

    def __str__(self):
        return str(self.categoryName)


class WarehouseSubCategory(models.Model):
    categoryStatusChoices = (('Y', '사용'), ('N', '미사용'))
    categoryId = models.AutoField(primary_key=True)
    categoryName = models.CharField(max_length=20, unique=True)
    categoryStatus = models.CharField(max_length=20, choices=categoryStatusChoices, default='Y')

    def __str__(self):
        return str(self.categoryName)


class Warehouse(models.Model):
    warehouseId = models.AutoField(primary_key=True)
    mainCategory = models.ForeignKey(WarehouseMainCategory, on_delete=models.PROTECT)
    subCategory = models.ForeignKey(WarehouseSubCategory, on_delete=models.PROTECT)
    warehouseDrawing = models.FileField(upload_to="warehouse/", null=True, blank=True, default="warehouse/noimage.png")

    def __str__(self):
        return str('창고:{} 섹션:{}'.format(self.mainCategory, self.subCategory))


class Type(models.Model):
    typeId = models.AutoField(primary_key=True)
    typeName = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return str(self.typeName)


class Product(models.Model):
    productId = models.AutoField(primary_key=True)
    typeName = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, blank=True)
    modelName = models.CharField(max_length=20, unique=True)
    productName = models.CharField(max_length=20, null=True, blank=True)
    unitPrice = models.IntegerField(null=True, blank=True, default=0)
    position = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    productPicture = models.FileField(upload_to="product/", null=True, blank=True, default="product/noimage.png")
    productStatus = models.CharField(max_length=20, default='Y')

    def __str__(self):
        return str(self.modelName)


class Size(models.Model):
    sizeId = models.AutoField(primary_key=True)
    productId = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return str(self.size)


class Affiliate(models.Model):
    affiliateId = models.AutoField(primary_key=True)
    affiliateName = models.CharField(max_length=20, null=True, blank=True, unique=True)

    def __str__(self):
        return str(self.affiliateName)


class Sale(models.Model):
    saleId = models.AutoField(primary_key=True)
    saleDate = models.DateField()
    affiliate = models.ForeignKey(Affiliate, on_delete=models.PROTECT, null=True)
    client = models.ForeignKey(Company, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    unitPrice = models.IntegerField(null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    salePrice = models.IntegerField()
    createdDate = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.saleId)


class Buy(models.Model):
    buyId = models.AutoField(primary_key=True)
    buyDate = models.DateField()
    client = models.ForeignKey(Company, on_delete=models.PROTECT)
    product = models.CharField(max_length=200, null=True, blank=True)
    # product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    # size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=0)
    salePrice = models.IntegerField(default=0)
    vatPrice = models.IntegerField()
    totalPrice = models.IntegerField()
    comment = models.CharField(max_length=200, null=True, blank=True)
    createdDate = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.buyId)


class DailyReport(models.Model):
    dailyreportId = models.AutoField(primary_key=True)
    workDate = models.DateField()
    writeEmp = models.ForeignKey(Employee, on_delete=models.CASCADE)
    title = models.CharField(max_length=20, null=True, blank=True)
    contents = models.TextField(help_text="상세 내용을 작성해 주세요.")
    writeDatetime = models.DateTimeField(default=timezone.now)
    modifyDatetime = models.DateTimeField(default=timezone.now, null=True, blank=True)
    files = models.FileField(upload_to="dailyreport/", null=True, blank=True)

    def __str__(self):
        return str(self.writeEmp)


class Display(models.Model):
    displayId = models.AutoField(primary_key=True)
    postDate = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    size = models.ForeignKey(Size, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    comment = models.CharField(max_length=200, null=True, blank=True, default='')

    def __str__(self):
        return str(self.displayId)


class Reproduction(models.Model):
    reproductionId = models.AutoField(primary_key=True)
    postDate = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    size = models.ForeignKey(Size, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    comment = models.CharField(max_length=200, null=True, blank=True, default='')

    def __str__(self):
        return str(self.reproductionId)


class StockCheck(models.Model):
    stockcheckId = models.AutoField(primary_key=True)
    typeName = models.ForeignKey(Type, on_delete=models.SET_NULL, null=True, blank=True)
    checkEmp = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    checkDate = models.DateField()
    createdDate = models.DateTimeField(default=timezone.now)
    modifyDate = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.checkDate)


class ProductCheck(models.Model):
    productcheckId = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)
    productGap = models.CharField(max_length=10, null=True, blank=True, default='')
    stockcheck = models.ForeignKey(StockCheck, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.product)