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


@login_required
def member_list(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    context = context_data(request)
    context['page_name'] = 'List Members'
    
    # Optimize query - only fetch what we need
    members_list = Member.objects.all().order_by('-member_join_at')
    
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
    context['page_obj'] = members  # For pagination template
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

                # Audit log: member created
                audit_log_user_action(
                    request=request,
                    action='member_created',
                    target=f'member:{member_id}',
                    extra_details={
                        'member_id': member_id,
                        'member_name': f'{member.member_initials} {member.member_first_name} {member.member_last_name}',
                    }
                )

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

        # Audit log: member deletion
        member_name = f'{member.member_initials} {member.member_first_name} {member.member_last_name}'
        
        # Delete the Member object
        member.delete()
        
        # Audit log: member deleted
        audit_log_user_action(
            request=request,
            action='member_deleted',
            target=f'member:{member_id}',
            extra_details={
                'member_id': member_id,
                'member_name': member_name,
            }
        )
        
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
            form = MemberEditForm(request.POST, request.FILES, instance=member, user=request.user)
            if not form.is_valid():
                # Form is invalid - display errors
                import logging
                logger = logging.getLogger('app')
                logger.error(f'Form validation failed: {form.errors}')
                from django.contrib import messages
                messages.error(request, f'Please correct the errors below: {form.errors}')
                context['form'] = form
                context['member'] = member
                return render(request, 'member/edit.html', context)
            
            # Form is valid - proceed with update
                new_member_id = form.cleaned_data['member_id']
                profile_picture = form.cleaned_data.get('member_profile_picture')
                
                # Role validation (only for superusers)
                if request.user.is_superuser:
                    new_role = form.cleaned_data.get('member_role', '')
                    from .constants import UNIQUE_ROLES
                    
                    # Check if assigning a unique role that's already taken
                    if new_role in UNIQUE_ROLES:
                        existing_member = Member.objects.filter(
                            member_role=new_role,
                            member_is_active=True
                        ).exclude(member_id=member_id).first()
                        
                        if existing_member:
                            form.add_error(
                                'member_role',
                                f'This role is already assigned to {existing_member.member_initials} {existing_member.member_first_name} {existing_member.member_last_name}. Only one member can have this role.'
                            )
                            context['form'] = form
                            context['member'] = member
                            return render(request, 'member/edit.html', context)

                # Check if the new member ID is different from the current one
                if new_member_id != member_id:
                    # Check if the new member ID already exists (excluding current member)
                    if Member.objects.filter(member_id=new_member_id).exclude(member_id=member_id).exists():
                        form.add_error('member_id', 'Member with this ID already exists.')
                        context['form'] = form
                        context['member'] = member
                        return render(request, 'member/edit.html', context)

                # Check if a new profile picture was uploaded
                if profile_picture and hasattr(profile_picture, 'name'):
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

                    # Set the profile picture upload path - use member.member_id (will be updated if changed)
                    profile_picture_name = f"{new_member_id}_profile.png"
                    profile_picture_path = os.path.join('profiles', new_member_id, profile_picture_name)

                    # Create the directory for the profile picture (use new_member_id)
                    profile_picture_directory = os.path.join(settings.MEDIA_ROOT, 'profiles', new_member_id)
                    os.makedirs(profile_picture_directory, exist_ok=True)

                    # Save the new profile picture
                    with open(os.path.join(profile_picture_directory, profile_picture_name), 'wb') as profile_file:
                        for chunk in profile_picture.chunks():
                            profile_file.write(chunk)

                    member.member_profile_picture = profile_picture_path

                # Update the member details
                member = form.save(commit=False)
                
                # Update member_id if it was changed
                if new_member_id != member.member_id:
                    # If ID changed and no new profile picture, move existing profile picture
                    if member.member_profile_picture and not (profile_picture and hasattr(profile_picture, 'name')):
                        old_path = member.member_profile_picture
                        new_path = os.path.join('profiles', new_member_id, f"{new_member_id}_profile.png")
                        # Move the file if it exists
                        old_full_path = os.path.join(settings.MEDIA_ROOT, old_path)
                        new_full_path = os.path.join(settings.MEDIA_ROOT, new_path)
                        new_dir = os.path.dirname(new_full_path)
                        os.makedirs(new_dir, exist_ok=True)
                        if os.path.exists(old_full_path):
                            import shutil
                            shutil.move(old_full_path, new_full_path)
                        member.member_profile_picture = new_path
                    member.member_id = new_member_id
                
                if profile_picture and hasattr(profile_picture, 'name'):
                    member.member_profile_picture = os.path.join('profiles', member.member_id, f"{member.member_id}_profile.png")
                
                # For superusers, ensure member_is_active and member_role are saved
                if request.user.is_superuser:
                    member_is_active = form.cleaned_data.get('member_is_active', True)
                    member_role = form.cleaned_data.get('member_role', '')
                    member.member_is_active = member_is_active
                    member.member_role = member_role
                
                member.save()

                # Audit log: member updated
                audit_log_user_action(
                    request=request,
                    action='member_updated',
                    target=f'member:{member.member_id}',
                    extra_details={
                        'member_id': member.member_id,
                        'member_name': f'{member.member_initials} {member.member_first_name} {member.member_last_name}',
                        'is_active': member.member_is_active,
                        'role': member.member_role or 'No Role',
                    }
                )

                from django.contrib import messages
                messages.success(request, f'Member {member.member_initials} {member.member_first_name} {member.member_last_name} updated successfully.')
                return redirect('member_list')  # Redirect to a member list view

        else:
            # Prepopulate the form with existing member data
            form = MemberEditForm(instance=member, user=request.user)

        context['form'] = form
        context['member'] = member
        return render(request, 'member/edit.html', context)

    except Member.DoesNotExist:
        # Handle the case where the member with the specified ID does not exist
        return redirect('member_list')  # Redirect to a member list view

