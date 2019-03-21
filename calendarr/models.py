from django.db import models


class Eventday(models.Model):
    eventDate = models.DateField(primary_key=True)
    eventName = models.CharField(max_length=10)
    eventStartDatetime = models.DateTimeField()
    eventEndDatetime = models.DateTimeField()

    def __str__(self):
        return 'Eventday : {} {}'.format(self.eventDate, self.eventName)
