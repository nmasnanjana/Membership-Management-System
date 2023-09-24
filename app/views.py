from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from .forms import *
from .models import *
import os
import qrcode
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm, AdminPasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import datetime
from django.db.models import Count


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

