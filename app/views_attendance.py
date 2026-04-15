from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import IntegrityError, transaction

from .forms import *
from .models import MemberAttendance, MeetingInfo, Member
from .views import context_data
from .constants import PAGINATION_ATTENDANCE_LIST, PAGINATION_ATTENDANCE_FULL


@login_required
def attendance_mark(request):
    context = context_data(request)
    context['page_name'] = "Attendance Mark"

    if request.method == 'POST':
        form = AttendanceMarkForm(request.POST)
        if form.is_valid():
            meeting_date = form.cleaned_data['meeting_date']
            member = form.cleaned_data['member_id']

            # Check if attendance record with the same date and member already exists
            # Use .first() instead of .exists() for better performance
            existing_attendance = MemberAttendance.objects.filter(
                meeting_date=meeting_date,
                member_id=member,
            ).first()

            if existing_attendance:
                # Duplicate record found, show an error message
                messages.error(request, 'Member attendance is already added for this date.')
            else:
                # No duplicate record found, save the attendance record
                # Members can pay fees even if absent
                try:
                    form.save()
                    messages.success(request, 'Member attendance has been recorded successfully.')
                    return redirect('attendance_mark')
                except Exception as e:
                    # Handle unique constraint violation
                    if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                        messages.error(request, 'Member attendance is already added for this date.')
                    else:
                        messages.error(request, f'Error saving attendance: {str(e)}')
        else:
            messages.error(request, form.errors)

    form = AttendanceMarkForm()
    context['form'] = form

    return render(request, 'attendance/mark.html', context)


@login_required
def attendance_scanner(request):
    """
    High-volume attendance marking via QR scanner + AJAX.
    Does not replace existing forms; it's an additional optimized workflow.
    """
    context = context_data(request)
    context['page_name'] = "Attendance Scanner"
    meetings = MeetingInfo.objects.all().order_by('-meeting_date')
    context['meetings'] = meetings
    return render(request, 'attendance/scan.html', context)


@require_POST
@login_required
def attendance_mark_api(request):
    """
    API endpoint for marking attendance (optimized for scanner / AJAX).

    Rules:
    - Creates a new record if missing.
    - If record exists: only superusers can update it (prevents accidental edits by staff).
    """
    meeting_id = (request.POST.get('meeting_id') or '').strip()
    member_id = (request.POST.get('member_id') or '').strip()
    attendance_status = (request.POST.get('attendance_status') or '').strip()
    fee_status = (request.POST.get('fee_status') or '').strip()

    if not meeting_id or not member_id:
        return JsonResponse({'ok': False, 'error': 'meeting_id and member_id are required.'}, status=400)

    try:
        meeting = MeetingInfo.objects.get(meeting_id=meeting_id)
    except MeetingInfo.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Meeting not found.'}, status=404)

    try:
        member = Member.objects.get(member_id=member_id)
    except Member.DoesNotExist:
        return JsonResponse({'ok': False, 'error': f'Member "{member_id}" not found.'}, status=404)

    if not member.member_is_active:
        return JsonResponse({'ok': False, 'error': f'Member "{member_id}" is inactive.'}, status=400)

    # Convert to bool (default present=True, fee_paid=False for scanner UX)
    present = True if attendance_status == '' else (attendance_status.lower() in ('true', '1', 'yes', 'present'))
    fee_paid = fee_status.lower() in ('true', '1', 'yes', 'paid')

    # Members can pay fees even if absent - no validation needed
    # Use get_or_create to avoid TOCTOU races under concurrent marking
    try:
        with transaction.atomic():
            attendance, created = MemberAttendance.objects.get_or_create(
                meeting_date=meeting,
                member_id=member,
                defaults={
                    'attendance_status': present,
                    'attendance_fee_status': fee_paid,
                }
            )
    except IntegrityError:
        # In case of a concurrent insert, re-fetch the existing row
        attendance = MemberAttendance.objects.filter(meeting_date=meeting, member_id=member).first()
        created = False

    if created:
        return JsonResponse({'ok': True, 'created': True})

    # Existing row
    if not request.user.is_superuser:
        return JsonResponse(
            {'ok': False, 'error': 'Attendance already marked for this member. Only superusers can edit.'},
            status=409
        )

    attendance.attendance_status = present
    attendance.attendance_fee_status = fee_paid
    attendance.save()
    return JsonResponse({'ok': True, 'updated': True})


