from django import forms
from django.db.models import Q

from hr.models import Employee
from client.models import Company, Customer
from .models import Contract, Goal, Purchase


class ContractForm(forms.ModelForm):
    saleCompanyNames = forms.CharField(
        max_length=200, required=False, widget=forms.TextInput(attrs={
            'class': 'magicsearch form-control', 'id': 'saleCompanyNames', 'autocomplete': 'off', 'onkeydown': 'magicsearchtab(saleCompanyNames)'}
        )
    )
    endCompanyNames = forms.CharField(
        max_length=200, required=False, widget=forms.TextInput(attrs={
            'class': 'magicsearch form-control', 'id': 'endCompanyNames', 'autocomplete': 'off', 'onkeydown': 'magicsearchtab(endCompanyNames)'}
        )
    )

    class Meta:
        model = Contract
        fields = (
            'contractName', 'contractStep', 'empId', 'saleCompanyNames', 'saleCustomerId', 'saleTaxCustomerId', 'endCompanyNames',
            'saleType', 'saleIndustry', 'salePrice', 'profitPrice', 'profitRatio', 'contractDate', 'contractStartDate', 'contractEndDate',
            'depositCondition', 'depositConditionDay', 'contractPaper', 'modifyContractPaper', 'orderPaper', 'comment'
        )

        widgets = {
            'contractName': forms.TextInput(attrs={'class': 'form-control', 'id': 'contractName'}),
            'contractStep': forms.Select(attrs={'class': 'form-control', 'id': 'contractStep'}),
            'empId': forms.Select(attrs={'class': 'form-control', 'id': 'empId'}),
            'saleCustomerId': forms.Select(attrs={'class': 'form-control', 'id': 'saleCustomerId'}),
            'saleTaxCustomerId': forms.Select(attrs={'class': 'form-control', 'id': 'saleTaxCustomerId'}),
            'saleType': forms.Select(attrs={'class': 'form-control', 'id': "saleType", 'onchange': "typeChange()"}),
            'saleIndustry': forms.Select(attrs={'class': 'form-control', 'id': "saleIndustry"}),
            'salePrice': forms.TextInput(attrs={'class': 'form-control money', 'id': 'salePrice'}),
            'profitPrice': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profitPrice'}),
            'profitRatio': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'profitRatio', 'readonly': ''}),
            'contractDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'contractDate'}),
            'contractStartDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'contractStartDate', 'readonly': ''}),
            'contractEndDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'contractEndDate', 'readonly': ''}),
            'depositCondition': forms.Select(attrs={'class': 'form-control', 'id': 'depositCondition'}),
            'depositConditionDay': forms.TextInput(attrs={'class': 'form-control', 'id': 'depositConditionDay'}),
            'contractPaper': forms.FileInput(attrs={
                'class': 'd-none', 'id': 'contractPaper',
                'onchange': "javascript:document.getElementById('contractPaper_route').value=this.value.replace(/c:\\\\fakepath\\\\/i,'')"}),
            'modifyContractPaper': forms.Select(attrs={'class': 'form-control', 'id': 'modifyContractPaper'}),
            'orderPaper': forms.FileInput(attrs={
                'class': 'd-none', 'id': 'orderPaper',
                'onchange': "javascript:document.getElementById('orderPaper_route').value=this.value.replace(/c:\\\\fakepath\\\\/i,'')"}
            ),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'id': 'comment'}),
        }

    def __init__(self, *args, **kwargs):
        super(ContractForm, self).__init__(*args, **kwargs)
        self.fields["empId"].queryset = Employee.objects.filter(Q(empDeptName__contains='영업') & Q(empStatus='Y'))


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = (
            'empDeptName', 'empName', 'year', 'sales1', 'sales2', 'sales3', 'sales4', 'sales5', 'sales6',
            'sales7', 'sales8', 'sales9', 'sales10', 'sales11', 'sales12',
            'profit1', 'profit2', 'profit3', 'profit4', 'profit5', 'profit6',
            'profit7', 'profit8', 'profit9', 'profit10', 'profit11', 'profit12',
        )

        widgets = {
            'empDeptName': forms.Select(attrs={'class': 'form-control', 'id': 'empDeptName', 'onchange': "changeDeptName(this.value)"}),
            'empName': forms.Select(attrs={'class': 'form-control', 'id': 'empName'}),
            'year': forms.TextInput(attrs={"type": "number", "min": "1900", "max": "2099", "step": "1", 'class': 'form-control', 'id': 'year'}),
            'sales1': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales1'}),
            'sales2': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales2'}),
            'sales3': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales3'}),
            'sales4': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales4'}),
            'sales5': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales5'}),
            'sales6': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales6'}),
            'sales7': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales7'}),
            'sales8': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales8'}),
            'sales9': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales9'}),
            'sales10': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales10'}),
            'sales11': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales11'}),
            'sales12': forms.TextInput(attrs={'class': 'form-control money', 'id': 'sales12'}),
            'profit1': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit1'}),
            'profit2': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit2'}),
            'profit3': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit3'}),
            'profit4': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit4'}),
            'profit5': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit5'}),
            'profit6': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit6'}),
            'profit7': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit7'}),
            'profit8': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit8'}),
            'profit9': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit9'}),
            'profit10': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit10'}),
            'profit11': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit11'}),
            'profit12': forms.TextInput(attrs={'class': 'form-control money', 'id': 'profit12'}),
        }

    def __init__(self, *args, **kwargs):
        super(GoalForm, self).__init__(*args, **kwargs)
