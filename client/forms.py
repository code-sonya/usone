from django import forms
from django.db.models import Q

from .models import Company
from .models import Customer
from hr.models import Employee


class CompanyForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = (
            'companyName', 'companyNumber', 'ceo', 'companyAddress',
            'companyPhone', 'companyComment', 'companyType',
        )

        widgets = {
            'companyName': forms.TextInput(attrs={'class': 'form-control', 'id': 'companyName'}),
            'companyNumber': forms.TextInput(attrs={'class': 'form-control', 'id': 'companyNumber'}),
            'ceo': forms.TextInput(attrs={'class': 'form-control', 'id': 'ceo'}),
            'companyPhone': forms.TextInput(attrs={'class': 'form-control', 'id': 'companyPhone'}),
            'companyAddress': forms.TextInput(attrs={'class': 'form-control', 'id': 'companyAddress'}),
            'companyComment': forms.TextInput(attrs={'class': 'form-control', 'id': 'companyComment'}),
            'companyType': forms.Select(attrs={'class': 'form-control', 'id': 'companyType'}),
        }

    def __init__(self, *args, **kwargs):
        super(CompanyForm, self).__init__(*args, **kwargs)


class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ('customerName',
                  'companyName',
                  'customerDeptName',
                  'customerPhone',
                  'customerEmail')

        widgets = {
            'customerName': forms.TextInput(attrs={'class': 'form-control', 'id': 'customerName'}),
            'companyName': forms.Select(attrs={'class': 'form-control', 'id': 'companyName'}),
            'customerDeptName': forms.TextInput(attrs={'class': 'form-control', 'id': "customerDeptName"}),
            'customerPhone': forms.TextInput(attrs={'class': 'form-control', 'id': "serviceEndTime"}),
            'customerEmail': forms.TextInput(attrs={'class': 'form-control', 'id': 'customerEmail'}),
        }

        labels = {
            'customerName': '담당자 명',
            'companyName' : '고객사 명',
            'customerDeptName': '담당자 부서',
            'customerPhone': '담당자 연락처',
            'customerEmail': '담당자 이메일',
        }