@login_required
def attendance_full_view(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    context = context_data(request)
    context['page_name'] = 'Attendance Dates-All'
    
    # Pagination - ordered by date (newest first)
    attendance_all_dates_list = MeetingInfo.objects.all()
    paginator = Paginator(attendance_all_dates_list, PAGINATION_ATTENDANCE_FULL)
    page = request.GET.get('page', 1)
    
    try:
        attendance_all_dates = paginator.page(page)
    except PageNotAnInteger:
        attendance_all_dates = paginator.page(1)
    except EmptyPage:
        attendance_all_dates = paginator.page(paginator.num_pages)
    
    context['attendance_all_dates'] = attendance_all_dates
    context['page_obj'] = attendance_all_dates  # For pagination template
    return render(request, 'attendance/all_dates.html', context)


@login_required
def attendance_date_view(request, meeting_id):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    context = context_data(request)
    try:
        meeting = get_object_or_404(MeetingInfo, meeting_id=meeting_id)
        context['page_name'] = f'Attendance Date {meeting.meeting_date}'
        
        # Optimize query with select_related to reduce database queries
        attendances_list = MemberAttendance.objects.filter(
            meeting_date=meeting_id
        ).select_related('member_id', 'meeting_date').order_by('member_id__member_id')
        
        # Pagination
        paginator = Paginator(attendances_list, PAGINATION_ATTENDANCE_LIST)
        page = request.GET.get('page', 1)
        
        try:
            attendances = paginator.page(page)
        except PageNotAnInteger:
            attendances = paginator.page(1)
        except EmptyPage:
            attendances = paginator.page(paginator.num_pages)
        
        context['attendances'] = attendances
        context['page_obj'] = attendances  # For pagination template
        context['meeting'] = meeting
        return render(request, 'attendance/attendance.html', context)
    except Exception as e:
        messages.error(request, f"Error loading attendance: {str(e)}")
        return redirect('attendance_date_all')


@user_passes_test(lambda u: u.is_superuser)
def attendance_delete(request, attendance_id, meeting_id):
    try:
        attendance_to_delete = get_object_or_404(MemberAttendance, attendance_id=attendance_id)
        attendance_to_delete.delete()
        messages.success(request, "Attendance Record has been deleted successfully")
    except Exception as e:
        messages.error(request, f"Error deleting attendance: {str(e)}")
    return redirect('attendance_date', meeting_id)


@user_passes_test(lambda u: u.is_superuser)
def attendance_edit(request, attendance_id, meeting_id):
    context = context_data(request)
    context['page_name'] = "Attendance Edit"
    try:
        attendance_to_edit = get_object_or_404(MemberAttendance, attendance_id=attendance_id)

        if request.method == 'POST':
            form = AttendanceEditForm(request.POST, instance=attendance_to_edit)
            if form.is_valid():
                # Members can pay fees even if absent
                try:
                    form.save()
                    messages.success(request, "Attendance Details Edited Successfully.")
                    return redirect('attendance_date', meeting_id)
                except Exception as e:
                    messages.error(request, f"Error saving attendance: {str(e)}")
        else:
            form = AttendanceEditForm(instance=attendance_to_edit)

        context['member_info'] = attendance_to_edit
        context['form'] = form
        return render(request, 'attendance/edit.html', context)
    except Exception as e:
        messages.error(request, f"Error editing attendance: {str(e)}")
        return redirect('attendance_date', meeting_id)

