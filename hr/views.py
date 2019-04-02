from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.models import User

def profile(request):
    template = loader.get_template('hr/profile.html')
    userId = request.user.id  # 로그인 유무 판단 변수
    user = User.objects.get(id=userId)
    if userId:

        if request.method == "POST":

            postMessage = request.POST['message']
            print(postMessage)
            user.employee.message=postMessage
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

    else:
        return redirect('login')



