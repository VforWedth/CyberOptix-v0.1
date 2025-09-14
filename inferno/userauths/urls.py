from django.urls import path
from userauths import views
from django.contrib.auth.views import LogoutView

app_name = "userauths"

urlpatterns = [
    # Basic Authentication
    path("sign-up/", views.register_view, name="sign-up"),
    path("sign-in/", views.login_view, name="sign-in"),
    path("sign-out/", views.logout_view, name="sign-out"),
    
    # Email Verification
    path("verify-email/<str:token>/", views.verify_email_view, name="verify-email"),
    path("resend-verification/", views.resend_verification_view, name="resend-verification"),
    path("registration-complete/", views.registration_complete_view, name="registration-complete"),
    
    # Google OAuth
    path("google/login/", views.google_login_view, name="google-login"),
    path("google/callback/", views.google_callback_view, name="google-callback"),
    
    # Two-Factor Authentication
    path("2fa/setup/", views.two_factor_setup_view, name="two-factor-setup"),
    path("2fa/auth/", views.two_factor_auth_view, name="two-factor-auth"),
    path("2fa/disable/", views.disable_2fa_view, name="disable-2fa"),
    
    # User Profile
    path("profile/", views.profile_view, name="profile"),
    
    # API Endpoints
    path("api/check-email/", views.api_check_email_view, name="api-check-email"),
]
