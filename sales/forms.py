from django import forms
from django.db.models import Q

from hr.models import Employee
from client.models import Company, Customer
from .models import Contract


class ContractForm(forms.ModelForm):

    class Meta:
        model = Contract
        fields = ('contractName', 'contractStep', 'empId', 'saleCompanyName', 'saleCustomerId', 'endCompanyName', 'saleType', 'saleIndustry',
                  'salePrice', 'profitPrice', 'profitRatio', 'contractDate', 'contractStartDate', 'contractEndDate', 'comment')

        widgets = {
            'contractName': forms.TextInput(attrs={'class': 'form-control', 'id': 'contractName'}),
            'contractStep': forms.Select(attrs={'class': 'form-control', 'id': 'contractStep'}),
            'empId': forms.Select(attrs={'class': 'form-control', 'id': 'empId'}),
            'saleCompanyName': forms.Select(attrs={'class': 'form-control', 'id': 'saleCompanyName', 'onchange': "companyChange(this.value,'saleCustomerId')"}),
            'saleCustomerId': forms.Select(attrs={'class': 'form-control', 'id': 'endCustomerId'}),
            'endCompanyName': forms.Select(attrs={'class': 'form-control', 'id': 'endCompanyName', 'onchange': "companyChange(this.value,'endCustomerId')"}),
            'saleType': forms.Select(attrs={'class': 'form-control', 'id': "saleType"}),
            'saleIndustry': forms.Select(attrs={'class': 'form-control', 'id': "saleIndustry"}),
            'salePrice': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'salePrice'}),
            'profitPrice': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'profitPrice'}),
            'profitRatio': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'profitRatio', 'readonly': ''}),
            'contractDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'contractDate'}),
            'contractStartDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'contractStartDate'}),
            'contractEndDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'contractEndDate'}),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'id': 'comment'}),
        }

    def __init__(self, *args, **kwargs):
        super(ContractForm, self).__init__(*args, **kwargs)
        self.fields["empId"].queryset = Employee.objects.filter(Q(empDeptName__contains='영업') & Q(empStatus='Y'))
        self.fields["saleCompanyName"].queryset = Company.objects.all().order_by('companyName')
        self.fields["endCompanyName"].queryset = Company.objects.all().order_by('companyName')
