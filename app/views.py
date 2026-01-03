from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import *
from .models import *
from django.contrib.auth.models import User
from datetime import datetime
from django.db.models import Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from openpyxl import Workbook
from .constants import PAGINATION_MEMBER_ATTENDANCE_REPORT


def context_data(request):
    from datetime import datetime
    current_year = datetime.now().year
    
    context = {
        'page_name': '',
        'system_name': 'Membership Management System',
        'auther_name': 'Anjana Narasinghe',
        'project_start_date': '2023',
        'current_year': current_year,
        'navbar_top': True,
        'footer': True
    }

    return context


@login_required
def dashboard(request):
    from django.db.models import Q, Sum, Avg, F
    from collections import defaultdict
    from django.core.cache import cache
    from .utils import check_and_deactivate_inactive_members
    from .constants import CONSECUTIVE_MEETINGS_FOR_DEACTIVATION

    # Automatically check and deactivate inactive members (runs once per hour via cache)
    # This is a backup check - signals handle it after attendance is saved
    # Works in shared hosting/cPanel - no cron jobs needed!
    CACHE_KEY_DASHBOARD_CHECK = 'dashboard_deactivation_check'
    try:
        cache_value = cache.get(CACHE_KEY_DASHBOARD_CHECK)
        if not cache_value:
            try:
                check_and_deactivate_inactive_members(
                    consecutive_meetings=CONSECUTIVE_MEETINGS_FOR_DEACTIVATION,
                    dry_run=False
                )
                # Cache for 1 hour to prevent running too frequently
                try:
                    cache.set(CACHE_KEY_DASHBOARD_CHECK, True, 3600)
                except Exception:
                    pass  # Cache might not be available
            except Exception:
                # Silently fail to not interrupt dashboard loading
                pass
    except Exception:
        # If cache is completely unavailable, skip the check
        pass

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Basic counts
    all_members = Member.objects.all().count()
    active_members = Member.objects.filter(member_is_active=True).count()
    passive_members = Member.objects.filter(member_is_active=False).count()
    all_staff = User.objects.all().count()
    all_meeting = MeetingInfo.objects.all().count()

    # Current year statistics
    meetings_this_year = MeetingInfo.objects.filter(meeting_date__year=current_year).count()
    total_attendance_this_year = MemberAttendance.objects.filter(
        meeting_date__meeting_date__year=current_year
    ).count()
    present_count_this_year = MemberAttendance.objects.filter(
        meeting_date__meeting_date__year=current_year,
        attendance_status=True
    ).count()
    paid_count_this_year = MemberAttendance.objects.filter(
        meeting_date__meeting_date__year=current_year,
        attendance_fee_status=True
    ).count()

    # Calculate attendance rate
    if total_attendance_this_year > 0:
        attendance_rate = (present_count_this_year / total_attendance_this_year) * 100
    else:
        attendance_rate = 0

    # Calculate fee payment rate
    if present_count_this_year > 0:
        fee_payment_rate = (paid_count_this_year / present_count_this_year) * 100
    else:
        fee_payment_rate = 0

    # Monthly attendance data for current year
    monthly_attendance = (
        MemberAttendance.objects
        .filter(meeting_date__meeting_date__year=current_year, attendance_status=True)
        .select_related('meeting_date')
    )
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = [0] * 12
    for attendance in monthly_attendance:
        month_index = attendance.meeting_date.meeting_date.month - 1
        if 0 <= month_index < 12:
            monthly_data[month_index] += 1

    # Meeting attendance over time (current year)
    meeting_attendance_counts = (
        MemberAttendance.objects
        .filter(meeting_date__meeting_date__year=current_year, attendance_status=True)
        .values('meeting_date__meeting_date')
        .annotate(attendance_count=Count('attendance_id'))
        .order_by('meeting_date__meeting_date')
    )

    meeting_dates = [entry['meeting_date__meeting_date'].strftime('%d %b') for entry in meeting_attendance_counts]
    attendance_counts = [entry['attendance_count'] for entry in meeting_attendance_counts]

    # Attendance vs Fee Payment comparison
    attendance_vs_fee = {
        'present_paid': MemberAttendance.objects.filter(
            meeting_date__meeting_date__year=current_year,
            attendance_status=True,
            attendance_fee_status=True
        ).count(),
        'present_unpaid': MemberAttendance.objects.filter(
            meeting_date__meeting_date__year=current_year,
            attendance_status=True,
            attendance_fee_status=False
        ).count(),
        'absent': MemberAttendance.objects.filter(
            meeting_date__meeting_date__year=current_year,
            attendance_status=False
        ).count(),
    }

    # Latest meeting info
    latest_meeting = None
    latest_meeting_member_count = 0
    try:
        if MemberAttendance.objects.exists():
            latest_meeting = MemberAttendance.objects.latest('meeting_date')
            latest_meeting_member_count = MemberAttendance.objects.filter(
                meeting_date=latest_meeting.meeting_date
            ).values('member_id').distinct().count()
    except:
        latest_meeting = None
        latest_meeting_member_count = 0

    # Member status distribution for pie chart
    member_status_data = {
        'active': active_members,
        'passive': passive_members
    }

    # Calculate percentages
    if all_members != 0:
        percentage_active = (active_members / all_members) * 100
        percentage_passive = (passive_members / all_members) * 100
    else:
        percentage_active = 0
        percentage_passive = 0

    context = context_data(request)
    context['page_name'] = 'Dashboard'
    context['current_year'] = current_year
    
    # Basic stats
    context['all_members'] = all_members
    context['active_members'] = active_members
    context['passive_members'] = passive_members
    context['all_staff'] = all_staff
    context['all_meeting'] = all_meeting
    context['meetings_this_year'] = meetings_this_year
    
    # Percentages
    context['active_members_percentage'] = f'{percentage_active:.1f}'
    context['passive_members_percentage'] = f'{percentage_passive:.1f}'
    context['attendance_rate'] = f'{attendance_rate:.1f}'
    context['fee_payment_rate'] = f'{fee_payment_rate:.1f}'
    
    # Chart data - format for JavaScript
    import json
    context['meeting_dates'] = json.dumps(meeting_dates)
    context['attendance_counts'] = json.dumps(attendance_counts)
    context['months'] = json.dumps(months)
    context['monthly_data'] = json.dumps(monthly_data)
    context['member_status_data'] = member_status_data
    context['attendance_vs_fee'] = attendance_vs_fee
    
    # Latest meeting
    context['latest_meeting'] = latest_meeting
    context['latest_meeting_member_count'] = latest_meeting_member_count
    context['present_count_this_year'] = present_count_this_year
    context['paid_count_this_year'] = paid_count_this_year

    # Member Roles Data for Dashboard Widgets
    from .models import MemberRole
    from .constants import MAIN_ROLES, SUB_ROLES
    
    # Main 3 roles (President, Secretary, Treasury)
    main_role_members = Member.objects.filter(
        member_role__in=MAIN_ROLES,
        member_is_active=True
    ).order_by('member_role')
    
    # Sub 3 roles (Vice President, Vice Secretary, Vice Treasury)
    sub_role_members = Member.objects.filter(
        member_role__in=SUB_ROLES,
        member_is_active=True
    ).order_by('member_role')
    
    # Committee Members
    committee_members = Member.objects.filter(
        member_role=MemberRole.COMMITTEE_MEMBER,
        member_is_active=True
    ).order_by('member_first_name', 'member_last_name')
    
    context['main_role_members'] = main_role_members
    context['sub_role_members'] = sub_role_members
    context['committee_members'] = committee_members
    
    # Finance Calculations
    # Total collected: Sum of meeting_fee for all attendance records where fee is paid
    total_collected_result = MemberAttendance.objects.filter(
        attendance_fee_status=True
    ).select_related('meeting_date').aggregate(
        total=Sum('meeting_date__meeting_fee')
    )
    total_collected = total_collected_result['total'] if total_collected_result['total'] else 0
    
    # Total to receive: Sum of meeting_fee for members who attended but didn't pay
    total_to_receive_result = MemberAttendance.objects.filter(
        attendance_status=True,
        attendance_fee_status=False
    ).select_related('meeting_date').aggregate(
        total=Sum('meeting_date__meeting_fee')
    )
    total_to_receive = total_to_receive_result['total'] if total_to_receive_result['total'] else 0
    
    # Format numbers with commas for better readability (meeting_fee is IntegerField, so no decimals)
    context['total_collected'] = f'{int(total_collected):,}'
    context['total_to_receive'] = f'{int(total_to_receive):,}'
    
    # Calendar widget data - upcoming holidays and meetings
    from .holidays_utils import get_upcoming_holidays
    from datetime import date
    upcoming_holidays = get_upcoming_holidays(5, date.today())
    context['upcoming_holidays'] = upcoming_holidays
    
    # Upcoming meetings (next 5)
    upcoming_meetings = MeetingInfo.objects.filter(
        meeting_date__gte=date.today()
    ).order_by('meeting_date')[:5]
    context['upcoming_meetings'] = upcoming_meetings
    
    # Smart Recommendations
    from .recommendations import get_smart_recommendations
    recommendations = get_smart_recommendations(request.user)
    context['recommendations'] = recommendations

    return render(request, 'dashboard.html', context)


