from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.exceptions import ValidationError

from .forms import *
from .models import *
from .views import context_data
from .constants import PAGINATION_MEETING_LIST


@login_required
def meeting_list(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    context = context_data(request)
    context['page_name'] = 'Meeting List'
    
    # Pagination - ordered by date (newest first)
    meetings_list = MeetingInfo.objects.all()
    paginator = Paginator(meetings_list, PAGINATION_MEETING_LIST)
    page = request.GET.get('page', 1)
    
    try:
        meetings = paginator.page(page)
    except PageNotAnInteger:
        meetings = paginator.page(1)
    except EmptyPage:
        meetings = paginator.page(paginator.num_pages)
    
    context['meetings'] = meetings
    context['page_obj'] = meetings  # For pagination template
    return render(request, 'meeting/list.html', context)


@user_passes_test(lambda u: u.is_superuser)
def meeting_delete(request, meeting_date):
    try:
        meeting_to_delete = get_object_or_404(MeetingInfo, meeting_date=meeting_date)
        meeting_to_delete.delete()
        messages.success(request, "Meeting Information has been deleted successfully")
    except Exception as e:
        messages.error(request, f"Error deleting meeting: {str(e)}")
    return redirect('meeting_list')


@login_required
def meeting_add(request):
    context = context_data(request)
    context['page_name'] = 'Meeting Add'
    if request.method == 'POST':
        form = MeetingAddForm(request.POST)
        if form.is_valid():
            meeting_date = form.cleaned_data['meeting_date']
            # Check for duplicate meeting date
            if MeetingInfo.objects.filter(meeting_date=meeting_date).exists():
                form.add_error('meeting_date', 'A meeting with this date already exists.')
                messages.error(request, "A meeting with this date already exists.")
            else:
                form.save()
                messages.success(request, "New Meeting added Successfully")
                return redirect('meeting_list')
        else:
            messages.error(request, "There was an error while adding the Meeting Info. Please try again!")
    form = MeetingAddForm()
    context['form'] = form
    return render(request, 'meeting/add.html', context)


@user_passes_test(lambda u: u.is_superuser)
def meeting_edit(request, meeting_date):
    context = context_data(request)
    context['page_name'] = "Meeting Edit"
    try:
        meeting_to_edit = get_object_or_404(MeetingInfo, meeting_date=meeting_date)
        form = MeetingAddForm(request.POST or None, instance=meeting_to_edit)
        if form.is_valid():
            new_meeting_date = form.cleaned_data['meeting_date']
            # Check for duplicate meeting date (excluding current meeting)
            if MeetingInfo.objects.filter(meeting_date=new_meeting_date).exclude(meeting_id=meeting_to_edit.meeting_id).exists():
                form.add_error('meeting_date', 'A meeting with this date already exists.')
                messages.error(request, "A meeting with this date already exists.")
            else:
                form.save()
                messages.success(request, "Meeting Information has been updated successfully")
                return redirect('meeting_list')

        context['form'] = form
        context['meeting'] = meeting_to_edit
        return render(request, 'meeting/edit.html', context)
    except Exception as e:
        messages.error(request, f"Error editing meeting: {str(e)}")
        return redirect('meeting_list')
