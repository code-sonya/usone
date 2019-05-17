from django import forms
from django.db.models import Q

from hr.models import Employee
from client.models import Company, Customer
from .models import Contract, Goal


class ContractForm(forms.ModelForm):

    class Meta:
        model = Contract
        fields = ('contractCode', 'contractName', 'contractStep', 'empId', 'saleCompanyName', 'saleCustomerId', 'endCompanyName', 'saleType', 'saleIndustry',
                  'salePrice', 'profitPrice', 'profitRatio', 'contractDate', 'contractStartDate', 'contractEndDate', 'comment')

        widgets = {
            'contractCode': forms.TextInput(attrs={'class': 'form-control', 'id': 'contractName'}),
            'contractName': forms.TextInput(attrs={'class': 'form-control', 'id': 'contractName'}),
            'contractStep': forms.Select(attrs={'class': 'form-control', 'id': 'contractStep'}),
            'empId': forms.Select(attrs={'class': 'form-control', 'id': 'empId'}),
            'saleCompanyName': forms.Select(attrs={'class': 'form-control', 'id': 'saleCompanyName', 'onchange': "companyChange(this.value,'saleCustomerId')"}),
            'saleCustomerId': forms.Select(attrs={'class': 'form-control', 'id': 'saleCustomerId'}),
            'endCompanyName': forms.Select(attrs={'class': 'form-control', 'id': 'endCompanyName'}),
            'saleType': forms.Select(attrs={'class': 'form-control', 'id': "saleType"}),
            'saleIndustry': forms.Select(attrs={'class': 'form-control', 'id': "saleIndustry"}),
            'salePrice': forms.TextInput(attrs={'class': 'form-control money', 'id': 'salePrice'}),
            'profitPrice': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profitPrice'}),
            'profitRatio': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'profitRatio', 'readonly': ''}),
            'contractDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'contractDate'}),
            'contractStartDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'contractStartDate', 'readonly': ''}),
            'contractEndDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'contractEndDate', 'readonly': ''}),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'id': 'comment'}),
        }

    def __init__(self, *args, **kwargs):
        super(ContractForm, self).__init__(*args, **kwargs)
        self.fields["empId"].queryset = Employee.objects.filter(Q(empDeptName__contains='영업') & Q(empStatus='Y'))
        self.fields["saleCompanyName"].queryset = Company.objects.all().order_by('companyName')
        self.fields["endCompanyName"].queryset = Company.objects.all().order_by('companyName')


class GoalForm(forms.ModelForm):

    # empDeptName = forms.CharField(widget=forms.Select(attrs={'class': 'form-control', 'id': 'empDeptName', 'onchange': "changeDeptName(this.value)"}))
    # empName = forms.CharField(widget=forms.Select(attrs={'class': 'form-control', 'id': 'empName'}))

    class Meta:
        model = Goal
        fields = ('empDeptName','empName', 'year', 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec')

        widgets = {
            'empDeptName': forms.Select(attrs={'class': 'form-control', 'id': 'empDeptName', 'onchange': "changeDeptName(this.value)"}),
            'empName': forms.Select(attrs={'class': 'form-control', 'id': 'empName'}),
            'year': forms.TextInput(attrs={"type":"number" ,"min":"1900" ,"max":"2099", "step":"1", 'class': 'form-control', 'id': 'year'}),
            'jan': forms.TextInput(attrs={'class': 'form-control', 'id': 'jan'}),
            'feb': forms.TextInput(attrs={'class': 'form-control', 'id': 'feb'}),
            'mar': forms.TextInput(attrs={'class': 'form-control', 'id': 'mar'}),
            'apr': forms.TextInput(attrs={'class': 'form-control', 'id': 'apr'}),
            'may': forms.TextInput(attrs={'class': 'form-control', 'id': 'may'}),
            'jun': forms.TextInput(attrs={'class': 'form-control', 'id': 'jun'}),
            'jul': forms.TextInput(attrs={'class': 'form-control', 'id': 'jul'}),
            'aug': forms.TextInput(attrs={'class': 'form-control', 'id': 'aug'}),
            'sep': forms.TextInput(attrs={'class': 'form-control', 'id': 'sep'}),
            'oct': forms.TextInput(attrs={'class': 'form-control', 'id': 'oct'}),
            'nov': forms.TextInput(attrs={'class': 'form-control', 'id': 'nov'}),
            'dec': forms.TextInput(attrs={'class': 'form-control', 'id': 'dec'}),
        }

    def __init__(self, *args, **kwargs):
        super(GoalForm, self).__init__(*args, **kwargs)