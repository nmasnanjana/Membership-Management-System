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


# Sri Lankan Public Holidays Data (2024-2026)
SRI_LANKAN_HOLIDAYS = {
    "2024": [
        {"date": "2024-01-15", "name": "Tamil Thai Pongal Day"},
        {"date": "2024-02-04", "name": "Independence Day"},
        {"date": "2024-02-23", "name": "Navam Full Moon Poya Day"},
        {"date": "2024-03-08", "name": "Maha Sivarathri Day"},
        {"date": "2024-03-24", "name": "Medin Full Moon Poya Day"},
        {"date": "2024-03-29", "name": "Good Friday"},
        {"date": "2024-04-11", "name": "Id-Ul-Fitr (Ramazan Festival Day)"},
        {"date": "2024-04-12", "name": "Day prior to Sinhala & Tamil New Year Day"},
        {"date": "2024-04-13", "name": "Sinhala & Tamil New Year Day"},
        {"date": "2024-04-14", "name": "Sinhala & Tamil New Year Day"},
        {"date": "2024-04-23", "name": "Bak Full Moon Poya Day"},
        {"date": "2024-05-01", "name": "May Day"},
        {"date": "2024-05-23", "name": "Vesak Full Moon Poya Day"},
        {"date": "2024-05-24", "name": "Day following Vesak Full Moon Poya Day"},
        {"date": "2024-06-17", "name": "Id-Ul-Alha (Hadji Festival Day)"},
        {"date": "2024-06-21", "name": "Poson Full Moon Poya Day"},
        {"date": "2024-07-20", "name": "Esala Full Moon Poya Day"},
        {"date": "2024-08-19", "name": "Nikini Full Moon Poya Day"},
        {"date": "2024-09-16", "name": "Milad-Un-Nabi (Holy Prophet's Birthday)"},
        {"date": "2024-09-17", "name": "Binara Full Moon Poya Day"},
        {"date": "2024-10-17", "name": "Vap Full Moon Poya Day"},
        {"date": "2024-10-31", "name": "Deepavali Festival Day"},
        {"date": "2024-11-15", "name": "Il Full Moon Poya Day"},
        {"date": "2024-12-14", "name": "Unduvap Full Moon Poya Day"},
        {"date": "2024-12-25", "name": "Christmas Day"},
    ],
    "2025": [
        {"date": "2025-01-14", "name": "Tamil Thai Pongal Day"},
        {"date": "2025-01-15", "name": "Duruthu Full Moon Poya Day"},
        {"date": "2025-02-04", "name": "Independence Day"},
        {"date": "2025-02-12", "name": "Navam Full Moon Poya Day"},
        {"date": "2025-02-26", "name": "Maha Sivarathri Day"},
        {"date": "2025-03-14", "name": "Medin Full Moon Poya Day"},
        {"date": "2025-03-31", "name": "Id-Ul-Fitr (Ramazan Festival Day)"},
        {"date": "2025-04-12", "name": "Bak Full Moon Poya Day"},
        {"date": "2025-04-13", "name": "Sinhala & Tamil New Year Day"},
        {"date": "2025-04-14", "name": "Day following Sinhala & Tamil New Year Day"},
        {"date": "2025-04-18", "name": "Good Friday"},
        {"date": "2025-05-01", "name": "May Day"},
        {"date": "2025-05-12", "name": "Vesak Full Moon Poya Day"},
        {"date": "2025-05-13", "name": "Day following Vesak Full Moon Poya Day"},
        {"date": "2025-06-07", "name": "Id-Ul-Alha (Hadji Festival Day)"},
        {"date": "2025-06-10", "name": "Poson Full Moon Poya Day"},
        {"date": "2025-07-10", "name": "Esala Full Moon Poya Day"},
        {"date": "2025-08-08", "name": "Nikini Full Moon Poya Day"},
        {"date": "2025-09-05", "name": "Milad-Un-Nabi (Holy Prophet's Birthday)"},
        {"date": "2025-09-07", "name": "Binara Full Moon Poya Day"},
        {"date": "2025-10-06", "name": "Vap Full Moon Poya Day"},
        {"date": "2025-10-20", "name": "Deepavali Festival Day"},
        {"date": "2025-11-05", "name": "Il Full Moon Poya Day"},
        {"date": "2025-12-04", "name": "Unduvap Full Moon Poya Day"},
        {"date": "2025-12-25", "name": "Christmas Day"},
    ],
    "2026": [
        {"date": "2026-01-04", "name": "Duruthu Full Moon Poya Day"},
        {"date": "2026-01-14", "name": "Tamil Thai Pongal Day"},
        {"date": "2026-02-02", "name": "Navam Full Moon Poya Day"},
        {"date": "2026-02-04", "name": "Independence Day"},
        {"date": "2026-02-16", "name": "Maha Sivarathri Day"},
        {"date": "2026-03-04", "name": "Medin Full Moon Poya Day"},
        {"date": "2026-03-20", "name": "Id-Ul-Fitr (Ramazan Festival Day)"},
        {"date": "2026-04-02", "name": "Bak Full Moon Poya Day"},
        {"date": "2026-04-03", "name": "Good Friday"},
        {"date": "2026-04-13", "name": "Day prior to Sinhala & Tamil New Year Day"},
        {"date": "2026-04-14", "name": "Sinhala & Tamil New Year Day"},
        {"date": "2026-05-01", "name": "May Day"},
        {"date": "2026-05-01", "name": "Vesak Full Moon Poya Day"},
        {"date": "2026-05-02", "name": "Day following Vesak Full Moon Poya Day"},
        {"date": "2026-05-27", "name": "Id-Ul-Alha (Hadji Festival Day)"},
        {"date": "2026-05-31", "name": "Poson Full Moon Poya Day"},
        {"date": "2026-06-29", "name": "Esala Full Moon Poya Day"},
        {"date": "2026-07-28", "name": "Nikini Full Moon Poya Day"},
        {"date": "2026-08-26", "name": "Milad-Un-Nabi (Holy Prophet's Birthday)"},
        {"date": "2026-08-27", "name": "Binara Full Moon Poya Day"},
        {"date": "2026-09-25", "name": "Vap Full Moon Poya Day"},
        {"date": "2026-10-09", "name": "Deepavali Festival Day"},
        {"date": "2026-10-25", "name": "Il Full Moon Poya Day"},
        {"date": "2026-11-23", "name": "Unduvap Full Moon Poya Day"},
        {"date": "2026-12-25", "name": "Christmas Day"},
    ]
}


