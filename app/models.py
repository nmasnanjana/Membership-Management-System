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


class MeetingInfo(models.Model):
    meeting_id = models.AutoField(primary_key=True)
    meeting_date = models.DateField()
    meeting_fee = models.IntegerField()

    def __str__(self):
        return str(f"{self.meeting_id} - {self.meeting_date}")


class MemberAttendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    meeting_date = models.ForeignKey(MeetingInfo, on_delete=models.CASCADE)
    member_id = models.ForeignKey(Member, on_delete=models.CASCADE)
    attendance_status = models.BooleanField(default=False)
    attendance_fee_status = models.BooleanField(default=False)
    attendance_created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.attendance_id)
