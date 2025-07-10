# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from userauths.models import User

class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "Username", 
            'class': 'input-field',
        }),
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "placeholder": "Email", 
            'class': 'input-field',
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password", 
            'class': 'input-field',
        }),
        help_text="Your password must contain at least 8 characters."
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm Password", 
            'class': 'input-field',
        }),
        help_text="Enter the same password as before, for verification."
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username