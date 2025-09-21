# from django.db import models
# from django.contrib.auth.models import AbstractUser
# # Create your models here.

# class User(AbstractUser):
#     email = models.EmailField(unique=True, null=False)
#     username = models.CharField(max_length=100)
#     bio = models.CharField(max_length=100)
#     # title = models.CharField()
#     # decs = models.TextField()
    
#     USERNAME_FIELD = "email"
#     REQUIRED_FIELDS = ['username']
    
#     def __str__(self):
#         return self.username

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.mail import send_mail
import uuid
import secrets

class User(AbstractUser):
    email = models.EmailField(unique=True, null=False)
    username = models.CharField(max_length=100, unique=True)
    bio = models.CharField(max_length=100, blank=True)
    
    # Enhanced authentication fields
    is_shop_admin = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Google OAuth fields
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    google_access_token = models.TextField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True)
    google_token_expires = models.DateTimeField(blank=True, null=True)
    
    # Profile enhancement
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Security fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True)
    last_password_change = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)
    
    # Privacy settings
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    USERNAME_FIELD = "email"  # Use email for authentication instead of username
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
    
    def generate_email_verification_token(self):
        """Generate a secure token for email verification"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = timezone.now()
        self.save()
        return self.email_verification_token
    
    def is_email_verification_expired(self):
        """Check if email verification token has expired (24 hours)"""
        if not self.email_verification_sent_at:
            return True
        return timezone.now() > self.email_verification_sent_at + timezone.timedelta(hours=24)
    
    def verify_email(self, token):
        """Verify email with provided token"""
        if (self.email_verification_token == token and 
            not self.is_email_verification_expired()):
            self.is_email_verified = True
            self.email_verification_token = None
            self.email_verification_sent_at = None
            self.save()
            return True
        return False
    
    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration"""
        self.account_locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save()
    
    def reset_failed_attempts(self):
        """Reset failed login attempts counter"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save()
    
    def increment_failed_attempts(self):
        """Increment failed login attempts and lock account if necessary"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_account()
        self.save()

class EmailVerificationLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_logs')
    email = models.EmailField()
    token = models.CharField(max_length=100)
    sent_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']

class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    login_method = models.CharField(max_length=20, choices=[
        ('email', 'Email/Password'),
        ('google', 'Google OAuth'),
        ('2fa', 'Two Factor Auth')
    ], default='email')
    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-login_time']
