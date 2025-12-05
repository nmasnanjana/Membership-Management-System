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


def dashboard(request):
    from django.db.models import Q, Sum, Avg
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
        member_fee_percentage = (member_fee_present_days / member_attendance_current_year) * 100

        format_annual_member_present = f"{annual_member_present:.1f}"
        format_member_fee_percentage = f"{member_fee_percentage:.1f}"

        context['current_year'] = current_year
        context['member_attendance_percentage'] = format_annual_member_present
        context['member_fee_percentage'] = format_member_fee_percentage

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
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Member Details.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Member Details"

    headers = ["Member ID", "Full Name", "Address", "Date of Birth", "Telephone Number", "Account Number", "Join Date"]
    ws.append(headers)

    members = Member.objects.all()
    for member in members:
        ws.append([member.member_id, f'{member.member_initials}{member.member_first_name} {member.member_last_name}',
                   member.member_address, member.member_dob.strftime("%d/%m/%Y"), member.member_tp_number,
                   member.member_acc_number, member.member_join_at.strftime("%d/%m/%Y")])

    wb.save(response)
    return response


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


def qr_scanner(request):
    context = context_data(request)
    context['page_name'] = 'QR Scanner'
    if request.method == "POST":
        form = QRScann(request.POST)
        if form.is_valid():
            member_id = form.cleaned_data['member_id']
            return redirect('member_view', member_id)

    form = QRScann()
    context['form'] = form
    return render(request, 'scann/scan.html', context)

