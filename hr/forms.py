from django import forms
from django.contrib.auth.models import User
from .models import Employee, Department, Position


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('username', 'password')

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'id': 'username'}),
            'password': forms.TextInput(attrs={'class': 'form-control', 'id': 'password'}),
        }


class EmployeeForm(forms.ModelForm):

    class Meta:
        model = Employee
        fields = (
            'empCode', 'empName', 'empPosition', 'empPhone', 'empEmail', 'departmentName', 'empRank', 'empRewardAvailable',
            'carId', 'empStartDate', 'empEndDate', 'empStatus', 'empManager', 'message', 'empSalary',
        )

        widgets = {
            'empCode': forms.TextInput(attrs={'class': 'form-control', 'id': 'empCode'}),
            'empName': forms.TextInput(attrs={'class': 'form-control', 'id': 'empName'}),
            'empPosition': forms.Select(attrs={'class': 'form-control', 'id': 'empPosition'}),
            'empPhone': forms.TextInput(attrs={'class': 'form-control', 'id': 'empPhone'}),
            'empEmail': forms.TextInput(attrs={'class': 'form-control', 'id': 'empEmail'}),
            'carId': forms.Select(attrs={'class': 'form-control', 'id': 'carId'}),
            'empRewardAvailable': forms.Select(attrs={'class': 'form-control', 'id': 'empRewardAvailable'}),
            'empStartDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'empStartDate'}),
            'empEndDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'empEndDate'}),
            'empStatus': forms.Select(attrs={'class': 'form-control', 'id': 'empStatus'}),
            'empManager': forms.Select(attrs={'class': 'form-control', 'id': 'empManager'}),
            'message': forms.TextInput(attrs={'class': 'form-control', 'id': 'message'}),
            'departmentName': forms.Select(attrs={'class': 'form-control', 'id': 'departmentName'}),
            'empSalary': forms.TextInput(attrs={'class': 'form-control', 'id': 'empSalary'}),
            'empRank': forms.TextInput(attrs={'class': 'form-control', 'id': 'empRank'}),
        }

    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)


class DepartmentForm(forms.ModelForm):

    class Meta:
        model = Department
        fields = ('deptName', 'deptManager', 'deptLevel', 'parentDept', 'startDate', 'endDate',)

        widgets = {
            'deptName': forms.TextInput(attrs={'class': 'form-control', 'id': 'deptName'}),
            'deptManager': forms.Select(attrs={'class': 'form-control', 'id': 'deptManager'}),
            'deptLevel': forms.TextInput(attrs={'class': 'form-control', 'id': 'deptLevel'}),
            'parentDept': forms.Select(attrs={'class': 'form-control', 'id': 'parentDept'}),
            'startDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'startDate'}),
            'endDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'max': '9999-12-31', 'id': 'endDate'}),
        }

    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)


class PositionForm(forms.ModelForm):

    class Meta:
        model = Position
        fields = ('positionName', 'positionRank', 'positionSalary')

        widgets = {
            'positionName': forms.TextInput(attrs={'class': 'form-control', 'id': 'positionName'}),
            'positionRank': forms.TextInput(attrs={'class': 'form-control', 'id': 'positionRank', 'type': 'number'}),
            'positionSalary': forms.TextInput(attrs={'class': 'form-control', 'id': 'positionSalary', 'type': 'number'}),
        }

    def __init__(self, *args, **kwargs):
        super(PositionForm, self).__init__(*args, **kwargs)
