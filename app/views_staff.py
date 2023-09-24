from django.contrib import messages
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from .views import context_data
from .forms import *


def staff_log_in(request):
    context = context_data(request)
    context['page_name'] = 'Staff Login'
    context['navbar_top'] = False
    context['footer'] = False

    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "You have been logged in successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Username or Password is Wrong please Try Again!")
            return redirect('login')

    else:
        return render(request, 'staff/login.html', context)


@login_required
def staff_log_out(request):
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect('login')


@user_passes_test(lambda u: u.is_superuser)
def staff_register(request):
    context = context_data(request)
    context['page_name'] = 'Staff Register'
    if request.method == 'POST':
        form = StaffRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff added Successfully")
            return redirect('staff_list')
        else:
            messages.success(request, "There was an error while Registering the new user. Please try again!")
    form = StaffRegisterForm()
    context['form'] = form
    return render(request, 'staff/register.html', context)


@user_passes_test(lambda u: u.is_superuser)
def staff_list(request):
    context = context_data(request)
    context['page_name'] = 'Staff List'
    users = User.objects.all()
    context['users'] = users
    return render(request, 'staff/list.html', context)


@user_passes_test(lambda u: u.is_superuser)
def staff_delete(request, staff_id):
    staff_to_delete = User.objects.get(id=staff_id)
    messages.success(request, "User have been deleted successfully")
    staff_to_delete.delete()
    return redirect('staff_list')


@login_required
def staff_password_change(request):
    context = context_data(request)
    context['page_name'] = ' Change Password'
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Password change successfully")
            return redirect('dashboard')
        else:
            messages.success(request, "There was an error while updating the password")

    form = PasswordChangeForm(request.user)
    context['form'] = form
    return render(request, 'staff/password_change.html', context)


@user_passes_test(lambda u: u.is_superuser)
def staff_password_reset(request, staff_id):
    context = context_data(request)
    context['page_name'] = "Password Rest"
    user = User.objects.get(id=staff_id)
    if request.method == "POST":
        form = AdminPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password has been changed successfully")
            return redirect('staff_list')
        else:
            messages.success(request, "There has been a error while changing the password")
    form = AdminPasswordChangeForm(user)
    context['form'] = form
    context['user'] = user
    return render(request, 'staff/password_reset.html', context)


@login_required
def staff_profile_edit(request, staff_id):
    context = context_data(request)
    context['page_name'] = "Change User Profile"
    user = User.objects.get(id=staff_id)
    form = CustomUserChangeForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        messages.success(request, "User Profile has been updated successfully")

        if user.is_superuser:
            return redirect('staff_list')
        else:
            return redirect('dashboard')

    context['form'] = form
    context['user'] = user
    return render(request, 'staff/profile_edit.html', context)
