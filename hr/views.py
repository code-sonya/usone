# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import loader


@login_required
def profile(request):
    template = loader.get_template('hr/profile.html')
    userId = request.user.id
    user = User.objects.get(id=userId)
    if request.method == "POST":
        postMessage = request.POST['message']
        user.employee.message = postMessage
        user.save()
        context = {
            'user': user,
        }
        return HttpResponse(template.render(context, request))
    else:
        context = {
            'user': user,
        }
        return HttpResponse(template.render(context, request))
