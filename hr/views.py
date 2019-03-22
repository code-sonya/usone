from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.template import loader

def profile(request):
    template = loader.get_template('profile.html')
    context = {
        'latest_question_list': "profile",
    }
    return HttpResponse(template.render(context, request))
