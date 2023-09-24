from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import *
from .models import MemberAttendance
from .views import context_data


def attendance_mark(request):
    context = context_data(request)
    context['page_name'] = "Attendance Mark"

    if request.method == 'POST':
        form = AttendanceMarkForm(request.POST)
        if form.is_valid():
            meeting_date = form.cleaned_data['meeting_date']
            member = form.cleaned_data['member_id']

            # Check if attendance record with the same date and member already exists
            existing_attendance = MemberAttendance.objects.filter(
                meeting_date=meeting_date,
                member_id=member,
            )

            if existing_attendance.exists():
                # Duplicate record found, show an error message
                messages.error(request, 'Member attendance is already added for this date.')
            else:
                # No duplicate record found, save the attendance record
                form.save()
                messages.success(request, 'Member attendance has been recorded successfully.')
                return redirect('attendance_mark')  # Redirect to a success page or a list view
        else:
            messages.error(request, form.errors)

    form = AttendanceMarkForm()
    context['form'] = form

    return render(request, 'attendance/mark.html', context)


def attendance_full_view(request):
    context = context_data(request)
    context['page_name'] = 'Attendance Dates-All'
    attendance_all_dates = MeetingInfo.objects.all()
    context['attendance_all_dates'] = attendance_all_dates
    return render(request, 'attendance/all_dates.html', context)


def attendance_date_view(request, meeting_id):
    context = context_data(request)
    meeting = MeetingInfo.objects.get(meeting_id=meeting_id)
    context['page_name'] = f'Attendance Date {meeting.meeting_date}'
    attendances = MemberAttendance.objects.filter(meeting_date=meeting_id)
    context['attendances'] = attendances
    context['meeting'] = meeting
    return render(request, 'attendance/attendance.html', context)


def attendance_delete(request, attendance_id, meeting_id):
    attendance_to_delete = MemberAttendance.objects.get(attendance_id=attendance_id)
    messages.success(request, "Attendance Record have been deleted successfully")
    attendance_to_delete.delete()
    return redirect('attendance_date', meeting_id)


def attendance_edit(request, attendance_id, meeting_id):
    context = context_data(request)
    context['page_name'] = "Attendance Edit"
    attendance_to_edit = MemberAttendance.objects.get(attendance_id=attendance_id)

    if request.method == 'POST':
        form = AttendanceEditForm(request.POST, instance=attendance_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance Details Edited Successfully.")
            return redirect('attendance_date', meeting_id)

    form = AttendanceEditForm(instance=attendance_to_edit)
    context['member_info'] = attendance_to_edit
    context['form'] = form
    return render(request, 'attendance/edit.html', context)

