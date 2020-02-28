from django import forms
from django.contrib.auth.models import User
from .models import Eventday


class EventdayForm(forms.ModelForm):

    class Meta:
        model = Eventday
        fields = ('eventDate', 'eventName', 'eventType')

        widgets = {
            'eventDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'eventDate'}),
            'eventName': forms.TextInput(attrs={'class': 'form-control', 'id': 'eventName'}),
            'eventType': forms.Select(attrs={'class': 'form-control', 'id': 'eventType'}),
        }
