from django.urls import path
from .views_staff import *
from .views_member import *
from .views_meeting import *
from .views_attendance import *
from .views import *

urlpatterns = [

    path('staff/register/', staff_register, name='staff_register'),
    path('staff/list/', staff_list, name='staff_list'),
    path('staff/delete/<int:staff_id>', staff_delete, name='staff_delete'),
    path('staff/password/reset/<int:staff_id>', staff_password_reset, name='staff_password_reset'),
    path('staff/password/change/', staff_password_change, name='staff_password_change'),
    path('staff/profile/change/<int:staff_id>', staff_profile_edit, name='staff_profile_edit'),

    path('member/list/', member_list, name='member_list'),
    path('member/register/', member_register, name='member_register'),
    path('member/delete/<str:member_id>', member_delete, name="member_delete"),
    path('member/view/<str:member_id>', member_view, name="member_view"),
    path('member/edit/<str:member_id>', member_edit, name="member_edit"),

    path('meeting/list/', meeting_list, name='meeting_list'),
    path('meeting/delete/<meeting_date>', meeting_delete, name="meeting_delete"),
    path('meeting/add/', meeting_add, name='meeting_add'),
    path('meeting/edit/<meeting_date>', meeting_edit, name="meeting_edit"),

    path('attendance/mark/', attendance_mark, name='attendance_mark'),
    path('attendance/date/all', attendance_full_view, name='attendance_date_all'),
    path('attendance/date/<meeting_id>', attendance_date_view, name='attendance_date'),
    path('attendance/delete/<meeting_id>/<attendance_id>', attendance_delete, name='attendance_delete'),
    path('attendance/edit/<meeting_id>/<attendance_id>', attendance_edit, name='attendance_edit'),

    path('login/', staff_log_in, name='login'),
    path('logout/', staff_log_out, name='logout'),
    path('', dashboard, name='dashboard'),
    path('member/report/attendance/<str:member_id>', member_attendance_report, name='member_attendance_report'),
    path('member/qr_code/generator/<str:member_id>', member_qr_generator, name='member_qr_generator'),

    path('export/member/', export_member_details, name='member_info_export'),
    path('export/member/attendance/<str:member_id>', export_member_attendance_report, name='member_attendance_export'),
    path('export/attendance/<meeting_id>', export_attendance_report, name='export_attendance_report'),

    path('qr_scan/', qr_scanner, name='qr_scann'),

]
