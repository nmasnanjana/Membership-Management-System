from django.contrib import messages
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import redirect, render, get_object_or_404
from .views import context_data
from .forms import *
from .constants import PAGINATION_STAFF_LIST
from .audit_logger import audit_log_security_event, audit_log_user_action


def staff_log_in(request):
    from app.security import check_account_lockout, record_failed_login, clear_login_attempts
    import logging
    
    logger = logging.getLogger('security')
    context = context_data(request)
    context['page_name'] = 'Staff Login'
    context['navbar_top'] = False
    context['footer'] = False

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Check for account lockout
        is_locked, remaining_time = check_account_lockout(username)
        if is_locked:
            minutes = remaining_time // 60
            messages.error(
                request, 
                f'Account is temporarily locked due to multiple failed login attempts. '
                f'Please try again in {minutes} minute(s).'
            )
            logger.warning(f'Login attempt on locked account: {username}')
            return render(request, 'staff/login.html', context)
        
        # Validate input
        if not username or not password:
            messages.error(request, "Please provide both username and password.")
            return render(request, 'staff/login.html', context)
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                clear_login_attempts(username)  # Clear failed attempts on success
                logger.info(f'Successful login: {username}')
                audit_log_security_event(
                    request=request,
                    event_type='login_success',
                    severity='INFO',
                    target=f'user:{username}',
                    extra_details={'username': username}
                )
                messages.success(request, "You have been logged in successfully!")
                
                # Redirect to the 'next' parameter if provided, otherwise to dashboard
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')
            else:
                messages.error(request, "Your account has been deactivated. Please contact administrator.")
                logger.warning(f'Login attempt on inactive account: {username}')
            audit_log_security_event(
                request=request,
                event_type='login_attempt_inactive_account',
                severity='WARNING',
                target=f'user:{username}',
                extra_details={'username': username}
            )
        else:
            record_failed_login(username)
            messages.error(request, "Username or Password is incorrect. Please try again.")
            logger.warning(f'Failed login attempt: {username}')
            audit_log_security_event(
                request=request,
                event_type='login_failed',
                severity='WARNING',
                target=f'user:{username}',
                extra_details={'username': username}
            )

    return render(request, 'staff/login.html', context)


@login_required
def staff_log_out(request):
    username = request.user.username if request.user.is_authenticated else 'unknown'
    logout(request)
    audit_log_security_event(
        request=request,
        event_type='logout',
        severity='INFO',
        target=f'user:{username}',
        extra_details={'username': username}
    )
    messages.success(request, "You have been logged out successfully")
    return redirect('login')


@user_passes_test(lambda u: u.is_superuser)
def staff_register(request):
    context = context_data(request)
    context['page_name'] = 'Staff Register'
    if request.method == 'POST':
        form = StaffRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Audit log: staff created
            audit_log_user_action(
                request=request,
                action='staff_created',
                target=f'user:{user.username}',
                extra_details={
                    'username': user.username,
                    'is_superuser': user.is_superuser,
                }
            )
            messages.success(request, "Staff added Successfully")
            return redirect('staff_list')
        else:
            messages.error(request, "There was an error while Registering the new user. Please try again!")
    form = StaffRegisterForm()
    context['form'] = form
    return render(request, 'staff/register.html', context)


@user_passes_test(lambda u: u.is_superuser)
def staff_list(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    context = context_data(request)
    context['page_name'] = 'Staff List'
    
    # Pagination
    users_list = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users_list, PAGINATION_STAFF_LIST)
    page = request.GET.get('page', 1)
    
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    
    context['users'] = users
    context['page_obj'] = users  # For pagination template
    return render(request, 'staff/list.html', context)


@user_passes_test(lambda u: u.is_superuser)
def staff_delete(request, staff_id):
    try:
        staff_to_delete = get_object_or_404(User, id=staff_id)
        # Prevent deleting yourself
        if staff_to_delete == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('staff_list')
        
        # Audit log: staff deletion
        username = staff_to_delete.username
        is_superuser = staff_to_delete.is_superuser
        staff_to_delete.delete()
        
        audit_log_user_action(
            request=request,
            action='staff_deleted',
            target=f'user:{username}',
            extra_details={
                'username': username,
                'was_superuser': is_superuser,
            }
        )
        
        messages.success(request, "User has been deleted successfully")
    except Exception as e:
        messages.error(request, f"Error deleting user: {str(e)}")
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
            messages.error(request, "There was an error while updating the password")

    form = PasswordChangeForm(request.user)
    context['form'] = form
    return render(request, 'staff/password_change.html', context)


@user_passes_test(lambda u: u.is_superuser)
def staff_password_reset(request, staff_id):
    context = context_data(request)
    context['page_name'] = "Password Reset"
    try:
        user = get_object_or_404(User, id=staff_id)
        if request.method == "POST":
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Password has been changed successfully")
                return redirect('staff_list')
            else:
                messages.error(request, "There has been an error while changing the password")
        form = AdminPasswordChangeForm(user)
        context['form'] = form
        context['user'] = user
        return render(request, 'staff/password_reset.html', context)
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('staff_list')


@login_required
def staff_profile_edit(request, staff_id):
    context = context_data(request)
    context['page_name'] = "Change User Profile"
    try:
        user = get_object_or_404(User, id=staff_id)
        # Users can only edit their own profile unless they're superuser
        if not request.user.is_superuser and request.user != user:
            messages.error(request, "You can only edit your own profile.")
            return redirect('dashboard')
        
        # Pass request.user to form so it can determine if admin privilege field should be shown
        form = CustomUserChangeForm(request.POST or None, instance=user, request_user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "User Profile has been updated successfully")

            # If accessed from staff management (admin user), always redirect to staff_list
            # Otherwise, redirect to dashboard (for self-editing)
            if request.user.is_superuser:
                return redirect('staff_list')
            else:
                return redirect('dashboard')

        context['form'] = form
        context['user'] = user
        return render(request, 'staff/profile_edit.html', context)
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')
