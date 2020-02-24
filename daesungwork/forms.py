from django import forms
from django.db.models import Q

from hr.models import Employee
from .models import CenterManager, Sale, Size, Product, Warehouse
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
            'saleDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'saleDate'}),
            'affiliate': forms.Select(attrs={'class': 'form-control', 'id': 'affiliate'}),
            'client': forms.Select(attrs={'class': 'form-control', 'id': "client"}),
            'product': forms.Select(attrs={'class': 'form-control', 'id': 'product'}),
            'size': forms.Select(attrs={'class': 'form-control', 'id': 'size'}),
            'unitPrice': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'unitPrice'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'quantity'}),
            'salePrice': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'salePrice'}),
        }

    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        self.fields["client"].queryset = Company.objects.filter(Q(companyStatus='Y'))
        # self.fields["size"].queryset = Size.objects.filter(Q(productId=self.fields["product"]["productId"]))


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ('modelName', 'productName', 'unitPrice', 'position', 'productPicture')

        widgets = {
            'modelName': forms.TextInput(attrs={'class': 'form-control', 'type': 'text', 'id': 'modelName'}),
            'productName': forms.TextInput(attrs={'class': 'form-control', 'type': 'text', 'id': 'productName'}),
            'unitPrice': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'unitPrice'}),
            'position': forms.Select(attrs={'class': 'form-control', 'id': 'position'}),
            'productPicture': forms.FileInput(attrs={
                'class': 'form-control-file', 'id': 'productPicture',
                'onchange': "javascript:document.getElementById('productPicture').value=this.value.replace(/c:\\\\fakepath\\\\/i,'')"}),
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
                'class': 'form-control-file', 'id': 'warehouseDrawing',
                'onchange': "javascript:document.getElementById('warehouseDrawing').value=this.value.replace(/c:\\\\fakepath\\\\/i,'')"}),
        }

    def __init__(self, *args, **kwargs):
        super(WarehouseForm, self).__init__(*args, **kwargs)


