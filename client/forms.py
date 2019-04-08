from django import forms
from .models import Company

class CompanyForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = ('companyName', 'saleEmpId', 'companyAddress')

        widgets = {
            'companyName': forms.TextInput(attrs={'class': 'form-control', 'id': 'companyName'}),
            'saleEmpId': forms.Select(attrs={'class': 'form-control', 'id': "saleEmpId"}),
            'companyAddress': forms.TextInput(attrs={'class': 'form-control', 'id': 'companyAddress'}),
        }

        labels = {
            'companyName': '고객사명',
            'saleEmpId': '영업대표',
            'companyAddress': '주소',
        }
