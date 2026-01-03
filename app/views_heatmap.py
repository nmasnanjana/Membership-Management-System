"""
Attendance Heatmap View
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Member, MemberAttendance, MeetingInfo
from .views import context_data
from datetime import date, timedelta
from django.db.models import Count, Q


@login_required
def attendance_heatmap(request):
    """Visual attendance heatmap showing patterns over time"""
    context = context_data(request)
    context['page_name'] = 'Attendance Heatmap'
    
    # Get parameters
    member_id = request.GET.get('member_id', '')
    year = int(request.GET.get('year', date.today().year))
    
    # Get all members for dropdown
    members = Member.objects.filter(member_is_active=True).order_by('member_first_name', 'member_last_name')
    
    # Get all meetings for the year
    meetings = MeetingInfo.objects.filter(meeting_date__year=year).order_by('meeting_date')
    
    # Build heatmap data
    heatmap_data = []
    
    if member_id:
        # Single member heatmap
        try:
            member = Member.objects.get(member_id=member_id)
            member_attendances = MemberAttendance.objects.filter(
                member_id=member,
                meeting_date__meeting_date__year=year
            ).select_related('meeting_date')
            
            attendance_dict = {att.meeting_date.meeting_date: att.attendance_status for att in member_attendances}
            
            for meeting in meetings:
                attended = attendance_dict.get(meeting.meeting_date, None)
                heatmap_data.append({
                    'date': meeting.meeting_date,
                    'attended': attended,
                    'meeting_id': meeting.meeting_id,
                })
            
            context['selected_member'] = member
        except Member.DoesNotExist:
            pass
    else:
        # Overall heatmap - show attendance rate per meeting
        for meeting in meetings:
            total_members = Member.objects.filter(member_is_active=True).count()
            if total_members > 0:
                present_count = MemberAttendance.objects.filter(
                    meeting_date=meeting,
                    attendance_status=True
                ).count()
                attendance_rate = (present_count / total_members) * 100
            else:
                attendance_rate = 0
            
            heatmap_data.append({
                'date': meeting.meeting_date,
                'attendance_rate': attendance_rate,
                'present_count': present_count if total_members > 0 else 0,
                'total_members': total_members,
                'meeting_id': meeting.meeting_id,
            })
    
    # Get monthly summary
    monthly_summary = []
    for month in range(1, 13):
        month_meetings = meetings.filter(meeting_date__month=month)
        if member_id:
            month_attendances = MemberAttendance.objects.filter(
                member_id__member_id=member_id,
                meeting_date__meeting_date__year=year,
                meeting_date__meeting_date__month=month
            )
            present = month_attendances.filter(attendance_status=True).count()
            total = month_attendances.count()
            rate = (present / total * 100) if total > 0 else 0
        else:
            total = month_meetings.count()
            if total > 0:
                present = MemberAttendance.objects.filter(
                    meeting_date__meeting_date__year=year,
                    meeting_date__meeting_date__month=month,
                    attendance_status=True
                ).count()
                active_members = Member.objects.filter(member_is_active=True).count()
                rate = (present / (total * active_members) * 100) if active_members > 0 else 0
            else:
                present = 0
                rate = 0
        
        monthly_summary.append({
            'month': month,
            'month_name': date(year, month, 1).strftime('%B'),
            'total': total,
            'present': present,
            'rate': rate
        })
    
    context.update({
        'heatmap_data': heatmap_data,
        'monthly_summary': monthly_summary,
        'members': members,
        'member_id': member_id,
        'year': year,
        'years': range(2020, date.today().year + 2),
        'breadcrumb_items': [
            {'name': 'Dashboard', 'url': '/', 'icon': 'home'},
            {'name': 'Attendance Heatmap', 'icon': 'chart-area'},
        ]
    })
    
    return render(request, 'attendance/heatmap.html', context)

