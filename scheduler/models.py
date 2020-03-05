# -*- coding: utf-8 -*-
from django.db import models


class Eventday(models.Model):
    eventTypeChoices = (
        ('휴일', '휴일'),
        ('사내일정', '사내일정'),
        ('프로젝트일정', '프로젝트일정'),
    )
    eventDate = models.DateField(primary_key=True)
    eventName = models.CharField(max_length=10)
    eventType = models.CharField(max_length=10, choices=eventTypeChoices, default='휴일')

    def __str__(self):
        return 'Eventday : {} {}'.format(self.eventDate, self.eventName)
