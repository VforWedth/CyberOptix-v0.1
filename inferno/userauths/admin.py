from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from userauths.models import User, EmailVerificationLog, LoginHistory

class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'email', 'email_verified_status', 
        'google_auth_status', 'two_factor_status', 'account_status',
        'login_count', 'last_login'
    ]
    list_filter = [
        'is_email_verified', 'two_factor_enabled', 'is_active', 
        'is_staff', 'is_superuser', 'date_joined', 'google_id'
    ]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    readonly_fields = [
        'date_joined', 'last_login', 'google_id', 'failed_login_attempts',
        'account_locked_until', 'email_verification_sent_at', 'last_password_change',
        'email_verification_token', 'two_factor_secret', 'google_access_token',
        'google_refresh_token', 'google_token_expires'
    ]
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Enhanced Profile', {
            'fields': (
                'bio', 'phone_number', 'date_of_birth', 'profile_picture'
            )
        }),
        ('Email Verification', {
            'fields': (
                'is_email_verified', 'email_verification_token', 
                'email_verification_sent_at'
            )
        }),
        ('Google OAuth', {
            'fields': (
                'google_id', 'google_access_token', 'google_refresh_token',
                'google_token_expires'
            )
        }),
        ('Security', {
            'fields': (
                'two_factor_enabled', 'two_factor_secret', 
                'failed_login_attempts', 'account_locked_until',
                'last_password_change'
            )
        }),
        ('Preferences', {
            'fields': (
                'email_notifications', 'marketing_emails'
            )
        }),
        ('Shop Admin', {
            'fields': ('is_shop_admin',)
        })
    )
    
    def login_count(self, obj):
        try:
            return obj.login_history.filter(success=True).count()
        except:
            return 0
    login_count.short_description = 'Login Count'
    
    def email_verified_status(self, obj):
        if obj.is_email_verified:
            return format_html('<span style="color: green; font-weight: bold;">✓ Verified</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Not Verified</span>')
    email_verified_status.short_description = 'Email Status'
    
    def google_auth_status(self, obj):
        if obj.google_id:
            return format_html('<span style="color: blue; font-weight: bold;">🔗 Connected</span>')
        return format_html('<span style="color: gray;">Not Connected</span>')
    google_auth_status.short_description = 'Google Auth'
    
    def two_factor_status(self, obj):
        if obj.two_factor_enabled:
            return format_html('<span style="color: green; font-weight: bold;">🔒 Enabled</span>')
        return format_html('<span style="color: orange;">Disabled</span>')
    two_factor_status.short_description = '2FA Status'
    
    def account_status(self, obj):
        from django.utils import timezone
        if obj.account_locked_until and obj.account_locked_until > timezone.now():
            return format_html('<span style="color: red; font-weight: bold;">🔒 Locked</span>')
        elif obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: gray;">Inactive</span>')
    account_status.short_description = 'Status'
    
    actions = ['verify_email', 'enable_two_factor', 'unlock_accounts', 'send_verification_email']
    
    def verify_email(self, request, queryset):
        updated = queryset.update(is_email_verified=True)
        self.message_user(request, f'{updated} users had their email verified.')
    verify_email.short_description = "Mark selected users as email verified"
    
    def enable_two_factor(self, request, queryset):
        updated = queryset.update(two_factor_enabled=True)
        self.message_user(request, f'{updated} users had 2FA enabled.')
    enable_two_factor.short_description = "Enable 2FA for selected users"
    
    def unlock_accounts(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            account_locked_until=None, 
            failed_login_attempts=0
        )
        self.message_user(request, f'{updated} accounts were unlocked.')
    unlock_accounts.short_description = "Unlock selected accounts"
    
    def send_verification_email(self, request, queryset):
        from userauths.services import EmailService
        count = 0
        for user in queryset.filter(is_email_verified=False):
            if EmailService.send_verification_email(user, request):
                count += 1
        self.message_user(request, f'Verification emails sent to {count} users.')
    send_verification_email.short_description = "Send verification email to selected users"

@admin.register(EmailVerificationLog)
class EmailVerificationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'sent_at', 'verified_at', 'ip_address']
    list_filter = ['sent_at', 'verified_at']
    search_fields = ['user__username', 'user__email', 'email']
    readonly_fields = ['sent_at', 'verified_at', 'token']
    date_hierarchy = 'sent_at'
    
    def has_add_permission(self, request):
        return False

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'login_time', 'login_method', 'success', 
        'ip_address', 'failure_reason'
    ]
    list_filter = ['login_method', 'success', 'login_time']
    search_fields = ['user__username', 'user__email', 'ip_address']
    readonly_fields = ['login_time']
    date_hierarchy = 'login_time'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

admin.site.site_header = "LaptopMart Myanmar Admin"
admin.site.site_title = "LaptopMart Admin"
admin.site.index_title = "Enhanced Authentication System"

admin.site.register(User, UserAdmin)
