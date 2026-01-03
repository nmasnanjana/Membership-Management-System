from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import CharField
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget.attrs.pop('help_text', None)
        if not self.instance.is_superuser:
            del self.fields['is_superuser']

    is_superuser = forms.BooleanField(label='Is Superuser', required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'is_superuser')


class MemberRegisterForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ('member_id', 'member_initials', 'member_first_name', 'member_last_name', 'member_address',
                  'member_dob', 'member_tp_number', 'member_acc_number', 'member_guardian_name',
                  'member_profile_picture')

    member_id = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "placeholder": "4 Digit Member ID",
            "class": "form-control"
        }),
        validators=[RegexValidator(
            regex=r'^\d{4,10}$',
            message='Member ID must be 4-10 digits.'
        )]
    )

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

    member_tp_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "placeholder": "WhatsApp Number (10 digits)",
            "class": "form-control"
        }),
        validators=[RegexValidator(
            regex=r'^\d{10}$',
            message='Phone number must be exactly 10 digits.'
        )]
    )

    member_acc_number = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "Account Number",
        "class": "form-control"}))

    member_guardian_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        "placeholder": "Guardian Name",
        "class": "form-control"}))

    member_profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'type': 'file',
            "class": "form-control"
        })
    )


class MemberEditForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ('member_id', 'member_initials', 'member_first_name', 'member_last_name', 'member_address',
                  'member_dob', 'member_tp_number', 'member_acc_number', 'member_guardian_name',
                  'member_profile_picture', 'member_is_active', 'member_role')
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show role and status fields to superusers
        if not self.user or not self.user.is_superuser:
            if 'member_role' in self.fields:
                del self.fields['member_role']
            if 'member_is_active' in self.fields:
                del self.fields['member_is_active']
        else:
            # For superusers, show role field with proper choices
            from .models import MemberRole
            self.fields['member_role'] = forms.ChoiceField(
                choices=[('', 'No Role')] + [(role.value, role.label) for role in MemberRole if role != MemberRole.NONE],
                required=False,
                widget=forms.Select(attrs={"class": "form-select"}),
                label="Club Role",
                help_text="Assign a club role to this member (only one person can have main/sub roles)"
            )
            
            # For superusers, show active status field
            self.fields['member_is_active'] = forms.BooleanField(
                required=False,
                widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
                label="Member Status",
                help_text="Check to mark member as active, uncheck to mark as inactive"
            )

    member_id = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "placeholder": "4 Digit Member ID",
            "class": "form-control",
            "readonly": "readonly",  # Visual indication
        }),
        disabled=True,  # Prevent value change in backend
        validators=[RegexValidator(
            regex=r'^\d{4,10}$',
            message='Member ID must be 4-10 digits.'
        )]
    )

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

    member_tp_number = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "placeholder": "WhatsApp Number (10 digits)",
            "class": "form-control"
        }),
        validators=[RegexValidator(
            regex=r'^\d{10}$',
            message='Phone number must be exactly 10 digits.'
        )]
    )

    member_acc_number = forms.CharField(max_length=10, widget=forms.TextInput(attrs={
        "placeholder": "Account Number",
        "class": "form-control"}))

    member_guardian_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        "placeholder": "Guardian Name",
        "class": "form-control"}))

    member_profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'type': 'file',
            "class": "form-control"
        })
    )


class MeetingAddForm(forms.ModelForm):
    class Meta:
        model = MeetingInfo
        fields = ('meeting_date', 'meeting_fee')

    meeting_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            "class": "form-control"
        })
    )
    
    def clean_meeting_date(self):
        meeting_date = self.cleaned_data.get('meeting_date')
        if meeting_date:
            from datetime import date
            # Prevent creating meetings in the future (optional - can be removed if needed)
            # if meeting_date > date.today():
            #     raise forms.ValidationError("Meeting date cannot be in the future.")
        return meeting_date

    meeting_fee = forms.IntegerField(widget=forms.TextInput(attrs={
        'type': 'number',
        "class": "form-control"}))


class AttendanceMarkForm(forms.ModelForm):
    class Meta:
        model = MemberAttendance
        fields = ('meeting_date', 'member_id', 'attendance_status', 'attendance_fee_status')

    meeting_date = forms.ModelChoiceField(
        queryset=MeetingInfo.objects.all().order_by('-meeting_date'),  # Newest first
        empty_label=None,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Date"
    )

    member_id = forms.ModelChoiceField(
        queryset=Member.objects.filter(member_is_active=True).order_by('member_id'),  # Only active members
        empty_label='Select Member',
        widget=forms.Select(attrs={"class": "form-select", 'id': 'member_select'}),
        label="Member ID"
    )

    attendance_status = forms.ChoiceField(choices=[(True, "Present"), (False, "Absent")],
                                          widget=forms.RadioSelect(attrs={'class': "form-check-label"}),
                                          initial=False,
                                          label="Attendance")

    attendance_fee_status = forms.ChoiceField(choices=[(True, "Payed"), (False, "Not Payed")],
                                              widget=forms.RadioSelect(attrs={'class': "form-check-label"}),
                                              initial=False,
                                              label="Member Fee")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member_id'].label_from_instance = self.member_id_label_from_instance
        self.fields['meeting_date'].label_from_instance = self.date_label_from_instance

    def member_id_label_from_instance(self, obj):
        return f"{obj.member_id} - {obj.member_initials} {obj.member_first_name} {obj.member_last_name}"

    def date_label_from_instance(self, obj):
        return f"{obj.meeting_date}"
    
    def clean(self):
        cleaned_data = super().clean()
        # Members can pay fees even if absent - no validation needed
        return cleaned_data


class AttendanceEditForm(forms.ModelForm):
    attendance_status = forms.ChoiceField(
        choices=[(True, "Present"), (False, "Absent")],
        widget=forms.RadioSelect(attrs={'class': "form-check-label"}),
        initial=False,
        label="Attendance"
    )

    attendance_fee_status = forms.ChoiceField(
        choices=[(True, "Payed"), (False, "Not Payed")],
        widget=forms.RadioSelect(attrs={'class': "form-check-label"}),
        initial=False,
        label="Member Fee"
    )

    class Meta:
        model = MemberAttendance
        fields = ('attendance_status', 'attendance_fee_status')
    
    def clean(self):
        cleaned_data = super().clean()
        # Members can pay fees even if absent - no validation needed
        return cleaned_data


class QRScann(forms.Form):

    member_id = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter or scan Member ID",
            "autocomplete": "off"
        }),
        label="Member ID",
        help_text="Scan QR code or enter member ID manually"
    )
    
    def clean_member_id(self):
        member_id = self.cleaned_data.get('member_id')
        if member_id:
            # Strip whitespace
            member_id = member_id.strip()
            
            # Validate member exists
            from .models import Member
            if not Member.objects.filter(member_id=member_id).exists():
                raise forms.ValidationError(f'Member with ID "{member_id}" does not exist.')
        
        return member_id

