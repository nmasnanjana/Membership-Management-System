from django.urls import path
from app import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('user-register/', views.userRegister, name='user_registration'),
    path('login/', views.UserLogin.as_view(), name='login'),
    path('logout/', views.UserLogout.as_view(), name='logout'),
]
