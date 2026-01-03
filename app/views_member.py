import os
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from .models import *
from .forms import *
from .views import context_data
from .utils import generate_qr_code
from .constants import *
from .audit_logger import audit_log_user_action
from django.core.files.uploadedfile import UploadedFile
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@login_required
def member_list(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    from .search_utils import search_members
    from .models import MemberRole
    
    context = context_data(request)
    context['page_name'] = 'List Members'
    
    # Get search query and filters from request
    search_query = request.GET.get('search', '').strip()
    is_active_filter = request.GET.get('is_active', '')
    role_filter = request.GET.get('role', '')
    join_date_from = request.GET.get('join_date_from', '')
    join_date_to = request.GET.get('join_date_to', '')
    
    # Build filters dict
    filters = {}
    if is_active_filter != '':
        filters['is_active'] = is_active_filter.lower() == 'true'
    if role_filter:
        filters['role'] = role_filter
    if join_date_from:
        filters['join_date_from'] = join_date_from
    if join_date_to:
        filters['join_date_to'] = join_date_to
    
    # Apply search and filters
    members_list = search_members(search_query, filters).order_by('-member_join_at')
    
    # Pagination
    paginator = Paginator(members_list, PAGINATION_MEMBER_LIST)
    page = request.GET.get('page', 1)
    
    try:
        members = paginator.page(page)
    except PageNotAnInteger:
        members = paginator.page(1)
    except EmptyPage:
        members = paginator.page(paginator.num_pages)
    
    context['members'] = members
    context['page_obj'] = members
    context['search_query'] = search_query
    context['is_active_filter'] = is_active_filter
    context['role_filter'] = role_filter
    context['join_date_from'] = join_date_from
    context['join_date_to'] = join_date_to
    context['roles'] = MemberRole.choices
    context['breadcrumb_items'] = [
        {'name': 'Dashboard', 'url': '/', 'icon': 'home'},
        {'name': 'Members', 'icon': 'users'},
    ]
    return render(request, 'member/list.html', context)


def is_image(file):
    """Check if uploaded file is a valid image"""
    # Get the file extension
    _, file_extension = os.path.splitext(file.name.lower())
    # Check if the file extension is in the allowed extensions list
    return file_extension in ALLOWED_IMAGE_EXTENSIONS


def validate_file_security(file):
    """Enhanced file validation with security checks"""
    from app.security_validators import validate_file_upload, sanitize_filename
    try:
        validate_file_upload(file)
        # Sanitize filename
        if hasattr(file, 'name'):
            file.name = sanitize_filename(file.name)
        return True
    except Exception as e:
        return str(e)


@login_required
def member_register(request):
    context = context_data(request)
    context['page_name'] = 'Member Register'
    if request.method == 'POST':
        form = MemberRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            member_id = form.cleaned_data['member_id']
            profile_picture = form.cleaned_data.get('member_profile_picture')

            # Check if a member with the same ID already exists
            if Member.objects.filter(member_id=member_id).exists():
                form.add_error('member_id', 'Member with this ID already exists.')
            
            # Validate profile picture if provided
            if profile_picture:
                file_validation = validate_file_security(profile_picture)
                if file_validation is not True:
                    form.add_error('member_profile_picture', file_validation)
            
            # Only proceed if no errors were added
            if not form.errors:
                # Create the Member object
                member = form.save(commit=False)

                # Create the directory for the profile picture and QR code
                profile_picture_directory = os.path.join(settings.MEDIA_ROOT, 'profiles', member_id)
                os.makedirs(profile_picture_directory, exist_ok=True)

                # Handle profile picture if provided
                if profile_picture:
                    # Set the profile picture upload path
                    profile_picture_name = f"{member_id}_profile.png"
                    profile_picture_path = os.path.join('profiles', member_id, profile_picture_name)

                    # Save the profile picture
                    with open(os.path.join(profile_picture_directory, profile_picture_name), 'wb') as profile_file:
                        for chunk in profile_picture.chunks():
                            profile_file.write(chunk)

                    member.member_profile_picture = profile_picture_path

                # Generate and save the QR code using utility function
                member.member_qr_code = generate_qr_code(member_id)
                member.save()

                return redirect('member_list')  # Redirect to a member list view

    else:
        form = MemberRegisterForm()
    
    context['form'] = form
    return render(request, 'member/register.html', context)


@login_required
def member_view(request, member_id):
    context = context_data(request)
    context['page_name'] = 'List Members'
    try:
        member = Member.objects.get(member_id=member_id)
        context['member'] = member
        return render(request, 'member/view.html', context)
    except Member.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Member not found.')
        return redirect('member_list')


@user_passes_test(lambda u: u.is_superuser)
def member_delete(request, member_id):
    from django.contrib import messages
    import shutil
    
    try:
        member = Member.objects.get(member_id=member_id)

        # Delete the profile picture if it exists
        if member.member_profile_picture:
            try:
                profile_picture_path = member.member_profile_picture.path
                if os.path.exists(profile_picture_path):
                    os.remove(profile_picture_path)
            except (ValueError, OSError):
                pass  # File doesn't exist or path is invalid

        # Delete the QR code if it exists
        if member.member_qr_code:
            try:
                qr_code_path = member.member_qr_code.path
                if os.path.exists(qr_code_path):
                    os.remove(qr_code_path)
            except (ValueError, OSError):
                pass  # File doesn't exist or path is invalid

        # Delete the member's directory if it exists
        member_directory = os.path.join(settings.MEDIA_ROOT, 'profiles', member_id)
        if os.path.exists(member_directory):
            try:
                shutil.rmtree(member_directory)
            except OSError:
                pass  # Directory doesn't exist or can't be deleted

        # Delete the Member object
        member.delete()
        messages.success(request, 'Member deleted successfully.')

        return redirect('member_list')

    except Member.DoesNotExist:
        messages.error(request, 'Member not found.')
        return redirect('member_list')


@login_required
def member_edit(request, member_id):
    context = context_data(request)
    context['page_name'] = 'Edit Member'
    try:
        member = Member.objects.get(member_id=member_id)

        if request.method == 'POST':
            import logging
            logger = logging.getLogger('app')
            logger.info(f'POST request received for member {member_id}')
            logger.info(f'POST data: {dict(request.POST)}')
            
            form = MemberEditForm(request.POST, request.FILES, instance=member, user=request.user)
                
                # Check if assigning a unique role that's already taken
                if new_role in UNIQUE_ROLES:
                    existing_member = Member.objects.filter(
                        member_role=new_role,
                        member_is_active=True
                    ).exclude(member_id=member_id).first()
                    



            # Check if a new profile picture was uploaded
            if profile_picture and hasattr(profile_picture, 'name'):
                # Only validate if it's a new upload (UploadedFile), not an existing file (ImageFieldFile)
                if isinstance(profile_picture, UploadedFile):
                    # Enhanced security validation
                    file_validation = validate_file_security(profile_picture)
                    if file_validation is not True:
                        form.add_error('member_profile_picture', file_validation)
                        context['form'] = form
                        context['member'] = member
                        return render(request, 'member/edit.html', context)
                
                # Delete old profile picture if it exists
                if member.member_profile_picture:
                    old_picture_path = member.member_profile_picture.path
                    if os.path.exists(old_picture_path):
                        os.remove(old_picture_path)

                # Set the profile picture upload path
                profile_picture_name = f"{member_id}_profile.png"
                profile_picture_path = os.path.join('profiles', member_id, profile_picture_name)

                # Create the directory for the profile picture
                profile_picture_directory = os.path.join(settings.MEDIA_ROOT, 'profiles', member_id)
                os.makedirs(profile_picture_directory, exist_ok=True)

                # Save the new profile picture
                with open(os.path.join(profile_picture_directory, profile_picture_name), 'wb') as profile_file:
                    for chunk in profile_picture.chunks():
                        profile_file.write(chunk)

                member.member_profile_picture = profile_picture_path

            # Update the member details
            member = form.save(commit=False)
            
            # Ensure ID is not changed (redundant safety check)
            member.member_id = member_id
            
            if profile_picture and hasattr(profile_picture, 'name'):
                member.member_profile_picture = os.path.join('profiles', member.member_id, f"{member.member_id}_profile.png")
            
            # For superusers, ensure member_is_active and member_role are saved
            if request.user.is_superuser:
                member_is_active = form.cleaned_data.get('member_is_active', True)
                member_role = form.cleaned_data.get('member_role', '')
                logger.info(f'Superuser update - is_active: {member_is_active}, role: {member_role}')
                member.member_is_active = member_is_active
                member.member_role = member_role
            
            logger.info(f'About to save member. Current state - ID: {member.member_id}, Role: {member.member_role}, Active: {member.member_is_active}')
            try:
                member.save()

        else:
            # Prepopulate the form with existing member data
            form = MemberEditForm(instance=member, user=request.user)

        context['form'] = form
        context['member'] = member
        return render(request, 'member/edit.html', context)

    except Member.DoesNotExist:
        # Handle the case where the member with the specified ID does not exist
        return redirect('member_list')  # Redirect to a member list view


@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST"])
def member_bulk_action(request):
    """Handle bulk actions on members"""
    try:
        action = request.POST.get('action')
        # Try both formats
        member_ids = request.POST.getlist('member_ids[]') or request.POST.getlist('member_ids')
        
        if not member_ids:
            return JsonResponse({'success': False, 'message': 'No members selected'})
        
        members = Member.objects.filter(member_id__in=member_ids)
        
        if action == 'activate':
            members.update(member_is_active=True)
            message = f'{members.count()} member(s) activated successfully'
        elif action == 'deactivate':
            members.update(member_is_active=False)
            message = f'{members.count()} member(s) deactivated successfully'
        elif action == 'delete':
            count = members.count()
            members.delete()
            message = f'{count} member(s) deleted successfully'
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action'})
        
        # Audit log
        audit_log_user_action(
            request=request,
            action=f'bulk_{action}',
            target=f'members:{len(member_ids)}',
            extra_details={
                'action': action,
                'member_count': len(member_ids),
            }
        )
        
        return JsonResponse({'success': True, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["POST"])
def member_inline_edit(request):
    """Handle inline editing of member fields"""
    try:
        member_id = request.POST.get('member_id')
        field = request.POST.get('field')
        value = request.POST.get('value')
        
        if not member_id or not field or not value:
            return JsonResponse({'success': False, 'message': 'Missing required fields'})
        
        member = Member.objects.get(member_id=member_id)
        
        # Validate field
        allowed_fields = ['member_first_name', 'member_last_name', 'member_tp_number']
        if field not in allowed_fields:
            return JsonResponse({'success': False, 'message': 'Invalid field'})
        
        # Update field
        setattr(member, field, value)
        member.save()
        
        # Audit log
        audit_log_user_action(
            request=request,
            action='member_inline_edit',
            target=f'member:{member_id}',
            extra_details={
                'field': field,
                'old_value': 'N/A',
                'new_value': value,
            }
        )
        
        return JsonResponse({'success': True, 'message': 'Field updated successfully'})
    except Member.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Member not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

