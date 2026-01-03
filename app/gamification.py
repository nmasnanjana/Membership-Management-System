"""
Gamification System - Badge Awarding Logic
Automatically awards badges to members based on their achievements
"""
from django.db.models import Count, Q, Min
from .models import Member, MemberBadge, MemberAttendance, MeetingInfo, BadgeType
from datetime import date, timedelta


def check_and_award_badges(member):
    """
    Check if a member qualifies for any badges and award them
    Returns list of newly awarded badges
    """
    newly_awarded = []
    
    # Get member's existing badges
    existing_badges = set(MemberBadge.objects.filter(member=member).values_list('badge_type', flat=True))
    
    # 1. Check Attendance Badges
    attendance_badges = check_attendance_badges(member, existing_badges)
    newly_awarded.extend(attendance_badges)
    
    # 2. Check Payment Badges
    payment_badges = check_payment_badges(member, existing_badges)
    newly_awarded.extend(payment_badges)
    
    # 3. Check Membership Badges
    membership_badges = check_membership_badges(member, existing_badges)
    newly_awarded.extend(membership_badges)
    
    # 4. Check Leadership Badges
    leadership_badges = check_leadership_badges(member, existing_badges)
    newly_awarded.extend(leadership_badges)
    
    return newly_awarded


def check_attendance_badges(member, existing_badges):
    """Check and award attendance-related badges"""
    newly_awarded = []
    
    # Get all attendance records for the member
    attendances = MemberAttendance.objects.filter(member_id=member)
    total_meetings = MeetingInfo.objects.count()
    member_attendances = attendances.filter(attendance_status=True)
    
    # Perfect Attendance - attended all meetings
    if BadgeType.PERFECT_ATTENDANCE not in existing_badges:
        if total_meetings > 0 and member_attendances.count() == total_meetings:
            badge = MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.PERFECT_ATTENDANCE,
                description=f"Attended all {total_meetings} meetings"
            )
            newly_awarded.append(badge)
    
    # Attendance Streaks
    if BadgeType.ATTENDANCE_STREAK_10 not in existing_badges:
        if check_attendance_streak(member, 10):
            badge = MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.ATTENDANCE_STREAK_10,
                description="Attended 10 consecutive meetings"
            )
            newly_awarded.append(badge)
    elif BadgeType.ATTENDANCE_STREAK_5 not in existing_badges:
        if check_attendance_streak(member, 5):
            badge = MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.ATTENDANCE_STREAK_5,
                description="Attended 5 consecutive meetings"
            )
            newly_awarded.append(badge)
    
    return newly_awarded


def check_attendance_streak(member, streak_length):
    """Check if member has a consecutive attendance streak"""
    meetings = MeetingInfo.objects.order_by('-meeting_date')[:streak_length]
    if meetings.count() < streak_length:
        return False
    
    attendances = MemberAttendance.objects.filter(
        member_id=member,
        meeting_date__in=meetings,
        attendance_status=True
    ).values_list('meeting_date_id', flat=True)
    
    return len(attendances) == streak_length


def check_payment_badges(member, existing_badges):
    """Check and award payment-related badges"""
    newly_awarded = []
    
    attendances = MemberAttendance.objects.filter(member_id=member)
    total_paid = attendances.filter(attendance_fee_status=True).count()
    total_attended = attendances.filter(attendance_status=True).count()
    
    # Always Paid - paid fees for all attended meetings
    if BadgeType.ALWAYS_PAID not in existing_badges:
        if total_attended > 0 and total_paid == total_attended:
            badge = MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.ALWAYS_PAID,
                description="Paid fees for all attended meetings"
            )
            newly_awarded.append(badge)
    
    # Payment Champion - paid fees for 20+ meetings
    if BadgeType.PAYMENT_CHAMPION not in existing_badges:
        if total_paid >= 20:
            badge = MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.PAYMENT_CHAMPION,
                description=f"Paid fees for {total_paid} meetings"
            )
            newly_awarded.append(badge)
    
    return newly_awarded


def check_membership_badges(member, existing_badges):
    """Check and award membership-related badges"""
    newly_awarded = []
    
    # Founding Member - joined in the first year (2023)
    if BadgeType.FOUNDING_MEMBER not in existing_badges:
        if member.member_join_at and member.member_join_at.year == 2023:
            badge = MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.FOUNDING_MEMBER,
                description="One of the founding members"
            )
            newly_awarded.append(badge)
    
    # Veteran Member - member for 2+ years
    if BadgeType.VETERAN_MEMBER not in existing_badges:
        if member.member_join_at:
            years_as_member = (date.today() - member.member_join_at).days / 365.25
            if years_as_member >= 2:
                badge = MemberBadge.objects.create(
                    member=member,
                    badge_type=BadgeType.VETERAN_MEMBER,
                    description=f"Member for {int(years_as_member)} years"
                )
                newly_awarded.append(badge)
    
    # Active Member - currently active
    if BadgeType.ACTIVE_MEMBER not in existing_badges:
        if member.member_is_active:
            badge = MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.ACTIVE_MEMBER,
                description="Active member"
            )
            newly_awarded.append(badge)
    
    return newly_awarded


def check_leadership_badges(member, existing_badges):
    """Check and award leadership-related badges"""
    newly_awarded = []
    
    # Leader - has a main or vice role
    if BadgeType.LEADER not in existing_badges:
        from .constants import MAIN_ROLES, SUB_ROLES
        if member.member_role in MAIN_ROLES + SUB_ROLES:
            badge = MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.LEADER,
                description=f"Leadership role: {member.get_member_role_display()}"
            )
            newly_awarded.append(badge)
    
    # Committee - is a committee member
    if BadgeType.COMMITTEE not in existing_badges:
        if member.member_role == 'COMMITTEE_MEMBER':
            badge = MemberBadge.objects.create(
                member=member,
                badge_type=BadgeType.COMMITTEE,
                description="Committee member"
            )
            newly_awarded.append(badge)
    
    return newly_awarded


def get_member_badge_summary(member):
    """Get a summary of all badges for a member"""
    badges = MemberBadge.objects.filter(member=member).order_by('-earned_date')
    return {
        'total': badges.count(),
        'badges': badges,
        'by_category': {
            'attendance': badges.filter(badge_type__startswith='ATTENDANCE') | badges.filter(badge_type='PERFECT_ATTENDANCE') | badges.filter(badge_type='EARLY_BIRD'),
            'payment': badges.filter(badge_type__startswith='PAYMENT') | badges.filter(badge_type='ALWAYS_PAID'),
            'membership': badges.filter(badge_type__startswith='FOUNDING') | badges.filter(badge_type__startswith='VETERAN') | badges.filter(badge_type='ACTIVE_MEMBER'),
            'leadership': badges.filter(badge_type__in=['LEADER', 'COMMITTEE']),
        }
    }