@login_required
def member_attendance_report(request, member_id):
    context = context_data(request)
    context['page_name'] = 'Attendance Report'

    current_year = datetime.now().year
    meetings_in_current_year = MeetingInfo.objects.filter(meeting_date__year=current_year).count()
    member_attendance_current_year = MemberAttendance.objects.filter(
        meeting_date__meeting_date__year=current_year,
        member_id=member_id,
        attendance_status=True
    ).count()
    member_fee_present_days = MemberAttendance.objects.filter(
        meeting_date__meeting_date__year=current_year,
        member_id=member_id,
        attendance_fee_status=True
    ).count()

    if meetings_in_current_year != 0:
        annual_member_present = (member_attendance_current_year / meetings_in_current_year) * 100
        format_annual_member_present = f"{annual_member_present:.1f}"
        context['member_attendance_percentage'] = format_annual_member_present
    else:
        context['member_attendance_percentage'] = "0.0"
    
    # Calculate fee percentage only if member has attended at least one meeting
    if member_attendance_current_year != 0:
        member_fee_percentage = (member_fee_present_days / member_attendance_current_year) * 100
        format_member_fee_percentage = f"{member_fee_percentage:.1f}"
        context['member_fee_percentage'] = format_member_fee_percentage
    else:
        context['member_fee_percentage'] = "0.0"
    
    context['current_year'] = current_year

    try:
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        
        member = get_object_or_404(Member, member_id=member_id)
        
        # Optimize query with select_related
        attendances_list = MemberAttendance.objects.filter(
            member_id=member_id
        ).select_related('meeting_date').order_by('-meeting_date__meeting_date')
        
        # Pagination
        paginator = Paginator(attendances_list, PAGINATION_MEMBER_ATTENDANCE_REPORT)
        page = request.GET.get('page', 1)
        
        try:
            attendances = paginator.page(page)
        except PageNotAnInteger:
            attendances = paginator.page(1)
        except EmptyPage:
            attendances = paginator.page(paginator.num_pages)
        
        context['attendances'] = attendances
        context['page_obj'] = attendances  # For pagination template
        context['member'] = member
        return render(request, 'report/member_attendance.html', context)
    except Exception as e:
        messages.error(request, f"Error loading attendance report: {str(e)}")
        return redirect('member_list')


