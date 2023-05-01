from django.urls import path
from app import views

def addleadingzeros(value):
    return str(value).zfill(4)

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('user-register/', views.userRegister, name='user_registration'),
    path('login/', views.UserLogin.as_view(), name='login'),
    path('logout/', views.UserLogout.as_view(), name='logout'),
    path('member-register/', views.member_register, name='member_registration'),
    path('member-list', views.member_list, name='member_list'),
    path('member-list/<int:pk>/', views.member_detail, name='member_detail'),
    path('member-list/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('member-list/<int:pk>/delete/', views.member_delete, name='member_delete'),
]
