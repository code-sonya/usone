from django import forms

from client.models import Company, Customer
from .models import Contract


class OpportunityForm(forms.ModelForm):

    class Meta:
        model = Contract
        fields = ('contractName', 'empId', 'saleCompanyName', 'saleCustomerId', 'endCompanyName', 'endCustomerId', 'saleType', 'saleIndustry',
                  'predictSalePrice', 'predictProfitPrice', 'predictProfitRatio', 'predictContractDate')

        widgets = {
            'contractName': forms.TextInput(attrs={'class': 'form-control', 'id': 'contractName'}),
            'empId': forms.Select(attrs={'class': 'form-control', 'id': 'empId'}),
            'saleCompanyName': forms.Select(attrs={'class': 'form-control', 'id': 'saleCompanyName'}),
            'saleCustomerId': forms.Select(attrs={'class': 'form-control', 'id': 'saleCustomerId'}),
            'endCompanyName': forms.Select(attrs={'class': 'form-control', 'id': 'endCompanyName'}),
            'endCustomerId': forms.Select(attrs={'class': 'form-control', 'id': 'endCustomerId'}),
            'saleType': forms.Select(attrs={'class': 'form-control', 'id': "saleType"}),
            'saleIndustry': forms.Select(attrs={'class': 'form-control', 'id': "saleIndustry"}),
            'predictSalePrice': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'predictSalePrice'}),
            'predictProfitPrice': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'predictProfitPrice'}),
            'predictProfitRatio': forms.TextInput(attrs={'class': 'form-control', 'type': 'number', 'id': 'predictProfitRatio'}),
            'predictContractDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'predictContractDate'}),
        }

    def __init__(self, *args, **kwargs):
        super(OpportunityForm, self).__init__(*args, **kwargs)
        self.fields["saleCompanyName"].queryset = Company.objects.all().order_by('companyName')
        self.fields["saleCustomerId"].queryset = Customer.objects.all().order_by('customerName')
        self.fields["endCompanyName"].queryset = Company.objects.all().order_by('companyName')
        self.fields["endCustomerId"].queryset = Customer.objects.all().order_by('customerName')
