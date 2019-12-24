from django import forms

from client.models import Company
from .models import Servicereport, Serviceform, Servicetype


class ServicereportForm(forms.ModelForm):
    startdate = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'date', "max": '9999-12-31', 'id': 'startdate', 'onchange': 'showVal(this.value)'
    }))
    starttime = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'time', 'id': 'starttime'
    }))
    enddate = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'date', "max": '9999-12-31', 'id': 'enddate'
    }))
    endtime = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'time', 'id': 'endtime'
    }))
    coWorkers = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={
        'class': 'magicsearch form-control', 'id': 'coWorkers', 'autocomplete': 'off'
    }))
    contracts = forms.CharField(max_length=300, required=False, widget=forms.TextInput(attrs={
        'class': 'magicsearch form-control', 'id': 'contracts', 'autocomplete': 'off', 'onkeydown': 'magicsearchtab(contracts)'
    }))

    class Meta:
        model = Servicereport
        fields = ('contractId', 'companyName', 'serviceType',
                  'startdate', 'starttime', 'enddate', 'endtime',
                  'serviceLocation', 'directgo', 'coWorkers', 'serviceTitle', 'serviceDetails')

        widgets = {
            'companyName': forms.TextInput(attrs={'class': 'form-control magicsearch', 'id': 'companyName', 'autocomplete': 'off', 'onkeydown': 'magicsearchtab(companyName)'}),
            'serviceType': forms.Select(attrs={'class': 'form-control', 'id': "serviceType"}),
            'serviceLocation': forms.Select(attrs={'class': 'form-control', 'id': 'serviceLocation'}),
            'directgo': forms.Select(attrs={'class': 'form-control', 'id': 'directgo'}),
            'serviceTitle': forms.TextInput(attrs={'class': 'form-control', 'id': 'serviceTitle'}),
            'serviceDetails': forms.Textarea(attrs={'class': 'form-control', 'id': 'serviceDetails'}),
        }

    def __init__(self, *args, **kwargs):
        super(ServicereportForm, self).__init__(*args, **kwargs)
        self.fields["companyName"].queryset = Company.objects.filter(companyStatus='Y').order_by('companyName')


class ServiceformForm(forms.ModelForm):

    class Meta:
        model = Serviceform
        fields = ('companyName', 'serviceType',
                  'serviceStartTime', 'serviceEndTime',
                  'serviceLocation', 'directgo', 'serviceTitle', 'serviceDetails')

        widgets = {
            'companyName': forms.Select(attrs={'class': 'form-control', 'id': 'companyName'}),
            'serviceType': forms.Select(attrs={'class': 'form-control', 'id': "serviceType"}),
            'serviceStartTime': forms.TextInput(attrs={'class': 'form-control', 'id': "serviceStartTime", 'type': 'time'}),
            'serviceEndTime': forms.TextInput(attrs={'class': 'form-control', 'id': "serviceEndTime", 'type': 'time'}),
            'serviceLocation': forms.Select(attrs={'class': 'form-control', 'id': 'serviceLocation'}),
            'directgo': forms.Select(attrs={'class': 'form-control', 'id': 'directgo'}),
            'serviceTitle': forms.TextInput(attrs={'class': 'form-control', 'id': 'serviceTitle'}),
            'serviceDetails': forms.Textarea(attrs={'class': 'form-control', 'id': 'serviceDetails'}),
        }

    def __init__(self, *args, **kwargs):
        super(ServiceformForm, self).__init__(*args, **kwargs)
        self.fields["companyName"].queryset = Company.objects.filter(companyStatus='Y').order_by('companyName')


class AdminServiceForm(forms.ModelForm):
    begindate = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'date', "max": '9999-12-31', 'id': 'begindate',
    }))
    begintime = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'time', 'id': 'begintime',
    }))
    startdate = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'date', "max": '9999-12-31', 'id': 'startdate'
    }))
    starttime = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'time', 'id': 'starttime'
    }))
    enddate = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'date', "max": '9999-12-31', 'id': 'enddate'
    }))
    endtime = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'time', 'id': 'endtime'
    }))
    finishdate = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'date', "max": '9999-12-31', 'id': 'finishdate'
    }))
    finishtime = forms.CharField(max_length=16, widget=forms.TextInput(attrs={
        'class': 'form-control', 'type': 'time', 'id': 'finishtime'
    }))
    coWorkers = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={
        'class': 'magicsearch form-control', 'id': 'coWorkers', 'autocomplete': 'off', 'readonly': 'readonly',
    }))
    contracts = forms.CharField(max_length=300, required=False, widget=forms.TextInput(attrs={
        'class': 'magicsearch form-control', 'id': 'contracts', 'autocomplete': 'off', 'onkeydown': 'magicsearchtab(contracts)',
        'readonly': 'readonly',
    }))
    beginLatitude = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'beginLatitude'
    }))
    beginLongitude = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'beginLongitude'
    }))
    startLatitude = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'startLatitude'
    }))
    startLongitude = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'startLongitude'
    }))
    endLatitude = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'endLatitude'
    }))
    endLongitude = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'endLongitude'
    }))
    finishLatitude = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'finishLatitude'
    }))
    finishLongitude = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'class': 'form-control', 'id': 'finishLongitude'
    }))

    class Meta:
        model = Servicereport
        fields = (
            'contractId', 'companyName', 'serviceType', 'startdate', 'starttime', 'enddate', 'endtime', 'serviceLocation', 'directgo',
            'coWorkers', 'serviceTitle', 'serviceDetails')

        widgets = {
            'companyName': forms.TextInput(attrs={
                'class': 'form-control magicsearch', 'id': 'companyName', 'autocomplete': 'off', 'onkeydown': 'magicsearchtab(companyName)',
                'readonly': 'readonly',
            }),
            'serviceType': forms.Select(attrs={
                'class': 'form-control', 'id': "serviceType", 'readonly': 'readonly',
            }),
            'serviceLocation': forms.Select(attrs={
                'class': 'form-control', 'id': 'serviceLocation', 'readonly': 'readonly',
            }),
            'directgo': forms.Select(attrs={
                'class': 'form-control', 'id': 'directgo', 'readonly': 'readonly',
            }),
            'serviceTitle': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'serviceTitle', 'readonly': 'readonly',
            }),
            'serviceDetails': forms.Textarea(attrs={
                'class': 'form-control', 'id': 'serviceDetails', 'readonly': 'readonly',
            }),
        }


class ServiceTypeForm(forms.ModelForm):

    class Meta:
        model = Servicetype
        fields = ('typeName', 'orderNumber')

        widgets = {
            'typeName': forms.TextInput(attrs={'class': 'form-control', 'id': 'typeName'}),
            'orderNumber': forms.TextInput(attrs={'class': 'form-control', 'id': "orderNumber"}),
        }
