from django import forms
from app import models
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class AddUser(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

class MemberForm(forms.ModelForm):
    class Meta:
        model = models.Member
        fields = '__all__'
        widgets = {
            'talents': forms.CheckboxSelectMultiple,
        }