"""
Advanced search and filtering utilities for all models
"""
from django.db.models import Q, CharField
from django.db.models.functions import Lower


def search_members(query, filters=None):
    """
    Advanced search for members with multiple field support
    """
    if not query and not filters:
        return Member.objects.all()
    
    qs = Member.objects.all()
    
    # Text search across multiple fields
    if query:
        query_lower = query.lower()
        qs = qs.filter(
            Q(member_id__icontains=query) |
            Q(member_first_name__icontains=query) |
            Q(member_last_name__icontains=query) |
            Q(member_initials__icontains=query) |
            Q(member_tp_number__icontains=query) |
            Q(member_address__icontains=query) |
            Q(member_guardian_name__icontains=query) |
            Q(member_acc_number__icontains=query)
        )
    
    # Apply filters
    if filters:
        if filters.get('is_active') is not None:
            qs = qs.filter(member_is_active=filters['is_active'])
        
        if filters.get('role'):
            qs = qs.filter(member_role=filters['role'])
        
        if filters.get('join_date_from'):
            qs = qs.filter(member_join_at__gte=filters['join_date_from'])
        
        if filters.get('join_date_to'):
            qs = qs.filter(member_join_at__lte=filters['join_date_to'])
    
    return qs.distinct()


def search_meetings(query, filters=None):
    """
    Advanced search for meetings
    """
    if not query and not filters:
        return MeetingInfo.objects.all()
    
    qs = MeetingInfo.objects.all()
    
    # Text search
    if query:
        qs = qs.filter(
            Q(meeting_id__icontains=query) |
            Q(meeting_date__icontains=query)
        )
    
    # Apply filters
    if filters:
        if filters.get('date_from'):
            qs = qs.filter(meeting_date__gte=filters['date_from'])
        
        if filters.get('date_to'):
            qs = qs.filter(meeting_date__lte=filters['date_to'])
        
        if filters.get('fee_min'):
            qs = qs.filter(meeting_fee__gte=filters['fee_min'])
        
        if filters.get('fee_max'):
            qs = qs.filter(meeting_fee__lte=filters['fee_max'])
    
    return qs.distinct()


def search_attendance(query, filters=None):
    """
    Advanced search for attendance records
    """
    if not query and not filters:
        return MemberAttendance.objects.all()
    
    qs = MemberAttendance.objects.select_related('member_id', 'meeting_date').all()
    
    # Text search
    if query:
        qs = qs.filter(
            Q(member_id__member_id__icontains=query) |
            Q(member_id__member_first_name__icontains=query) |
            Q(member_id__member_last_name__icontains=query) |
            Q(meeting_date__meeting_date__icontains=query)
        )
    
    # Apply filters
    if filters:
        if filters.get('member_id'):
            qs = qs.filter(member_id__member_id=filters['member_id'])
        
        if filters.get('meeting_id'):
            qs = qs.filter(meeting_date__meeting_id=filters['meeting_id'])
        
        if filters.get('attendance_status') is not None:
            qs = qs.filter(attendance_status=filters['attendance_status'])
        
        if filters.get('fee_status') is not None:
            qs = qs.filter(attendance_fee_status=filters['fee_status'])
        
        if filters.get('date_from'):
            qs = qs.filter(meeting_date__meeting_date__gte=filters['date_from'])
        
        if filters.get('date_to'):
            qs = qs.filter(meeting_date__meeting_date__lte=filters['date_to'])
    
    return qs.distinct()

