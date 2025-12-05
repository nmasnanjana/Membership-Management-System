from django.db import models
from django.core.exceptions import ValidationError
from .constants import UNIQUE_ROLES


class MemberRole(models.TextChoices):
    """Club roles for members (display purposes only)"""
    # Main 3 roles (only one person each)
    PRESIDENT = 'PRESIDENT', 'President'
    SECRETARY = 'SECRETARY', 'Secretary'
    TREASURY = 'TREASURY', 'Treasury'
    
    # Sub 3 roles (only one person each)
    VICE_PRESIDENT = 'VICE_PRESIDENT', 'Vice President'
    VICE_SECRETARY = 'VICE_SECRETARY', 'Vice Secretary'
    VICE_TREASURY = 'VICE_TREASURY', 'Vice Treasury'
    
    # Other role (can be multiple)
    COMMITTEE_MEMBER = 'COMMITTEE_MEMBER', 'Committee Member'
    
    # No role (default)
    NONE = '', 'No Role'


class Member(models.Model):
    member_id = models.CharField(max_length=10, primary_key=True, null=False, unique=True)
    member_initials = models.CharField(max_length=10, null=False)
    member_first_name = models.CharField(max_length=50, null=False)
    member_last_name = models.CharField(max_length=50, null=False)
    member_address = models.CharField(max_length=255, null=False)
    member_dob = models.DateField()
    member_tp_number = models.CharField(max_length=10, null=False)
    member_acc_number = models.CharField(max_length=10)
    member_guardian_name = models.CharField(max_length=100, null=False)
    member_profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    member_qr_code = models.ImageField(upload_to='profiles/', blank=True)
    member_is_active = models.BooleanField(default=True)
    member_role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
        default=MemberRole.NONE,
        blank=True,
        help_text='Club role assigned to member (for display purposes only)'
    )
    member_join_at = models.DateField(auto_now_add=True)
    member_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['member_is_active']),
            models.Index(fields=['member_join_at']),
            models.Index(fields=['member_tp_number']),
            models.Index(fields=['member_role']),
        ]

    def clean(self):
        """Validate that unique roles (main 3 and sub 3) are not assigned to multiple members"""
        if self.member_role and self.member_role in UNIQUE_ROLES:
            # Check if another member already has this role
            existing_member = Member.objects.filter(
                member_role=self.member_role,
                member_is_active=True
            ).exclude(member_id=self.member_id).first()
            
            if existing_member:
                raise ValidationError({
                    'member_role': f'This role is already assigned to {existing_member.member_initials} {existing_member.member_first_name} {existing_member.member_last_name}. Only one member can have this role.'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Run validation
        super().save(*args, **kwargs)

    def __str__(self):
        return self.member_id


class MeetingInfo(models.Model):
    meeting_id = models.AutoField(primary_key=True)
    meeting_date = models.DateField()
    meeting_fee = models.IntegerField()
    meeting_created_at = models.DateTimeField(auto_now_add=True)
    meeting_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['meeting_date']),
        ]
        ordering = ['-meeting_date']

    def __str__(self):
        return str(f"{self.meeting_id} - {self.meeting_date}")


class MemberAttendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    meeting_date = models.ForeignKey(MeetingInfo, on_delete=models.CASCADE)
    member_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    attendance_status = models.BooleanField(default=False)
    attendance_fee_status = models.BooleanField(default=False)
    attendance_created_at = models.DateTimeField(auto_now_add=True)
    attendance_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['meeting_date', 'member_id']]
        indexes = [
            models.Index(fields=['meeting_date', 'member_id']),
            models.Index(fields=['member_id', 'attendance_status']),
            models.Index(fields=['attendance_status', 'attendance_fee_status']),
        ]
        ordering = ['-attendance_created_at']

    def __str__(self):
        return str(self.attendance_id)
    
    def clean(self):
        """Model validation - members can pay fees even if absent"""
        # No validation needed - members can pay fees regardless of attendance status
        pass
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Run validation
        super().save(*args, **kwargs)
