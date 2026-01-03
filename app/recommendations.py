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
    """Get recommendations related to meetings with scheduling insights"""
    recommendations = []
    
    # Check if no meetings scheduled for next 30 days
    upcoming_meetings = MeetingInfo.objects.filter(
        meeting_date__gte=date.today(),
        meeting_date__lte=date.today() + timedelta(days=30)
    ).count()
    
    if upcoming_meetings == 0:
        # Check average meeting frequency
        all_meetings = MeetingInfo.objects.all().order_by('meeting_date')
        if all_meetings.count() > 1:
            first_meeting = all_meetings.first()
            last_meeting = all_meetings.last()
            if first_meeting and last_meeting:
                days_diff = (last_meeting.meeting_date - first_meeting.meeting_date).days
                avg_days = days_diff / all_meetings.count() if all_meetings.count() > 0 else 30
                
                recommendations.append({
                    'type': 'warning',
                    'title': 'Schedule Upcoming Meeting',
                    'message': f'No meetings scheduled for the next 30 days. Based on your average meeting frequency ({avg_days:.0f} days), it\'s time to schedule the next meeting.',
                    'action': 'Add Meeting',
                    'url': '/meeting/add/',
                    'priority': 9,
                    'icon': 'calendar-plus'
                })
        else:
            recommendations.append({
                'type': 'info',
                'title': 'Schedule Your First Meeting',
                'message': 'No meetings scheduled. Start by scheduling your first meeting to begin tracking attendance and engagement.',
                'action': 'Add Meeting',
                'url': '/meeting/add/',
                'priority': 9,
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
                'type': 'warning',
                'title': 'Mark Attendance for Recent Meeting',
                'message': f'Attendance not marked for meeting on {meeting.meeting_date.strftime("%d %b %Y")}. Complete attendance records are essential for accurate reporting.',
                'action': 'Mark Attendance',
                'url': f'/attendance/date/{meeting.meeting_id}',
                'priority': 10,
                'icon': 'check-circle'
            })
            break  # Only show one at a time
    
    # Meeting frequency optimization
    today = date.today()
    last_three_months = today - timedelta(days=90)
    recent_meeting_count = MeetingInfo.objects.filter(
        meeting_date__gte=last_three_months
    ).count()
    
    if recent_meeting_count < 2:
        recommendations.append({
            'type': 'info',
            'title': 'Increase Meeting Frequency',
            'message': f'Only {recent_meeting_count} meeting(s) in the last 3 months. Regular meetings improve member engagement and community building. Consider monthly meetings.',
            'action': 'Add Meeting',
            'url': '/meeting/add/',
            'priority': 6,
            'icon': 'calendar-alt'
        })
    
    return recommendations


