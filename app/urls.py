from django.urls import path
from .views_staff import *
from .views_member import *
from .views_meeting import *
from .views_attendance import *
from .views_attendance_bulk import *
from .views import *
from .views_db import database_management
from .views_calendar import calendar_view
from .views_payment import payment_list, payment_add, payment_edit, payment_delete, payment_statistics
from .views_reports import reports_builder, reports_quick_stats
from .views_heatmap import attendance_heatmap

urlpatterns = [

    path('staff/register/', staff_register, name='staff_register'),
    path('staff/list/', staff_list, name='staff_list'),
    path('staff/delete/<int:staff_id>', staff_delete, name='staff_delete'),
    path('staff/password/reset/<int:staff_id>', staff_password_reset, name='staff_password_reset'),
    path('staff/password/change/', staff_password_change, name='staff_password_change'),
    path('staff/profile/change/<int:staff_id>', staff_profile_edit, name='staff_profile_edit'),


    
    # Database Management
    path('database-management/', database_management, name='database_management'),

    path('member/list/', member_list, name='member_list'),
    path('member/list/adults/', member_list_adults, name='member_list_adults'),
    path('member/register/', member_register, name='member_register'),
    path('member/delete/<str:member_id>', member_delete, name="member_delete"),
    path('member/view/<str:member_id>', member_view, name="member_view"),
    path('member/edit/<str:member_id>', member_edit, name="member_edit"),
    path('member/bulk-action/', member_bulk_action, name='member_bulk_action'),
    path('member/inline-edit/', member_inline_edit, name='member_inline_edit'),

    path('meeting/list/', meeting_list, name='meeting_list'),
    path('meeting/delete/<meeting_date>', meeting_delete, name="meeting_delete"),
    path('meeting/add/', meeting_add, name='meeting_add'),
    path('meeting/edit/<meeting_date>', meeting_edit, name="meeting_edit"),

    path('attendance/mark/', attendance_mark, name='attendance_mark'),
    path('attendance/bulk/', attendance_bulk_mark, name='attendance_bulk_mark'),
    path('attendance/mark-all-present/<meeting_id>', attendance_mark_all_present, name='attendance_mark_all_present'),
    path('attendance/date/all', attendance_full_view, name='attendance_date_all'),
    path('attendance/date/<meeting_id>', attendance_date_view, name='attendance_date'),
    path('attendance/delete/<meeting_id>/<attendance_id>', attendance_delete, name='attendance_delete'),
    path('attendance/edit/<meeting_id>/<attendance_id>', attendance_edit, name='attendance_edit'),
    path('attendance/heatmap/', attendance_heatmap, name='attendance_heatmap'),

    path('login/', staff_log_in, name='login'),
    path('logout/', staff_log_out, name='logout'),
    path('', dashboard, name='dashboard'),
    path('member/report/attendance/<str:member_id>', member_attendance_report, name='member_attendance_report'),
    path('member/qr_code/generator/<str:member_id>', member_qr_generator, name='member_qr_generator'),

    path('export/member/', export_member_details, name='member_info_export'),
    path('export/member/attendance/<str:member_id>', export_member_attendance_report, name='member_attendance_export'),
    path('export/attendance/<meeting_id>', export_attendance_report, name='export_attendance_report'),

    path('qr_scan/', qr_scanner, name='qr_scann'),
    
    # Calendar View
    path('calendar/', calendar_view, name='calendar_view'),
    
    # Payment Tracking
    path('payment/list/', payment_list, name='payment_list'),
    path('payment/add/', payment_add, name='payment_add'),
    path('payment/edit/<int:payment_id>/', payment_edit, name='payment_edit'),
    path('payment/delete/<int:payment_id>/', payment_delete, name='payment_delete'),
    path('payment/statistics/', payment_statistics, name='payment_statistics'),
    
    # Custom Reports Builder
    path('reports/builder/', reports_builder, name='reports_builder'),
    path('reports/quick-stats/', reports_quick_stats, name='reports_quick_stats'),

]