def get_sri_lankan_holidays(year=None):
    """
    Get Sri Lankan public holidays for a specific year.
    
    Args:
        year: Year as string or int (default: current year)
        
    Returns:
        list: List of holiday dictionaries with 'date' and 'name'
    """
    from datetime import datetime
    
    if year is None:
        year = str(datetime.now().year)
    else:
        year = str(year)
    
    return SRI_LANKAN_HOLIDAYS.get(year, [])


def get_upcoming_holidays(limit=5):
    """
    Get upcoming Sri Lankan holidays.
    
    Args:
        limit: Maximum number of holidays to return
        
    Returns:
        list: List of upcoming holiday dictionaries
    """
    from datetime import datetime, date
    
    today = date.today()
    upcoming = []
    
    # Check current and next year
    for year in [today.year, today.year + 1]:
        holidays = get_sri_lankan_holidays(year)
        for holiday in holidays:
            holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
            if holiday_date >= today:
                upcoming.append({
                    'date': holiday_date,
                    'name': holiday['name'],
                    'days_until': (holiday_date - today).days
                })
    
    # Sort by date and limit
    upcoming.sort(key=lambda x: x['date'])
    return upcoming[:limit]


def calculate_member_engagement_score(member):
    """
    Calculate engagement score for a member (0-100).
    
    Scoring:
    - Attendance rate: 40 points
    - Payment rate: 30 points
    - Recent activity: 20 points
    - Role/leadership: 10 points
    
    Args:
        member: Member object
        
    Returns:
        dict: {
            'score': int (0-100),
            'breakdown': dict with component scores,
            'grade': str (A+, A, B, C, D, F)
        }
    """
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    score = 0
    breakdown = {}
    
    # 1. Attendance Rate (40 points)
    total_meetings = MeetingInfo.objects.count()
    if total_meetings > 0:
        attended = MemberAttendance.objects.filter(
            member_id=member,
            attendance_status=True
        ).count()
        attendance_rate = (attended / total_meetings) * 100
        attendance_score = min(40, (attendance_rate / 100) * 40)
        score += attendance_score
        breakdown['attendance'] = round(attendance_score, 1)
    else:
        breakdown['attendance'] = 0
    
    # 2. Payment Rate (30 points)
    attended_meetings = MemberAttendance.objects.filter(
        member_id=member,
        attendance_status=True
    ).count()
    if attended_meetings > 0:
        paid_meetings = MemberAttendance.objects.filter(
            member_id=member,
            attendance_status=True,
            attendance_fee_status=True
        ).count()
        payment_rate = (paid_meetings / attended_meetings) * 100
        payment_score = min(30, (payment_rate / 100) * 30)
        score += payment_score
        breakdown['payment'] = round(payment_score, 1)
    else:
        breakdown['payment'] = 0
    
    # 3. Recent Activity (20 points) - Last 3 months
    three_months_ago = datetime.now() - timedelta(days=90)
    recent_meetings = MeetingInfo.objects.filter(
        meeting_date__gte=three_months_ago.date()
    ).count()
    
    if recent_meetings > 0:
        recent_attendance = MemberAttendance.objects.filter(
            member_id=member,
            meeting_date__meeting_date__gte=three_months_ago.date(),
            attendance_status=True
        ).count()
        recent_rate = (recent_attendance / recent_meetings) * 100
        recent_score = min(20, (recent_rate / 100) * 20)
        score += recent_score
        breakdown['recent_activity'] = round(recent_score, 1)
    else:
        breakdown['recent_activity'] = 0
    
    # 4. Role/Leadership (10 points)
    role_score = 0
    if member.member_role:
        if member.member_role in ['PRESIDENT', 'SECRETARY', 'TREASURY']:
            role_score = 10
        elif member.member_role in ['VICE_PRESIDENT', 'VICE_SECRETARY', 'VICE_TREASURY']:
            role_score = 8
        elif member.member_role == 'COMMITTEE_MEMBER':
            role_score = 5
    score += role_score
    breakdown['leadership'] = role_score
    
    # Determine grade
    final_score = round(score, 1)
    if final_score >= 90:
        grade = 'A+'
    elif final_score >= 80:
        grade = 'A'
    elif final_score >= 70:
        grade = 'B'
    elif final_score >= 60:
        grade = 'C'
    elif final_score >= 50:
        grade = 'D'
    else:
        grade = 'F'
    
    return {
        'score': final_score,
        'breakdown': breakdown,
        'grade': grade
    }


