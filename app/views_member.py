import os
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from .models import *
from .forms import *
from .views import context_data
from .utils import generate_qr_code
from .constants import *


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


@login_required
def member_register(request):
    context = context_data(request)
    context['page_name'] = 'Member Register'
    if request.method == 'POST':
        form = MemberRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            member_id = form.cleaned_data['member_id']
            profile_picture = form.cleaned_data['member_profile_picture']

            # Check if a member with the same ID already exists
            if Member.objects.filter(member_id=member_id).exists():
                form.add_error('member_id', 'Member with this ID already exists.')
            elif not is_image(profile_picture):
                form.add_error('member_profile_picture', f'Please upload a valid image file ({", ".join(ALLOWED_IMAGE_EXTENSIONS)}).')
            elif profile_picture.size > MAX_IMAGE_SIZE:
                form.add_error('member_profile_picture', f'Image size must be less than {MAX_IMAGE_SIZE // (1024*1024)}MB.')
            else:
                # Create the Member object
                member = form.save(commit=False)

                # Set the profile picture upload path
                profile_picture_name = f"{member_id}_profile.png"
                profile_picture_path = os.path.join('profiles', member_id, profile_picture_name)

                # Create the directory for the profile picture and QR code
                profile_picture_directory = os.path.join(settings.MEDIA_ROOT, 'profiles', member_id)
                os.makedirs(profile_picture_directory, exist_ok=True)

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
            form = MemberEditForm(request.POST, request.FILES, instance=member)
            if form.is_valid():
                new_member_id = form.cleaned_data['member_id']
                profile_picture = form.cleaned_data['member_profile_picture']

                # Check if the new member ID is the same as the current one
                if new_member_id != member_id:
                    # Check if the new member ID already exists
                    form.add_error('member_id', 'Member with this ID already exists.')
                    context['form'] = form
                    context['member'] = member
                    return render(request, 'member/edit.html', context)

                # Check if a new profile picture was uploaded
                if profile_picture and hasattr(profile_picture, 'name'):
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
                if profile_picture and hasattr(profile_picture, 'name'):
                    member.member_profile_picture = os.path.join('profiles', member_id, f"{member_id}_profile.png")
                member.save()

                return redirect('member_list')  # Redirect to a member list view

        else:
            # Prepopulate the form with existing member data
            form = MemberEditForm(instance=member)

        context['form'] = form
        context['member'] = member
        return render(request, 'member/edit.html', context)

    except Member.DoesNotExist:
        # Handle the case where the member with the specified ID does not exist
        return redirect('member_list')  # Redirect to a member list view

