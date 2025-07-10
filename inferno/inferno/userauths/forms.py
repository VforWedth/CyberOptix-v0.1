from django import forms 
from django.contrib.auth.forms import UserCreationForm
from userauths.models import User

class UserRegisterForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Username"}))
     
    class Meta:
        model = User
        fields = ['username','email']