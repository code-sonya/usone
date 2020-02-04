from django import forms
from django.db.models import Q

from hr.models import Employee
from .models import CenterManager


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