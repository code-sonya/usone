from django import forms
from .models import Board


class BoardForm(forms.ModelForm):

    class Meta:
        model = Board
        fields = ('boardTitle', 'boardDetails', 'boardFiles')

        widgets = {
            'boardTitle': forms.TextInput(attrs={'class': 'form-control', 'id': 'boardTitle'}),
            'boardDetails': forms.Textarea(attrs={'class': 'form-control', 'id': 'boardDetails', 'rows': '20'}),
            'boardFiles': forms.FileInput(attrs={'class': 'd-none', 'id': 'boardFiles',
                                                 'onchange': "javascript:document.getElementById('file_route').value=this.value.replace(/c:\\\\fakepath\\\\/i,'')"}),
        }

        labels = {
            'boardTitle': '제목',
            'boardDetails': '본문',
            'boardFiles': '첨부파일',
        }
