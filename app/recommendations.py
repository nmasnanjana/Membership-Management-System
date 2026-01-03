"""
Smart Recommendations System
Provides context-aware suggestions for actions based on current system state
"""
from django.db.models import Count, Q, Sum, Avg
from datetime import date, timedelta
from .models import Member, MeetingInfo, MemberAttendance, MemberBadge


def get_smart_recommendations(user, context=None):
    """
    Get smart recommendations based on current context
    Returns a list of recommendation dictionaries
    """
    recommendations = []
    
    # 1. Meeting-related recommendations
    meeting_recs = get_meeting_recommendations()
    recommendations.extend(meeting_recs)
    
    # 2. Member-related recommendations
    member_recs = get_member_recommendations()
    recommendations.extend(member_recs)
    
    # 3. Attendance-related recommendations
    attendance_recs = get_attendance_recommendations()
    recommendations.extend(attendance_recs)
    
    # 4. Payment-related recommendations
    payment_recs = get_payment_recommendations()
    recommendations.extend(payment_recs)
    
    # 5. Badge-related recommendations
    badge_recs = get_badge_recommendations()
    recommendations.extend(badge_recs)
    
    # Sort by priority (higher priority first)
    recommendations.sort(key=lambda x: x.get('priority', 5), reverse=True)
    
    return recommendations[:10]  # Return top 10 recommendations


def get_meeting_recommendations():
    """Get recommendations related to meetings"""
    recommendations = []
    
    # Check if no meetings scheduled for next 30 days
    upcoming_meetings = MeetingInfo.objects.filter(
        meeting_date__gte=date.today(),
        meeting_date__lte=date.today() + timedelta(days=30)
    ).count()
    
    if upcoming_meetings == 0:
        recommendations.append({
            'type': 'meeting',
            'title': 'Schedule Upcoming Meeting',
            'message': 'No meetings scheduled for the next 30 days. Consider scheduling the next meeting.',
            'action': 'Add Meeting',
            'url': '/meeting/add/',
            'priority': 8,
            'icon': 'calendar-plus'
        })
    
    # Check for meetings without attendance marked
    recent_meetings = MeetingInfo.objects.filter(
        meeting_date__lte=date.today(),
        meeting_date__gte=date.today() - timedelta(days=7)
    )
    
    for meeting in recent_meetings:
        attendance_count = MemberAttendance.objects.filter(meeting_date=meeting).count()
        if attendance_count == 0:
            recommendations.append({
                'type': 'attendance',
                'title': 'Mark Attendance for Recent Meeting',
                'message': f'Attendance not marked for meeting on {meeting.meeting_date.strftime("%d %b %Y")}.',
                'action': 'Mark Attendance',
                'url': f'/attendance/date/{meeting.meeting_id}',
                'priority': 9,
                'icon': 'check-circle'
            })
            break  # Only show one at a time
    
    return recommendations


def get_member_recommendations():
    """Get recommendations related to members"""
    recommendations = []
    
    # Check for inactive members
    inactive_count = Member.objects.filter(member_is_active=False).count()
    if inactive_count > 0:
        recommendations.append({
            'type': 'member',
            'title': f'Review {inactive_count} Inactive Member(s)',
            'message': f'You have {inactive_count} inactive member(s). Consider reviewing their status.',
            'action': 'View Members',
            'url': '/member/list/?is_active=false',
            'priority': 6,
            'icon': 'user-times'
        })
    
    # Check for members without roles assigned
    members_without_roles = Member.objects.filter(
        member_is_active=True,
        member_role=''
    ).count()
    
    if members_without_roles > 5:
        recommendations.append({
            'type': 'member',
            'title': 'Assign Roles to Members',
            'message': f'{members_without_roles} active members don\'t have roles assigned.',
            'action': 'View Members',
            'url': '/member/list/',
            'priority': 4,
            'icon': 'user-tag'
        })
    
    return recommendations


def get_attendance_recommendations():
    """Get recommendations related to attendance"""
    recommendations = []
    
    # Check for low attendance rate
    current_year = date.today().year
    total_attendance = MemberAttendance.objects.filter(
        meeting_date__meeting_date__year=current_year
    ).count()
    present_count = MemberAttendance.objects.filter(
        meeting_date__meeting_date__year=current_year,
        attendance_status=True
    ).count()
    
    if total_attendance > 0:
        attendance_rate = (present_count / total_attendance) * 100
        if attendance_rate < 50:
            recommendations.append({
                'type': 'attendance',
                'title': 'Low Attendance Rate',
                'message': f'Current year attendance rate is {attendance_rate:.1f}%. Consider engaging members.',
                'action': 'View Calendar',
                'url': '/calendar/',
                'priority': 7,
                'icon': 'chart-line'
            })
    
    return recommendations


def get_payment_recommendations():
    """Get recommendations related to payments"""
    recommendations = []
    
    # Check for unpaid fees
    unpaid_fees = MemberAttendance.objects.filter(
        attendance_status=True,
        attendance_fee_status=False
    ).select_related('meeting_date').aggregate(
        total=Sum('meeting_date__meeting_fee')
    )['total'] or 0
    
    if unpaid_fees > 0:
        recommendations.append({
            'type': 'payment',
            'title': f'Collect Outstanding Fees',
            'message': f'Rs. {unpaid_fees:,} in unpaid fees. Consider following up with members.',
            'action': 'View Reports',
            'url': '/',
            'priority': 8,
            'icon': 'money-bill-wave'
        })
    
    return recommendations


def get_badge_recommendations():
    """Get recommendations related to badges"""
    recommendations = []
    
    # Check for members close to earning badges
    active_members = Member.objects.filter(member_is_active=True)
    
    for member in active_members[:5]:  # Check first 5 active members
        badges = MemberBadge.objects.filter(member=member)
        if badges.count() == 0:
            # Check if they're close to earning a badge
            attendances = MemberAttendance.objects.filter(
                member_id=member,
                attendance_status=True
            ).count()
            
            if attendances >= 3:
                recommendations.append({
                    'type': 'badge',
                    'title': 'Award Badges',
                    'message': f'{member.member_first_name} {member.member_last_name} may qualify for badges. Check their achievements.',
                    'action': 'View Member',
                    'url': f'/member/view/{member.member_id}',
                    'priority': 3,
                    'icon': 'award'
                })
                break  # Only show one at a time
    
    return recommendations

