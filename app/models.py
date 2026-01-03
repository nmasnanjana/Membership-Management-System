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


class ActivityLog(models.Model):
    """Track all user activities for audit and recent activity feed"""
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('VIEW', 'Viewed'),
        ('EXPORT', 'Exported'),
    ]
    
    activity_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    target_model = models.CharField(max_length=50)  # Member, Meeting, etc.
    target_id = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['target_model', 'target_id']),
        ]
    
    def __str__(self):
        return f"{self.user} {self.action_type} {self.target_model} at {self.created_at}"


class Payment(models.Model):
    """Track member payments separately from attendance"""
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('BANK', 'Bank Transfer'),
        ('CARD', 'Card'),
        ('OTHER', 'Other'),
    ]
    
    payment_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    meeting = models.ForeignKey(MeetingInfo, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    receipt_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['member', '-payment_date']),
            models.Index(fields=['-payment_date']),
            models.Index(fields=['meeting']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.member.member_id} - Rs.{self.amount}"


class BadgeType(models.TextChoices):
    """Achievement badge types"""
    # Attendance badges
    PERFECT_ATTENDANCE = 'PERFECT_ATTENDANCE', '🎯 Perfect Attendance'
    ATTENDANCE_STREAK_5 = 'ATTENDANCE_STREAK_5', '🔥 5 Meeting Streak'
    ATTENDANCE_STREAK_10 = 'ATTENDANCE_STREAK_10', '⚡ 10 Meeting Streak'
    EARLY_BIRD = 'EARLY_BIRD', '🌅 Early Bird'
    
    # Payment badges
    PAYMENT_CHAMPION = 'PAYMENT_CHAMPION', '💰 Payment Champion'
    ALWAYS_PAID = 'ALWAYS_PAID', '💳 Always Paid'
    
    # Membership badges
    FOUNDING_MEMBER = 'FOUNDING_MEMBER', '👑 Founding Member'
    VETERAN_MEMBER = 'VETERAN_MEMBER', '🏆 Veteran Member'
    ACTIVE_MEMBER = 'ACTIVE_MEMBER', '⭐ Active Member'
    
    # Leadership badges
    LEADER = 'LEADER', '👔 Leader'
    COMMITTEE = 'COMMITTEE', '🤝 Committee Member'


class MemberBadge(models.Model):
    """Track badges earned by members"""
    badge_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='badges')
    badge_type = models.CharField(max_length=30, choices=BadgeType.choices)
    earned_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = [['member', 'badge_type']]
        ordering = ['-earned_date']
        indexes = [
            models.Index(fields=['member', '-earned_date']),
        ]
    
    def __str__(self):
        return f"{self.member.member_id} - {self.get_badge_type_display()}"