def award_badges_to_member(member):
    """
    Check and award badges to a member based on their achievements.
    
    Args:
        member: Member object
        
    Returns:
        list: List of newly awarded badge types
    """
    from .models import MemberBadge, BadgeType
    from datetime import datetime, timedelta
    
    newly_awarded = []
    
    # Get all meetings and attendance
    all_meetings = MeetingInfo.objects.all().order_by('-meeting_date')
    member_attendance = MemberAttendance.objects.filter(member_id=member)
    
    # 1. Perfect Attendance (100% attendance)
    total_meetings = all_meetings.count()
    if total_meetings > 0:
        attended = member_attendance.filter(attendance_status=True).count()
        if attended == total_meetings and attended >= 5:
            if not MemberBadge.objects.filter(member=member, badge_type=BadgeType.PERFECT_ATTENDANCE).exists():
                MemberBadge.objects.create(
                    member=member,
                    badge_type=BadgeType.PERFECT_ATTENDANCE,
                    description=f"Attended all {total_meetings} meetings"
                )
                newly_awarded.append(BadgeType.PERFECT_ATTENDANCE)
    
    # 2. Attendance Streaks
    streak_5 = check_attendance_streak(member, 5)
    streak_10 = check_attendance_streak(member, 10)
    
    if streak_10:
        if not MemberBadge.objects.filter(member=member, badge_type=BadgeType.ATTENDANCE_STREAK_10).exists():
            MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.ATTENDANCE_STREAK_10,
                description="Attended 10 consecutive meetings"
            )
            newly_awarded.append(BadgeType.ATTENDANCE_STREAK_10)
    elif streak_5:
        if not MemberBadge.objects.filter(member=member, badge_type=BadgeType.ATTENDANCE_STREAK_5).exists():
            MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.ATTENDANCE_STREAK_5,
                description="Attended 5 consecutive meetings"
            )
            newly_awarded.append(BadgeType.ATTENDANCE_STREAK_5)
    
    # 3. Payment Champion (100% payment rate)
    attended_meetings = member_attendance.filter(attendance_status=True).count()
    if attended_meetings >= 5:
        paid_meetings = member_attendance.filter(
            attendance_status=True,
            attendance_fee_status=True
        ).count()
        if paid_meetings == attended_meetings:
            if not MemberBadge.objects.filter(member=member, badge_type=BadgeType.PAYMENT_CHAMPION).exists():
                MemberBadge.objects.create(
                    member=member,
                    badge_type=BadgeType.PAYMENT_CHAMPION,
                    description="100% payment rate"
                )
                newly_awarded.append(BadgeType.PAYMENT_CHAMPION)
    
    # 4. Founding Member (member for over 2 years)
    member_age_days = (datetime.now().date() - member.member_join_at).days
    if member_age_days >= 730:  # 2 years
        if not MemberBadge.objects.filter(member=member, badge_type=BadgeType.FOUNDING_MEMBER).exists():
            MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.FOUNDING_MEMBER,
                description=f"Member for {member_age_days // 365} years"
            )
            newly_awarded.append(BadgeType.FOUNDING_MEMBER)
    
    # 5. Leadership Badges
    if member.member_role in ['PRESIDENT', 'SECRETARY', 'TREASURY', 'VICE_PRESIDENT', 'VICE_SECRETARY', 'VICE_TREASURY']:
        if not MemberBadge.objects.filter(member=member, badge_type=BadgeType.LEADER).exists():
            MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.LEADER,
                description=f"Serving as {member.get_member_role_display()}"
            )
            newly_awarded.append(BadgeType.LEADER)
    elif member.member_role == 'COMMITTEE_MEMBER':
        if not MemberBadge.objects.filter(member=member, badge_type=BadgeType.COMMITTEE).exists():
            MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.COMMITTEE,
                description="Committee Member"
            )
            newly_awarded.append(BadgeType.COMMITTEE)
    
    return newly_awarded


