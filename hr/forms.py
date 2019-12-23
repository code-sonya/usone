from django import forms
from .models import Employee, Department


class EmployeeForm(forms.ModelForm):

    class Meta:
        model = Employee
        fields = (
            'empCode', 'empName', 'empPosition', 'empPhone', 'empEmail', 'departmentName', 'empRank',
            'carId', 'empStartDate', 'empEndDate', 'empStatus', 'empManager', 'message', 'empSalary',
        )

        widgets = {
            'empCode': forms.TextInput(attrs={'class': 'form-control', 'id': 'empCode'}),
            'empName': forms.TextInput(attrs={'class': 'form-control', 'id': 'empName'}),
            'empPosition': forms.Select(attrs={'class': 'form-control', 'id': 'empPosition'}),
            'empPhone': forms.TextInput(attrs={'class': 'form-control', 'id': 'empPhone'}),
            'empEmail': forms.TextInput(attrs={'class': 'form-control', 'id': 'empEmail'}),
            'carId': forms.Select(attrs={'class': 'form-control', 'id': 'carId'}),
            'empStartDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'empStartDate'}),
            'empEndDate': forms.TextInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'empEndDate'}),
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
        fields = ('deptName', 'deptManager', 'deptLevel', 'parentDept')

        widgets = {
            'deptName': forms.TextInput(attrs={'class': 'form-control', 'id': 'deptName'}),
            'deptManager': forms.Select(attrs={'class': 'form-control', 'id': 'deptManager'}),
            'deptLevel': forms.TextInput(attrs={'class': 'form-control', 'id': 'deptLevel'}),
            'parentDept': forms.Select(attrs={'class': 'form-control', 'id': 'parentDept'}),
        }

    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)
