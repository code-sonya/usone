from django import forms

from .models import Servicereport
from client.models import Company, Customer

import datetime


class ServicereportForm(forms.ModelForm):
    startdate = forms.CharField(max_length=16, widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'startdate', 'onchange': "showVal(this.value)"}))
    starttime = forms.CharField(max_length=16, widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'time', 'id': 'starttime'}))
    enddate = forms.CharField(max_length=16, widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'enddate'}))
    endtime = forms.CharField(max_length=16, widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'time', 'id': 'endtime'}))

    class Meta:
        model = Servicereport
        fields = ('companyName', 'serviceType',
                  'startdate', 'starttime', 'enddate', 'endtime',
                  'serviceLocation', 'directgo', 'serviceTitle', 'serviceDetails')

        widgets = {
            'companyName': forms.Select(attrs={'class': 'form-control', 'id': 'companyName'}),
            'serviceType': forms.Select(attrs={'class': 'form-control', 'id': "serviceType"}),
            'serviceLocation': forms.Select(attrs={'class': 'form-control', 'id': 'serviceLocation'}),
            'directgo': forms.Select(attrs={'class': 'form-control', 'id': 'directgo'}),
            'serviceTitle': forms.TextInput(attrs={'class': 'form-control', 'id': 'serviceTitle'}),
            'serviceDetails': forms.Textarea(attrs={'class': 'form-control', 'id': 'serviceDetails'}),
        }

    def __init__(self, *args, **kwargs):
        super(ServicereportForm, self).__init__(*args, **kwargs)
        self.fields["companyName"].queryset = Company.objects.filter(companyStatus='Y').order_by('companyName')
