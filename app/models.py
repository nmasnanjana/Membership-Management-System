from django.db import models


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
    member_join_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.member_id
