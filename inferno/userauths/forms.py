# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from userauths.models import User
from django.utils.translation import gettext_lazy as _
import re

class UserRegisterForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": _("Username"), 
            'class': 'input-field',
        }),
        help_text=_("Choose a unique username (3-30 characters)")
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "placeholder": _("Gmail Address"), 
            'class': 'input-field',
        }),
        help_text=_("Please use a valid Gmail address for verification")
    )
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            "placeholder": _("Password"), 
            'class': 'input-field',
        }),
        help_text=_("Password must be at least 8 characters long with letters and numbers")
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={
            "placeholder": _("Confirm Password"), 
            'class': 'input-field',
        })
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": _("Phone Number (Optional)"),
            'class': 'input-field',
        })
    )
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("I accept the Terms of Service and Privacy Policy")
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        
        # Check if email is Gmail
        if not email.endswith('@gmail.com'):
            raise ValidationError(_(
                "Only Gmail addresses are supported for registration. "
                "Please use a valid @gmail.com email address."
            ))
        
        # Additional Gmail validation
        gmail_pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
        if not re.match(gmail_pattern, email):
            raise ValidationError(_("Please enter a valid Gmail address."))
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("An account with this email already exists."))
        
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        
        # Username validation
        if len(username) < 3:
            raise ValidationError(_("Username must be at least 3 characters long."))
        
        if len(username) > 30:
            raise ValidationError(_("Username must not exceed 30 characters."))
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            raise ValidationError(_(
                "Username can only contain letters, numbers, dots, hyphens, and underscores."
            ))
        
        # Check if username already exists
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(_("This username is already taken."))
        
        return username

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if phone:
            # Basic phone validation
            phone_pattern = r'^\+?[\d\s\-\(\)]{10,20}$'
            if not re.match(phone_pattern, phone):
                raise ValidationError(_("Please enter a valid phone number."))
        return phone

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        # Enhanced password validation
        if len(password) < 8:
            raise ValidationError(_("Password must be at least 8 characters long."))
        
        if password.isdigit():
            raise ValidationError(_("Password cannot be entirely numeric."))
        
        if password.lower() in ['password', '12345678', 'qwerty123']:
            raise ValidationError(_("Password is too common."))
        
        # Check for at least one letter and one number
        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            raise ValidationError(_("Password must contain both letters and numbers."))
        
        return password

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "placeholder": _("Email Address"),
            'class': 'input-field',
            "autofocus": True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": _("Password"),
            'class': 'input-field',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_("Remember me")
    )
    
    def clean_email(self):
        return self.cleaned_data.get('email', '').lower().strip()

class EmailVerificationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "placeholder": _("Enter your email address"),
            'class': 'input-field',
        }),
        help_text=_("We'll send you a verification link")
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                raise ValidationError(_("This email is already verified."))
            return email
        except User.DoesNotExist:
            raise ValidationError(_("No account found with this email address."))

class TwoFactorSetupForm(forms.Form):
    token = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "placeholder": _("Enter 6-digit code"),
            'class': 'input-field text-center',
            "maxlength": "6",
            "pattern": "[0-9]{6}"
        }),
        help_text=_("Enter the 6-digit code from your authenticator app")
    )
    
    def clean_token(self):
        token = self.cleaned_data.get('token', '').strip()
        if not token.isdigit() or len(token) != 6:
            raise ValidationError(_("Please enter a valid 6-digit code."))
        return token

class TwoFactorForm(forms.Form):
    token = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "placeholder": "000000",
            'class': 'input-field text-center',
            "maxlength": "6",
            "pattern": "[0-9]{6}",
            "autofocus": True
        })
    )
    
    def clean_token(self):
        token = self.cleaned_data.get('token', '').strip()
        if not token.isdigit() or len(token) != 6:
            raise ValidationError(_("Please enter a valid 6-digit code."))
        return token