def get_member_recommendations():
    """Get recommendations related to members with growth insights"""
    recommendations = []
    
    # Check for inactive members
    inactive_count = Member.objects.filter(member_is_active=False).count()
    active_count = Member.objects.filter(member_is_active=True).count()
    total_members = Member.objects.count()
    
    if inactive_count > 0:
        inactive_percentage = (inactive_count / total_members * 100) if total_members > 0 else 0
        recommendations.append({
            'type': 'warning',
            'title': f'Review {inactive_count} Inactive Member(s)',
            'message': f'You have {inactive_count} inactive member(s) ({inactive_percentage:.1f}% of total). Consider reactivation campaigns or exit surveys to understand reasons.',
            'action': 'View Members',
            'url': '/member/list/?is_active=false',
            'priority': 6,
            'icon': 'user-times'
        })
    
    # Growth opportunity: Check member growth trend
    today = date.today()
    six_months_ago = today - timedelta(days=180)
    new_members_recent = Member.objects.filter(member_join_at__gte=six_months_ago).count()
    
    if new_members_recent == 0 and active_count > 0:
        recommendations.append({
            'type': 'info',
            'title': 'Member Growth Opportunity',
            'message': 'No new members joined in the last 6 months. Consider organizing recruitment events or outreach programs to grow membership.',
            'action': 'Register Member',
            'url': '/member/register/',
            'priority': 6,
            'icon': 'user-plus'
        })
    elif new_members_recent > 0:
        recommendations.append({
            'type': 'success',
            'title': 'Healthy Member Growth',
            'message': f'Great! {new_members_recent} new member(s) joined in the last 6 months. Continue engagement strategies to retain them.',
            'action': 'View Members',
            'url': '/member/list/',
            'priority': 4,
            'icon': 'users'
        })
    
    # Check for members without roles assigned
    members_without_roles = Member.objects.filter(
        member_is_active=True,
        member_role=''
    ).count()
    
    if members_without_roles > 5:
        recommendations.append({
            'type': 'info',
            'title': 'Role Assignment Opportunity',
            'message': f'{members_without_roles} active members don\'t have roles assigned. Assigning roles can improve engagement and sense of belonging.',
            'action': 'View Members',
            'url': '/member/list/',
            'priority': 5,
            'icon': 'user-tag'
        })
    
    # Age distribution insights
    from datetime import date as date_obj
    today = date_obj.today()
    cutoff_date = date_obj(today.year - 18, today.month, today.day)
    if today.month == 2 and today.day == 29:
        cutoff_date = date_obj(today.year - 18, 2, 28)
    
    under_18_count = Member.objects.filter(member_dob__gt=cutoff_date, member_is_active=True).count()
    over_18_count = Member.objects.filter(member_dob__lte=cutoff_date, member_is_active=True).count()
    
    if under_18_count > 0 and over_18_count > 0:
        ratio = over_18_count / under_18_count if under_18_count > 0 else 0
        if ratio > 2:
            recommendations.append({
                'type': 'info',
                'title': 'Member Age Distribution Insight',
                'message': f'You have {over_18_count} adult members vs {under_18_count} youth members. Consider programs that bridge both age groups for better community building.',
                'action': 'View Members',
                'url': '/member/list/',
                'priority': 4,
                'icon': 'users-cog'
            })
    
    return recommendations


def get_attendance_recommendations():
    """Get recommendations related to attendance with trend analysis"""
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
                'type': 'warning',
                'title': 'Low Attendance Rate - Action Needed',
                'message': f'Current year attendance rate is {attendance_rate:.1f}%. Consider organizing engaging activities or reaching out to inactive members to boost participation.',
                'action': 'View Calendar',
                'url': '/calendar/',
                'priority': 9,
                'icon': 'chart-line'
            })
    
    # Trend analysis: Compare last 3 months vs previous 3 months
    today = date.today()
    three_months_ago = today - timedelta(days=90)
    six_months_ago = today - timedelta(days=180)
    
    recent_attendance = MemberAttendance.objects.filter(
        meeting_date__meeting_date__gte=three_months_ago,
        meeting_date__meeting_date__lte=today,
        attendance_status=True
    ).count()
    
    previous_attendance = MemberAttendance.objects.filter(
        meeting_date__meeting_date__gte=six_months_ago,
        meeting_date__meeting_date__lt=three_months_ago,
        attendance_status=True
    ).count()
    
    if previous_attendance > 0:
        trend_change = ((recent_attendance - previous_attendance) / previous_attendance) * 100
        if trend_change < -10:
            recommendations.append({
                'type': 'warning',
                'title': 'Declining Attendance Trend',
                'message': f'Attendance has decreased by {abs(trend_change):.1f}% in the last 3 months. Consider member engagement strategies or review meeting schedules.',
                'action': 'View Reports',
                'url': '/reports/builder/',
                'priority': 8,
                'icon': 'arrow-down'
            })
        elif trend_change > 10:
            recommendations.append({
                'type': 'success',
                'title': 'Growing Attendance Trend',
                'message': f'Great! Attendance has increased by {trend_change:.1f}% in the last 3 months. Keep up the momentum with engaging activities.',
                'action': 'View Calendar',
                'url': '/calendar/',
                'priority': 5,
                'icon': 'arrow-up'
            })
    
    # Check for members with declining attendance
    active_members = Member.objects.filter(member_is_active=True)
    declining_members = []
    for member in active_members[:10]:  # Check first 10
        recent_count = MemberAttendance.objects.filter(
            member_id=member,
            meeting_date__meeting_date__gte=three_months_ago,
            attendance_status=True
        ).count()
        previous_count = MemberAttendance.objects.filter(
            member_id=member,
            meeting_date__meeting_date__gte=six_months_ago,
            meeting_date__meeting_date__lt=three_months_ago,
            attendance_status=True
        ).count()
        
        if previous_count > 0 and recent_count < previous_count * 0.7:  # 30% decline
            declining_members.append(member)
    
    if len(declining_members) >= 3:
        recommendations.append({
            'type': 'warning',
            'title': 'Multiple Members Showing Declining Attendance',
            'message': f'{len(declining_members)} members have shown declining attendance. Consider reaching out to understand their needs and improve engagement.',
            'action': 'View Members',
            'url': '/member/list/',
            'priority': 7,
            'icon': 'user-friends'
        })
    
    return recommendations


