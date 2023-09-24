from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test

from .forms import *
from .models import *
from .views import context_data


@user_passes_test(lambda u: u.is_superuser)
def meeting_list(request):
    context = context_data(request)
    context['page_name'] = 'Meeting List'
    meetings = MeetingInfo.objects.all()
    context['meetings'] = meetings
    return render(request, 'meeting/list.html', context)


@user_passes_test(lambda u: u.is_superuser)
def meeting_delete(request, meeting_date):
    meeting_to_delete = MeetingInfo.objects.get(meeting_date=meeting_date)
    messages.success(request, "Meeting Information have been deleted successfully")
    meeting_to_delete.delete()
    return redirect('meeting_list')


@user_passes_test(lambda u: u.is_superuser)
def meeting_add(request):
    context = context_data(request)
    context['page_name'] = 'Meeting Add'
    if request.method == 'POST':
        form = MeetingAddForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New Meeting added Successfully")
            return redirect('meeting_list')
        else:
            messages.success(request, "There was an error while Adding a the Meeting Info. Please try again!")
    form = MeetingAddForm()
    context['form'] = form
    return render(request, 'meeting/add.html', context)


@user_passes_test(lambda u: u.is_superuser)
def meeting_edit(request, meeting_date):
    context = context_data(request)
    context['page_name'] = "Meeting Edit"
    meeting_to_edit = MeetingInfo.objects.get(meeting_date=meeting_date)
    form = MeetingAddForm(request.POST or None, instance=meeting_to_edit)
    if form.is_valid():
        form.save()
        messages.success(request, "User Profile has been updated successfully")
        return redirect('meeting_list')

    context['form'] = form
    context['meeting'] = meeting_to_edit
    return render(request, 'meeting/edit.html', context)
