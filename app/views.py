from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from app import forms
from app import models

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
            return redirect('dashboard')
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


def member_register(request):
    context = context_data(request)
    context['page_name'] = 'member_register'
    context['page_title'] = 'Member Registration'
    if request.method == 'POST':
        form = forms.MemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.save()
            """form.save()"""
            return redirect('dashboard')
    else:
        form = forms.MemberForm()

    context['form'] = form
    return render(request, 'member_register.html', context)




def member_list(request):
    members = models.Member.objects.all()

    # Sorting
    sort_by = request.GET.get('sort_by', '')
    if sort_by == 'member_id':
        members = members.order_by('member_id')
    elif sort_by == 'birthday':
        members = members.order_by('birthday')

    # Searching
    query = request.GET.get('q')
    if query:
        members = members.filter(
            name__icontains=query) | members.filter(
            member_id__icontains=query) | members.filter(
            bank_account_number__icontains=query) | members.filter(
            contact_number__icontains=query)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(members, 10)
    try:
        members = paginator.page(page)
    except PageNotAnInteger:
        members = paginator.page(1)
    except EmptyPage:
        members = paginator.page(paginator.num_pages)

    return render(request, 'member_list.html', {
        'members': members,
        'sort_by': sort_by,
        'query': query,
    })

def member_detail(request, pk):
    member = get_object_or_404(models.Member, pk='%04d' % pk)
    return render(request, 'member_detail.html', {'member': member})

def member_edit(request, pk):
    member = get_object_or_404(models.Member, pk='%04d' % pk)
    if request.method == 'POST':
        form = forms.MemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            member = form.save(commit=False)
            member.save()
            return redirect('member_list')
    else:
        form = forms.MemberForm(instance=member)
    return render(request, 'member_edit.html', {'form': form, 'member': member})

def member_delete(request, pk):
    print('pk ', pk)
    member = get_object_or_404(models.Member, pk='%04d' % pk)
    member.delete()
    return redirect('member_list')

