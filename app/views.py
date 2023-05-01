from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from app import forms

def context_data(request):
    context = {
        'page_name': '',
        'page_title': '',
        'system_title': 'Lama Samajaya',
        'nav_bar_title': 'Membership Management System',
        'author_name': 'Anjana Narasinghe',
        'nav-bar-top': True,
        'footer': True
    }

    return context


# Create your views here.
def userRegister(request):
    context = context_data(request)
    context['page_name'] = 'user_register'
    context['page_title'] = 'User Registration'
    if request.method == 'POST':
        form = forms.AddUser(request.POST)
        if form.is_valid():
            form.save()
            return redirect('#')
    else:
        form = forms.AddUser()

    context['form'] = form
    return render(request, 'userRegister.html', context)


class UserLogin(LoginView):
    template_name = 'login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_name'] = 'user_login'
        context['page_title'] = 'User Login'
        context['page_name'] = 'user_register'
        context['nav-bar-top'] = False
        context['footer'] = False
        context['system_title'] = 'Lama Samajaya'
        return context


class UserLogout(LogoutView):
    next_page = reverse_lazy('login')


def dashboard(request):
    return HttpResponse('<h1>Hello World</h1>')
