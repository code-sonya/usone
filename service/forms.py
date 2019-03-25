from django import forms

from .models import Servicereport
from client.models import Company, Customer

import datetime


class ServicereportForm(forms.ModelForm):
    startdate = forms.CharField(max_length = 16,widget = forms.TextInput(attrs={'class': 'form-control','type': 'date','id':'startdate','onchange':"showVal(this.value)"}),label = '시작 일자')
    starttime = forms.CharField(max_length = 16,widget = forms.TextInput(attrs={'class': 'form-control','type': 'time','id':'starttime'}),label = '시작 시간')
    finishdate = forms.CharField(max_length = 16,widget = forms.TextInput(attrs={'class': 'form-control','type': 'date','id':'finishdate'}),label = '종료 일자')
    finishtime = forms.CharField(max_length = 16,widget = forms.TextInput(attrs={'class': 'form-control','type': 'time','id':'finishtime'}),label = '종료 시간')

    class Meta:
        model = Servicereport
        fields = ('companyName','serviceType',
                  'startdate','starttime','finishdate','finishtime',
                  'serviceLocation','directgo','serviceTitle','serviceDetails')

        widgets = {
            'companyName': forms.Select(attrs={'class': 'form-control','id':'company'}),
            'serviceType': forms.Select(attrs={'class': 'form-control' ,'onchange':'chageLangSelect()' , 'id' : "selectBox"}),
            'serviceLocation': forms.Select(attrs={'class': 'form-control','id':'location'}),
            'directgo': forms.Select(attrs={'class': 'form-control','id':'jigchul'}),
            'serviceTitle': forms.TextInput(attrs={'class': 'form-control','id':'title'}),
            'serviceDetails': forms.Textarea(attrs={'class': 'form-control'}),
        }

        labels = {
            'companyName': '고객사 명',
            'serviceType': '지원 타입',
            'serviceLocation': '지역 구분',
            'directgo':'직출 여부',
            'serviceDetails': '지원 내용'
        }

    def __init__(self, *args, **kwargs):
        super(ServicereportForm, self).__init__(*args, **kwargs)
        self.fields["startdate"].initial = str(datetime.datetime.now())[:10]
        self.fields["starttime"].initial = '09:00'
        self.fields["finishdate"].initial = str(datetime.datetime.now())[:10]
        self.fields["finishtime"].initial = '18:00'
        self.fields["companyName"].queryset = Company.objects.filter(companyStatus = 'Y').order_by('companyName')