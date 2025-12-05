"""
Utility functions for the Membership Management System
"""
import os
import qrcode
from django.conf import settings
from django.db.models import Q
from .models import Member, MeetingInfo, MemberAttendance


def generate_qr_code(member_id):
    """
    Generate QR code for a member and save it to the media directory.
    
    Args:
        member_id: The member ID to encode in the QR code
        
    Returns:
        str: Relative path to the saved QR code image
    """
    profile_picture_directory = os.path.join(settings.MEDIA_ROOT, 'profiles', member_id)
    os.makedirs(profile_picture_directory, exist_ok=True)
    
    qr_code = qrcode.make(member_id)
    qr_code_name = f"{member_id}_qr.png"
    qr_code_path = os.path.join(profile_picture_directory, qr_code_name)
    
    qr_code.save(qr_code_path)
    
    return os.path.relpath(qr_code_path, settings.MEDIA_ROOT)


def check_and_deactivate_inactive_members(consecutive_meetings=3, dry_run=False):
    """
    Check for members who haven't attended N consecutive meetings and deactivate them.
    
    Args:
        consecutive_meetings: Number of consecutive meetings to check (default: 3)
        dry_run: If True, only return list without deactivating (default: False)
        
    Returns:
        dict: {
            'deactivated_count': int,
            'deactivated_members': list of member objects
        }
    """
    # Get the latest N meetings ordered by date (newest first)
    latest_meetings = MeetingInfo.objects.all().order_by('-meeting_date')[:consecutive_meetings]

    if not latest_meetings.exists() or latest_meetings.count() < consecutive_meetings:
        return {
            'deactivated_count': 0,
            'deactivated_members': [],
            'message': f'Not enough meetings found. Need at least {consecutive_meetings} meetings.'
        }

    # Get all active members
    active_members = Member.objects.filter(member_is_active=True)

    deactivated_members = []

    for member in active_members:
        # Check attendance for the latest N meetings
        missed_count = 0
        
        for meeting in latest_meetings:
            # Check if member has an attendance record for this meeting
            attendance = MemberAttendance.objects.filter(
                member_id=member,
                meeting_date=meeting
            ).first()

            # If no attendance record OR attendance_status is False, member missed the meeting
            if not attendance or not attendance.attendance_status:
                missed_count += 1
            else:
                # If member attended any meeting in the sequence, break (not consecutive)
                break

        # If member missed all N consecutive meetings, mark for deactivation
        if missed_count == consecutive_meetings:
            deactivated_members.append(member)

    if not dry_run and deactivated_members:
        # Deactivate members
        member_ids_to_deactivate = [m.member_id for m in deactivated_members]
        Member.objects.filter(
            member_id__in=member_ids_to_deactivate
        ).update(member_is_active=False)

    return {
        'deactivated_count': len(deactivated_members),
        'deactivated_members': deactivated_members,
        'message': f'Checked {active_members.count()} active members against {latest_meetings.count()} latest meetings.'
    }

