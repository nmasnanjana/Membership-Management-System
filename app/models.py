from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.
class Member(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    member_id = models.CharField(max_length=50, primary_key=True)
    full_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    birthday = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    bank_account_number = models.CharField(max_length=50)
    school = models.CharField(max_length=255)
    grade = models.CharField(max_length=50)
    talent_1 = models.CharField(max_length=255)
    talent_2 = models.CharField(max_length=255, blank=True, null=True)
    talent_3 = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=50)
    library_membership = models.CharField(max_length=255)
    parent_guardian_name = models.CharField(max_length=255)
    parent_guardian_bank_account_number = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='avatar/')

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        # Check for duplicate member ids
        if Member.objects.filter(member_id=self.member_id).exists():
            raise ValidationError('Member id already exists')
        super(Member, self).save(*args, **kwargs)
