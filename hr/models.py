from django.db import models
from django.contrib.auth.models import User


class Employee(models.Model):
    empPositionChoices = ((1, '임원'), (2, '부장'), (3, '차장'), (4, '과장'), (5, '대리'), (6, '사원'))
    empDeptNameChoices = (('임원', '임원'), ('경영지원본부', '경영지원본부'), ('영업1팀', '영업1팀'), ('영업2팀', '영업2팀'),
                          ('영업3팀', '영업3팀'), ('인프라서비스사업팀', '인프라서비스사업팀'),
                          ('솔루션지원팀', '솔루션지원팀'), ('DB지원팀', 'DB지원팀'), ('미정', '미정'))
    statusChoices = (('Y', 'Y'), ('N', 'N'))

    empId = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    empName = models.CharField(max_length=10)
    empPosition = models.IntegerField(choices=empPositionChoices, default=6)
    empManager = models.CharField(max_length=1, choices=statusChoices, default='N')
    empPhone = models.CharField(max_length=20)
    empEmail = models.EmailField(max_length=254)
    empDeptName = models.CharField(max_length=30, choices=empDeptNameChoices, default='미정')
    dispatchCompany = models.CharField(max_length=100, default='내근')
    message = models.CharField(max_length=200, default='내근 업무 내용을 작성해 주세요.', help_text='내근 업무 내용을 작성해 주세요.')
    empStatus = models.CharField(max_length=1, choices=statusChoices, default='Y')