from django import forms
from django.db.models import Q

from hr.models import Employee
from .models import CenterManager, Sale, Size, Product, Warehouse, DailyReport, Display, Reproduction, Buy
from client.forms import CompanyForm
from client.models import Company


class CenterManagerForm(forms.ModelForm):

    class Meta:
        model = CenterManager
        fields = ('startDate', 'endDate')

        widgets = {
            'startDate': forms.TextInput(attrs={'class': 'input-form', 'type': 'date', 'max': '9999-12-31', 'id': 'startDate'}),
            'endDate': forms.TextInput(attrs={'class': 'input-form', 'type': 'date', 'max': '9999-12-31', 'id': 'endDate'}),
        }

    def __init__(self, *args, **kwargs):
        super(CenterManagerForm, self).__init__(*args, **kwargs)


class SaleForm(forms.ModelForm):

    class Meta:
        model = Sale
        fields = ('saleDate', 'affiliate', 'client', 'product', 'size', 'unitPrice', 'quantity', 'salePrice',)

        widgets = {
            'saleDate': forms.TextInput(attrs={
                'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'saleDate'
            }),
            'affiliate': forms.Select(attrs={
                'class': 'form-control', 'id': 'affiliate'
            }),
            'client': forms.Select(attrs={
                'class': 'form-control', 'id': "client"
            }),
            'product': forms.Select(attrs={
                'class': 'form-control', 'id': 'product',
                'onchange': 'changeModel(this.value, "size", "unitPrice", "quantity", "salePrice")'
            }),
            'size': forms.Select(attrs={
                'class': 'form-control', 'id': 'size'
            }),
            'unitPrice': forms.TextInput(attrs={
                'class': 'form-control', 'type': 'number', 'id': 'unitPrice',
                'onchange': 'changePrice("unitPrice", "quantity", "salePrice")'
            }),
            'quantity': forms.TextInput(attrs={
                'class': 'form-control', 'type': 'number', 'id': 'quantity',
                'onchange': 'changePrice("unitPrice", "quantity", "salePrice")'
            }),
            'salePrice': forms.TextInput(attrs={
                'class': 'form-control', 'type': 'number', 'id': 'salePrice'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        self.fields["client"].queryset = Company.objects.filter(Q(companyStatus='Y'))
        self.fields["product"].queryset = Product.objects.filter(Q(productStatus='Y'))
        # self.fields["size"].queryset = Size.objects.filter(Q(productId=self.fields["product"]["productId"]))


class BuyForm(forms.ModelForm):

    class Meta:
        model = Buy
        fields = (
            'buyDate', 'client', 'product', 'quantity',
            'salePrice', 'vatPrice', 'totalPrice', 'comment',
        )

        widgets = {
            'buyDate': forms.TextInput(attrs={
                'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'buyDate',
            }),
            'client': forms.Select(attrs={
                'class': 'form-control', 'id': "client",
            }),
            'product': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'product',
            }),
            'quantity': forms.TextInput(attrs={
                'class': 'form-control', 'type': 'number', 'id': 'quantity',
                'onchange': "changePrice('quantity', 'salePrice', 'vatPrice', 'totalPrice')",
            }),
            'salePrice': forms.TextInput(attrs={
                'class': 'form-control', 'type': 'number', 'id': 'salePrice',
                'onchange': "changePrice('quantity', 'salePrice', 'vatPrice', 'totalPrice')",
            }),
            'vatPrice': forms.TextInput(attrs={
                'class': 'form-control', 'type': 'number', 'id': 'vatPrice', 'readonly': 'readonly',
            }),
            'totalPrice': forms.TextInput(attrs={
                'class': 'form-control', 'type': 'number', 'id': 'totalPrice', 'readonly': 'readonly',
            }),
            'comment': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'comment',
            }),
        }

    def __init__(self, *args, **kwargs):
        super(BuyForm, self).__init__(*args, **kwargs)
        self.fields["client"].queryset = Company.objects.filter(Q(companyStatus='Y'))


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ('typeName', 'modelName', 'productName', 'unitPrice', 'position', 'productPicture')

        widgets = {
            'typeName': forms.Select(attrs={'class': 'form-control', 'id': 'typeName'}),
            'modelName': forms.TextInput(attrs={'class': 'form-control', 'type': 'text', 'id': 'modelName'}),
            'productName': forms.TextInput(attrs={'class': 'form-control', 'type': 'text', 'id': 'productName'}),
            'unitPrice': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'unitPrice'}),
            'position': forms.Select(attrs={'class': 'form-control', 'id': 'position'}),
            'productPicture': forms.FileInput(attrs={
                'class': 'form-control', 'id': 'productPicture',
                'onchange': "javascript:document.getElementById('productPicture').value=this.value.replace(/c:\\\\fakepath\\\\/i,'')"
            }),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)


class WarehouseForm(forms.ModelForm):

    class Meta:
        model = Warehouse
        fields = ('mainCategory', 'subCategory', 'warehouseDrawing')

        widgets = {
            'mainCategory': forms.Select(attrs={'class': 'form-control', 'id': 'mainCategory'}),
            'subCategory': forms.Select(attrs={'class': 'form-control', 'id': 'subCategory'}),
            'warehouseDrawing': forms.FileInput(attrs={
                'class': 'form-control', 'id': 'warehouseDrawing',
                'onchange': "javascript:document.getElementById('warehouseDrawing').value=this.value.replace(/c:\\\\fakepath\\\\/i,'')"}),
        }

    def __init__(self, *args, **kwargs):
        super(WarehouseForm, self).__init__(*args, **kwargs)


class DailyReportForm(forms.ModelForm):

    class Meta:
        model = DailyReport
        fields = ('workDate', 'writeEmp', 'title', 'contents', 'files')

        widgets = {
            'workDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'workDate'}),
            'writeEmp': forms.Select(attrs={'class': 'form-control', 'id': 'writeEmp'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'type': 'text', 'id': 'title'}),
            'contents': forms.Textarea(attrs={'class': 'form-control', 'id': 'contents'}),
            'files': forms.FileInput(attrs={
                'class': 'form-control', 'id': 'files',
                'onchange': "javascript:document.getElementById('files').value=this.value.replace(/c:\\\\fakepath\\\\/i,'')"}),
        }

    def __init__(self, *args, **kwargs):
        super(DailyReportForm, self).__init__(*args, **kwargs)


class DisplayForm(forms.ModelForm):

    class Meta:
        model = Display
        fields = ('postDate', 'product', 'size', 'quantity', 'comment')

        widgets = {
            'postDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'postDate'}),
            'product': forms.Select(attrs={'class': 'form-control', 'id': 'product', 'onchange': 'changeModel(this.value, "size")'}),
            'size': forms.Select(attrs={'class': 'form-control', 'id': 'size'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'quantity'}),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'id': 'comment'})
        }

    def __init__(self, *args, **kwargs):
        super(DisplayForm, self).__init__(*args, **kwargs)


class ReproductionForm(forms.ModelForm):

    class Meta:
        model = Reproduction
        fields = ('postDate', 'product', 'size', 'quantity', 'comment')

        widgets = {
            'postDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'postDate'}),
            'product': forms.Select(attrs={'class': 'form-control', 'id': 'product', 'onchange': 'changeModel(this.value, "size")'}),
            'size': forms.Select(attrs={'class': 'form-control', 'id': 'size'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'quantity'}),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'id': 'comment'})
        }

    def __init__(self, *args, **kwargs):
        super(ReproductionForm, self).__init__(*args, **kwargs)
