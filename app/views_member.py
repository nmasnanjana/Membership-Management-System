import os
import qrcode
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from .models import *
from .forms import *
from .views import context_data


@login_required
def member_list(request):
    context = context_data(request)
    context['page_name'] = 'List Members'
    members = Member.objects.all()
    context['members'] = members
    return render(request, 'member/list.html', context)


def is_image(file):
    # Define a list of allowed image file extensions
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']

    # Get the file extension
    _, file_extension = os.path.splitext(file.name.lower())

    # Check if the file extension is in the allowed extensions list
    return file_extension in allowed_extensions


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
                form.add_error('member_profile_picture', 'Please upload a valid image file (jpg, jpeg, png, gif).')
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

                # Generate and save the QR code
                qr_code = qrcode.make(member_id)
                qr_code_name = f"{member_id}_qr.png"
                qr_code_path = os.path.join(profile_picture_directory, qr_code_name)

                # Ensure the directory for QR code exists
                os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)

                # Save the QR code
                qr_code.save(qr_code_path)

                # Save the Member object with the updated profile picture and QR code path
                member.member_qr_code = os.path.relpath(qr_code_path, settings.MEDIA_ROOT)
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
    member = Member.objects.get(member_id=member_id)
    context['member'] = member
    return render(request, 'member/view.html', context)


@user_passes_test(lambda u: u.is_superuser)
def member_delete(request, member_id):
    try:
        member = Member.objects.get(member_id=member_id)

        # Get the paths to the profile picture and QR code
        profile_picture_path = member.member_profile_picture.path
        qr_code_path = member.member_qr_code.path

        # Delete the profile picture and QR code files
        if os.path.exists(profile_picture_path):
            os.remove(profile_picture_path)
        if os.path.exists(qr_code_path):
            os.remove(qr_code_path)

        # Delete the member's directory
        member_directory = os.path.join(settings.MEDIA_ROOT, 'profiles', member_id)
        if os.path.exists(member_directory):
            os.rmdir(member_directory)

        # Delete the Member object
        member.delete()

        return redirect('member_list')  # Redirect to a member list view

    except Member.DoesNotExist:
        # Handle the case where the member with the specified ID does not exist
        return redirect('member_list')  # Redirect to a member list view


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

                # Do not update the profile picture if a new one is not provided
                if form.cleaned_data['member_profile_picture'] != Member.objects.get(member_id=member_id).member_profile_picture:
                    if os.path.exists(Member.objects.get(member_id=member_id).member_profile_picture.path):
                        os.remove(Member.objects.get(member_id=member_id).member_profile_picture.path)

                    form.cleaned_data['member_profile_picture'] = member.member_profile_picture

                    #member = form.save(commit=False)

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

                # Update the member details
                form.save()

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