@login_required
def member_qr_generator(request, member_id):
    try:
        member = get_object_or_404(Member, member_id=member_id)
        from .utils import generate_qr_code
        
        member.member_qr_code = generate_qr_code(member_id)
        member.save()
        messages.success(request, 'QR code generated successfully.')
        return redirect('member_view', member_id)
    except Exception as e:
        messages.error(request, f"Error generating QR code: {str(e)}")
        return redirect('member_list')


@user_passes_test(lambda u: u.is_superuser)
def export_member_details(request):
    """Export members with format selection, column selection, and filter support"""
    from .search_utils import search_members
    from .export_utils import export_members_excel, export_members_pdf
    from datetime import date
    
    # Get data from POST or GET
    data_source = request.POST if request.method == 'POST' else request.GET
    
    # Get filters from request (same as member_list)
    search_query = data_source.get('search', '').strip()
    is_active_filter = data_source.get('is_active', '')
    role_filter = data_source.get('role', '')
    join_date_from = data_source.get('join_date_from', '')
    join_date_to = data_source.get('join_date_to', '')
    is_adults = data_source.get('is_adults', 'false').lower() == 'true'
    
    # Build filters dict
    filters = {}
    if search_query:
        # When searching, ignore other filters
        filters = {}
    else:
        if is_active_filter != '':
            filters['is_active'] = is_active_filter.lower() == 'true'
        if role_filter:
            filters['role'] = role_filter
        if join_date_from:
            filters['join_date_from'] = join_date_from
        if join_date_to:
            filters['join_date_to'] = join_date_to
    
    # Get members with filters
    members = search_members(search_query, filters)
    
    # Filter by age if needed
    today = date.today()
    cutoff_date = date(today.year - 18, today.month, today.day)
    if today.month == 2 and today.day == 29:
        cutoff_date = date(today.year - 18, 2, 28)
    
    if not is_adults:
        # Members under 18
        members = members.filter(member_dob__gt=cutoff_date)
    else:
        # Members 18+
        members = members.filter(member_dob__lte=cutoff_date)
    
    # Get export format and selected columns
    export_format = data_source.get('format', 'excel')
    selected_columns = data_source.getlist('columns')
    
    # Default columns if none selected
    if not selected_columns:
        selected_columns = ['member_id', 'initials', 'first_name', 'last_name', 'address', 
                           'dob', 'telephone', 'account', 'guardian', 'role', 'status', 'join_date']
    
    # Export based on format
    if export_format == 'pdf':
        return export_members_pdf(members, selected_columns=selected_columns)
    else:
        return export_members_excel(members, selected_columns=selected_columns)


