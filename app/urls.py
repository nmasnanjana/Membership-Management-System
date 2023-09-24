from django.urls import path
from .views_staff import *

urlpatterns = [

    path('staff/register/', staff_register, name='staff_register'),
    path('staff/list/', staff_list, name='staff_list'),
    path('staff/delete/<int:staff_id>', staff_delete, name='staff_delete'),
    path('staff/password/reset/<int:staff_id>', staff_password_reset, name='staff_password_reset'),
    path('staff/password/change/', staff_password_change, name='staff_password_change'),
    path('staff/profile/change/<int:staff_id>', staff_profile_edit, name='staff_profile_edit'),

]
