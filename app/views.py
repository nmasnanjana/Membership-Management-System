from django.shortcuts import render, redirect
from .models import *
import os
import qrcode
from django.conf import settings
from django.contrib.auth.models import User
from datetime import datetime
from django.db.models import Count
from django.contrib.auth.decorators import login_required, user_passes_test


def context_data(request):
    context = {
        'page_name': '',
        'system_name': 'Membership Management System',
        'auther_name': 'Anjana Narasinghe',
        'project_start_date': '2023',
        'navbar_top': True,
        'footer': True
    }

    return context


def dashboard(request):

    current_year = datetime.now().year

    meeting_attendance_counts = (
        MemberAttendance.objects
        .filter(meeting_date__meeting_date__year=current_year)
        .values('meeting_date__meeting_date')
        .annotate(attendance_count=Count('attendance_id'))
        .order_by('meeting_date__meeting_date')
    )

    meeting_dates = [entry['meeting_date__meeting_date'].strftime('%Y-%m-%d') for entry in meeting_attendance_counts]
    attendance_counts = [entry['attendance_count'] for entry in meeting_attendance_counts]

    context = context_data(request)
    context['page_name'] = 'Dashboard'

    combine_date_attendance = zip(meeting_dates, attendance_counts)
    context['attendance_data'] = combine_date_attendance

    context['meeting_dates'] = meeting_dates
    context['attendance_counts'] = attendance_counts
    context['current_year'] = current_year

    all_members = Member.objects.all().count()
    context['all_members'] = all_members

    active_members = Member.objects.filter(member_is_active=True).count()
    context['active_members'] = active_members

    passive_members = Member.objects.filter(member_is_active=False).count()
    context['passive_members'] = passive_members

    all_staff = User.objects.all().count()
    context['all_staff'] = all_staff

    all_meeting = MeetingInfo.objects.all().count()
    context['all_meeting'] = all_meeting

    if all_members != 0:
        percentage_active = (active_members / all_members) * 100
        format_percentage_active = f'{percentage_active:.1f}'
        context['active_members_percentage'] = format_percentage_active

        percentage_passive = (passive_members / all_members) * 100
        format_percentage_passive = f'{percentage_passive:.1f}'
        context['passive_members_percentage'] = format_percentage_passive

    if MemberAttendance.objects.all():
        latest_meeting = MemberAttendance.objects.latest('meeting_date')
        latest_meeting_member_count = MemberAttendance.objects.filter(meeting_date=latest_meeting.meeting_date).values(
            'member_id').distinct().count()

        context['latest_meeting'] = latest_meeting
        context['latest_meeting_member_count'] = latest_meeting_member_count

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

    attendances = MemberAttendance.objects.filter(member_id=member_id)
    member = Member.objects.get(member_id=member_id)
    context['attendances'] = attendances
    context['member'] = member
    return render(request, 'report/member_attendance.html', context)


def member_qr_generator(request, member_id):
    member = Member.objects.get(member_id=member_id)

    profile_picture_directory = os.path.join(settings.MEDIA_ROOT, 'profiles', member_id)

    qr_code = qrcode.make(member_id)
    qr_code_name = f"{member_id}_qr.png"
    qr_code_path = os.path.join(profile_picture_directory, qr_code_name)

    os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)

    qr_code.save(qr_code_path)

    member.member_qr_code = os.path.relpath(qr_code_path, settings.MEDIA_ROOT)
    return redirect('member_view', member_id)