def check_attendance_streak(member, required_streak):
    """
    Check if member has attended N consecutive meetings.
    
    Args:
        member: Member object
        required_streak: Number of consecutive meetings
        
    Returns:
        bool: True if streak exists
    """
    recent_meetings = MeetingInfo.objects.all().order_by('-meeting_date')[:required_streak]
    
    if recent_meetings.count() < required_streak:
        return False
    
    for meeting in recent_meetings:
        attendance = MemberAttendance.objects.filter(
            member_id=member,
            meeting_date=meeting,
            attendance_status=True
        ).exists()
        if not attendance:
            return False
    
    return True


def get_smart_recommendations():
    """
    Generate smart recommendations for administrators.
    
    Returns:
        list: List of recommendation dictionaries with:
            - type: str (warning, info, success)
            - title: str
            - message: str
            - action: str (optional)
            - link: str (optional)
    """
    from datetime import datetime, timedelta
    from django.db.models import Count, Q
    
    recommendations = []
    
    # 1. Identify at-risk members (low attendance in last 3 meetings)
    recent_meetings = MeetingInfo.objects.all().order_by('-meeting_date')[:3]
    if recent_meetings.count() >= 3:
        active_members = Member.objects.filter(member_is_active=True)
        for member in active_members:
            attended = MemberAttendance.objects.filter(
                member_id=member,
                meeting_date__in=recent_meetings,
                attendance_status=True
            ).count()
            
            if attended == 0:
                recommendations.append({
                    'type': 'warning',
                    'title': f'At-Risk Member: {member.member_id}',
                    'message': f'{member.member_first_name} {member.member_last_name} has missed the last 3 meetings.',
                    'action': 'Follow up',
                    'link': f'/member/view/{member.member_id}'
                })
    
    # 2. Members with unpaid fees
    unpaid_count = MemberAttendance.objects.filter(
        attendance_status=True,
        attendance_fee_status=False
    ).values('member_id').distinct().count()
    
    if unpaid_count > 0:
        recommendations.append({
            'type': 'info',
            'title': 'Unpaid Fees',
            'message': f'{unpaid_count} members have attended but not paid fees.',
            'action': 'View details',
            'link': '/attendance/date/all'
        })
    
    # 3. Suggest next meeting if none scheduled soon
    latest_meeting = MeetingInfo.objects.first()
    if latest_meeting:
        days_since = (datetime.now().date() - latest_meeting.meeting_date).days
        if days_since > 14:
            recommendations.append({
                'type': 'info',
                'title': 'Schedule Next Meeting',
                'message': f'Last meeting was {days_since} days ago. Consider scheduling the next meeting.',
                'action': 'Add meeting',
                'link': '/meeting/add/'
            })
    
    # 4. Celebrate high performers
    active_members = Member.objects.filter(member_is_active=True)
    for member in active_members[:5]:  # Check top 5
        score_data = calculate_member_engagement_score(member)
        if score_data['score'] >= 90:
            recommendations.append({
                'type': 'success',
                'title': f'Top Performer: {member.member_id}',
                'message': f'{member.member_first_name} {member.member_last_name} has an engagement score of {score_data["score"]}!',
                'action': 'View profile',
                'link': f'/member/view/{member.member_id}'
            })
    
    return recommendations[:10]  # Limit to 10 recommendations


