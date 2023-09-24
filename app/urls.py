from django.urls import path
from .views_staff import *
from .views_member import *
from .views_meeting import *

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

]
