"""
Calendar View with Sri Lankan Holidays
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .views import context_data
from .models import MeetingInfo, MemberAttendance
from .holidays_utils import get_sri_lankan_holidays, get_upcoming_holidays
from datetime import datetime, date
from calendar import monthrange, monthcalendar
from django.db.models import Count, Q


@login_required
def calendar_view(request):
    """Main calendar view showing meetings and holidays"""
    context = context_data(request)
    context['page_name'] = 'Calendar View'
    
    # Get year and month from request, default to current
    try:
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().month
    
    # Get all meetings for the month
    meetings = MeetingInfo.objects.filter(
        meeting_date__year=year,
        meeting_date__month=month
    ).order_by('meeting_date')
    
    # Get holidays for the month
    all_holidays = get_sri_lankan_holidays(year)
    month_holidays = [h for h in all_holidays if h['date'].month == month]
    
    # Get attendance stats for meetings
    meeting_stats = {}
    for meeting in meetings:
        attendance = MemberAttendance.objects.filter(meeting_date=meeting)
        meeting_stats[meeting.meeting_id] = {
            'total': attendance.count(),
            'present': attendance.filter(attendance_status=True).count(),
            'paid': attendance.filter(attendance_fee_status=True).count(),
        }
    
    # Build calendar grid
    cal = monthcalendar(year, month)
    calendar_data = []
    
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                day_date = date(year, month, day)
                day_info = {
                    'date': day_date,
                    'day': day,
                    'is_today': day_date == date.today(),
                    'meetings': [m for m in meetings if m.meeting_date == day_date],
                    'holidays': [h for h in month_holidays if h['date'] == day_date],
                }
                week_data.append(day_info)
        calendar_data.append(week_data)
    
    # Get upcoming holidays
    upcoming_holidays = get_upcoming_holidays(10)
    
    context.update({
        'year': year,
        'month': month,
        'month_name': datetime(year, month, 1).strftime('%B'),
        'calendar_data': calendar_data,
        'meetings': meetings,
        'month_holidays': month_holidays,
        'upcoming_holidays': upcoming_holidays,
        'meeting_stats': meeting_stats,
        'prev_month': month - 1 if month > 1 else 12,
        'prev_year': year if month > 1 else year - 1,
        'next_month': month + 1 if month < 12 else 1,
        'next_year': year if month < 12 else year + 1,
    })
    
    # Breadcrumb
    context['breadcrumb_items'] = [
        {'name': 'Dashboard', 'url': '/', 'icon': 'home'},
        {'name': 'Calendar', 'icon': 'calendar-alt'},
    ]
    
    return render(request, 'calendar/view.html', context)