def get_payment_recommendations():
    """Get recommendations related to payments with trend analysis"""
    recommendations = []
    
    # Check for unpaid fees
    unpaid_fees = MemberAttendance.objects.filter(
        attendance_status=True,
        attendance_fee_status=False
    ).select_related('meeting_date').aggregate(
        total=Sum('meeting_date__meeting_fee')
    )['total'] or 0
    
    if unpaid_fees > 0:
        unpaid_count = MemberAttendance.objects.filter(
            attendance_status=True,
            attendance_fee_status=False
        ).values('member_id').distinct().count()
        
        recommendations.append({
            'type': 'warning',
            'title': f'Collect Outstanding Fees',
            'message': f'Rs. {unpaid_fees:,} in unpaid fees from {unpaid_count} member(s). Implement payment reminders or flexible payment plans to improve collection rate.',
            'action': 'View Payments',
            'url': '/payment/list/',
            'priority': 8,
            'icon': 'money-bill-wave'
        })
    
    # Payment trend analysis
    today = date.today()
    three_months_ago = today - timedelta(days=90)
    six_months_ago = today - timedelta(days=180)
    
    recent_paid = MemberAttendance.objects.filter(
        meeting_date__meeting_date__gte=three_months_ago,
        attendance_status=True,
        attendance_fee_status=True
    ).select_related('meeting_date').aggregate(
        total=Sum('meeting_date__meeting_fee')
    )['total'] or 0
    
    previous_paid = MemberAttendance.objects.filter(
        meeting_date__meeting_date__gte=six_months_ago,
        meeting_date__meeting_date__lt=three_months_ago,
        attendance_status=True,
        attendance_fee_status=True
    ).select_related('meeting_date').aggregate(
        total=Sum('meeting_date__meeting_fee')
    )['total'] or 0
    
    if previous_paid > 0:
        payment_trend = ((recent_paid - previous_paid) / previous_paid) * 100
        if payment_trend < -15:
            recommendations.append({
                'type': 'warning',
                'title': 'Declining Payment Collection',
                'message': f'Payment collection has decreased by {abs(payment_trend):.1f}% in the last 3 months. Review payment processes and member communication.',
                'action': 'View Payments',
                'url': '/payment/list/',
                'priority': 7,
                'icon': 'chart-line'
            })
        elif payment_trend > 15:
            recommendations.append({
                'type': 'success',
                'title': 'Improving Payment Collection',
                'message': f'Excellent! Payment collection has increased by {payment_trend:.1f}% in the last 3 months. Your payment strategies are working well.',
                'action': 'View Payments',
                'url': '/payment/list/',
                'priority': 4,
                'icon': 'check-circle'
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