def predict_next_meeting_attendance():
    """
    Predict attendance for the next meeting using simple moving average.
    
    Returns:
        dict: {
            'predicted_count': int,
            'confidence': str (low, medium, high),
            'based_on_meetings': int
        }
    """
    recent_meetings = MeetingInfo.objects.all().order_by('-meeting_date')[:5]
    
    if recent_meetings.count() < 3:
        return {
            'predicted_count': 0,
            'confidence': 'low',
            'based_on_meetings': recent_meetings.count(),
            'message': 'Not enough data for prediction'
        }
    
    attendance_counts = []
    for meeting in recent_meetings:
        count = MemberAttendance.objects.filter(
            meeting_date=meeting,
            attendance_status=True
        ).count()
        attendance_counts.append(count)
    
    # Simple moving average
    predicted = sum(attendance_counts) // len(attendance_counts)
    
    # Determine confidence based on variance
    avg = sum(attendance_counts) / len(attendance_counts)
    variance = sum((x - avg) ** 2 for x in attendance_counts) / len(attendance_counts)
    
    if variance < 5:
        confidence = 'high'
    elif variance < 15:
        confidence = 'medium'
    else:
        confidence = 'low'
    
    return {
        'predicted_count': predicted,
        'confidence': confidence,
        'based_on_meetings': len(attendance_counts),
        'recent_counts': attendance_counts
    }
