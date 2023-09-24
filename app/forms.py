from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import CharField
from django.contrib.auth.models import User
from .models import *


class StaffRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super(StaffRegisterForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')


class MemberRegisterForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ('member_id', 'member_initials', 'member_first_name', 'member_last_name', 'member_address',
                  'member_dob', 'member_tp_number', 'member_acc_number', 'member_guardian_name',
                  'member_profile_picture')

    member_id = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "4 Digit Member ID",
        "class": "form-control"}))

    member_initials = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "Initials",
        "class": "form-control"}))

    member_first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        "placeholder": "First Name",
        "class": "form-control"}))

    member_last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        "placeholder": "Last Name",
        "class": "form-control"}))

    member_address = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        "placeholder": "Address",
        "class": "form-control"}))

    member_dob = forms.DateField(widget=forms.DateInput(attrs={
        'type': 'date',
        "class": "form-control"}))

    member_tp_number = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "WhatsApp Number",
        "class": "form-control"}))

    member_acc_number = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "Account Number",
        "class": "form-control"}))

    member_guardian_name: CharField = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        "placeholder": "Guardian Name",
        "class": "form-control"}))

    member_profile_picture = forms.ImageField(widget=forms.FileInput(attrs={
        'type': 'file',
        "class": "form-control"}))


class MemberEditForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ('member_id', 'member_initials', 'member_first_name', 'member_last_name', 'member_address',
                  'member_dob', 'member_tp_number', 'member_acc_number', 'member_guardian_name',
                  'member_profile_picture')

    member_id = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "4 Digit Member ID",
        "class": "form-control", }))

    member_initials = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "Initials",
        "class": "form-control"}))

    member_first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        "placeholder": "First Name",
        "class": "form-control"}))

    member_last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        "placeholder": "Last Name",
        "class": "form-control"}))

    member_address = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        "placeholder": "Address",
        "class": "form-control"}))

    member_dob = forms.DateField(widget=forms.DateInput(attrs={
        'type': 'date',
        "class": "form-control"}))

    member_tp_number = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "WhatsApp Number",
        "class": "form-control"}))

    member_acc_number = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "Account Number",
        "class": "form-control"}))

    member_guardian_name = CharField = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        "placeholder": "Guardian Name",
        "class": "form-control"}))

    member_profile_picture = forms.ImageField(widget=forms.FileInput(attrs={
        'type': 'file',
        "class": "form-control"}))


class MeetingAddForm(forms.ModelForm):
    class Meta:
        model = MeetingInfo
        fields = ('meeting_date', 'meeting_fee')

    meeting_date = forms.DateField(widget=forms.DateInput(attrs={
        'type': 'date',
        "class": "form-control"}))

    meeting_fee = forms.IntegerField(widget=forms.TextInput(attrs={
        'type': 'number',
        "class": "form-control"}))

