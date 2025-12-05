"""
Bulk attendance marking views for optimized attendance recording
"""
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import formset_factory
from .forms import *
from .models import MemberAttendance, MeetingInfo, Member
from .views import context_data


@login_required
def attendance_bulk_mark(request):
    """
    Bulk attendance marking - mark multiple members at once for a meeting
    """
    context = context_data(request)
    context['page_name'] = "Bulk Attendance Marking"
    
    # Get selected meeting from GET parameter
    meeting_id = request.GET.get('meeting_id')
    selected_meeting = None
    
    if meeting_id:
        try:
            selected_meeting = get_object_or_404(MeetingInfo, meeting_id=meeting_id)
        except:
            messages.error(request, 'Invalid meeting selected.')
            return redirect('attendance_bulk_mark')
    
    # Get all meetings for dropdown (newest first)
    meetings = MeetingInfo.objects.all().order_by('-meeting_date')
    context['meetings'] = meetings
    context['selected_meeting'] = selected_meeting
    
    if request.method == 'POST' and selected_meeting:
        # Process bulk attendance submission
        member_ids = request.POST.getlist('member_ids')
        attendance_statuses = request.POST.getlist('attendance_status')
        fee_statuses = request.POST.getlist('fee_status')
        
        # Debug: Log what we received
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'Received {len(member_ids)} members, {len(attendance_statuses)} attendance statuses, {len(fee_statuses)} fee statuses')
        if len(member_ids) > 0:
            logger.info(f'First member: {member_ids[0]}, attendance: {attendance_statuses[0] if len(attendance_statuses) > 0 else "N/A"}, fee: {fee_statuses[0] if len(fee_statuses) > 0 else "N/A"}')
        
        if not member_ids:
            messages.error(request, 'Please select at least one member.')
            context['selected_meeting'] = selected_meeting
            # Reload members data
            active_members = Member.objects.filter(member_is_active=True).order_by('member_id')
            existing_attendance = MemberAttendance.objects.filter(
                meeting_date=selected_meeting
            ).select_related('member_id')
            attendance_dict = {att.member_id.member_id: att for att in existing_attendance}
            is_superuser = request.user.is_superuser
            members_data = []
            for member in active_members:
                existing = attendance_dict.get(member.member_id)
                members_data.append({
                    'member': member,
                    'existing_attendance': existing,
                    'is_present': existing.attendance_status if existing else False,
                    'is_fee_paid': existing.attendance_fee_status if existing else False,
                    'has_existing': existing is not None,
                })
            context['members_data'] = members_data
            context['is_superuser'] = is_superuser
            return render(request, 'attendance/bulk_mark.html', context)
        
        # Validate and save attendance records
        success_count = 0
        error_count = 0
        permission_denied_count = 0
        
        # Check if user is superuser
        is_superuser = request.user.is_superuser
        
        with transaction.atomic():
            for i, member_id in enumerate(member_ids):
                try:
                    member = Member.objects.get(member_id=member_id, member_is_active=True)
                    
                    # Get attendance status and fee status
                    attendance_status_str = attendance_statuses[i] if i < len(attendance_statuses) else 'False'
                    fee_status_str = fee_statuses[i] if i < len(fee_statuses) else 'False'
                    
                    # Convert string to boolean
                    attendance_status = attendance_status_str == 'True'
                    fee_status = fee_status_str == 'True'
                    
                    # Debug logging (remove in production)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f'Processing member {member_id}: attendance={attendance_status}, fee={fee_status}')
                    
                    # Validate business rule: fee can only be paid if present
                    if fee_status and not attendance_status:
                        fee_status = False
                    
                    # Check if attendance already exists
                    existing = MemberAttendance.objects.filter(
                        meeting_date=selected_meeting,
                        member_id=member
                    ).first()
                    
                    if existing:
                        # Only superusers can update existing attendance
                        if not is_superuser:
                            permission_denied_count += 1
                            continue
                        
                        # Update existing record
                        existing.attendance_status = attendance_status
                        existing.attendance_fee_status = fee_status
                        existing.save()
                        success_count += 1
                    else:
                        # Create new record
                        MemberAttendance.objects.create(
                            meeting_date=selected_meeting,
                            member_id=member,
                            attendance_status=attendance_status,
                            attendance_fee_status=fee_status
                        )
                        success_count += 1
                except Member.DoesNotExist:
                    error_count += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Error processing member {member_id}: {str(e)}')
                    error_count += 1
        
        if success_count > 0:
            messages.success(request, f'Successfully marked attendance for {success_count} member(s).')
        if permission_denied_count > 0:
            messages.warning(request, f'Cannot update attendance for {permission_denied_count} member(s) - attendance already marked. Only superusers can edit existing attendance.')
        if error_count > 0:
            messages.warning(request, f'Failed to mark attendance for {error_count} member(s).')
        
        # Clear any saved localStorage data by adding a flag in the redirect
        response = redirect('attendance_date', meeting_id=selected_meeting.meeting_id)
        response['X-Clear-Storage'] = 'true'  # Signal to clear storage
        return response
    
    # GET request - show form
    if selected_meeting:
        # Get all active members
        active_members = Member.objects.filter(member_is_active=True).order_by('member_id')
        
        # Get existing attendance records for this meeting
        existing_attendance = MemberAttendance.objects.filter(
            meeting_date=selected_meeting
        ).select_related('member_id')
        
        # Create a dictionary of existing attendance by member_id
        attendance_dict = {att.member_id.member_id: att for att in existing_attendance}
        
        # Check if user is superuser
        is_superuser = request.user.is_superuser
        
        # Prepare member data with existing attendance status
        members_data = []
        for member in active_members:
            existing = attendance_dict.get(member.member_id)
            members_data.append({
                'member': member,
                'existing_attendance': existing,
                'is_present': existing.attendance_status if existing else False,
                'is_fee_paid': existing.attendance_fee_status if existing else False,
                'has_existing': existing is not None,  # Flag to indicate if attendance already exists
            })
        
        context['members_data'] = members_data
        context['is_superuser'] = is_superuser
    
    return render(request, 'attendance/bulk_mark.html', context)


@login_required
def attendance_mark_all_present(request, meeting_id):
    """
    Quick action: Mark all active members as present for a meeting
    """
    try:
        meeting = get_object_or_404(MeetingInfo, meeting_id=meeting_id)
        active_members = Member.objects.filter(member_is_active=True)
        
        success_count = 0
        
        with transaction.atomic():
            for member in active_members:
                # Check if attendance already exists
                attendance, created = MemberAttendance.objects.get_or_create(
                    meeting_date=meeting,
                    member_id=member,
                    defaults={
                        'attendance_status': True,
                        'attendance_fee_status': False,
                    }
                )
                
                if not created:
                    # Update existing record
                    attendance.attendance_status = True
                    attendance.save()
                
                success_count += 1
        
        messages.success(request, f'Marked all {success_count} active members as present for {meeting.meeting_date}.')
        return redirect('attendance_date', meeting_id=meeting_id)
    
    except Exception as e:
        messages.error(request, f'Error marking all members as present: {str(e)}')
        return redirect('attendance_date', meeting_id=meeting_id)

