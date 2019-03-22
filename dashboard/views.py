from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.http import HttpResponse
from django.template import loader

#
# def index(request):
#     template = loader.get_template('index.html')
#     context = {
#         'latest_question_list': "index",
#     }
#     return HttpResponse(template.render(context, request))
#

def dashboard(request):
    if request.user.id:
        template = loader.get_template('dashboard/index.html')
        context = {
            'latest_question_list': "index",
        }
        return HttpResponse(template.render(context, request))
    else:
        return redirect('login')