@user_passes_test(lambda u: u.is_superuser)
def export_member_attendance_report(request, member_id):
    try:
        member = get_object_or_404(Member, member_id=member_id)
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{member.member_id} - {member.member_initials}{member.member_first_name} {member.member_last_name} Attendance Report.xlsx"'

        wb = Workbook()
        ws = wb.active
        ws.title = "Member Attendance Report"

        headers = ["Date", "Attendance State", "Member Fee State"]
        ws.append(headers)

        attendances = MemberAttendance.objects.filter(member_id=member_id)
        for attendance in attendances:
            member_attendance = 'Present' if attendance.attendance_status else 'Absent'
            member_fee = 'Payed' if attendance.attendance_fee_status else 'Not Payed'
            ws.append([attendance.meeting_date.meeting_date.strftime("%d/%m/%Y"), member_attendance, member_fee])

        wb.save(response)
        return response
    except Exception as e:
        messages.error(request, f"Error exporting report: {str(e)}")
        return redirect('member_list')


@user_passes_test(lambda u: u.is_superuser)
def export_attendance_report(request, meeting_id):
    try:
        meeting = get_object_or_404(MeetingInfo, meeting_id=meeting_id)
        attendances = MemberAttendance.objects.filter(meeting_date=meeting_id)

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{meeting.meeting_date.strftime("%d/%m/%Y")} - Attendance Report.xlsx"'

        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance Report"

        headers = ["Member ID", "Full Name", "Attendance State", "Member Fee State"]
        ws.append(headers)

        for attendance in attendances:
            member = attendance.member_id
            member_attendance = 'Present' if attendance.attendance_status else 'Absent'
            member_fee = 'Payed' if attendance.attendance_fee_status else 'Not Payed'
            full_name = f"{member.member_initials} {member.member_first_name} {member.member_last_name}"
            ws.append([member.member_id, full_name, member_attendance, member_fee])

        wb.save(response)
        return response
    except Exception as e:
        messages.error(request, f"Error exporting report: {str(e)}")
        return redirect('attendance_date_all')


@login_required
def qr_scanner(request):
    context = context_data(request)
    context['page_name'] = 'QR Scanner'
    
    if request.method == "POST":
        form = QRScann(request.POST)
        if form.is_valid():
            member_id = form.cleaned_data['member_id']
            # Additional check to ensure member exists and is active (optional)
            from .models import Member
            try:
                member = Member.objects.get(member_id=member_id)
                if not member.member_is_active:
                    messages.warning(request, f'Member "{member_id}" is inactive.')
                return redirect('member_view', member_id)
            except Member.DoesNotExist:
                messages.error(request, f'Member with ID "{member_id}" not found.')
                form = QRScann()
        else:
            # Form validation errors will be displayed
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = QRScann()
    
    context['form'] = form
    return render(request, 'scann/scan.html', context)

