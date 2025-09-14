from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from userauths.forms import UserRegisterForm, LoginForm, EmailVerificationForm, TwoFactorForm, TwoFactorSetupForm
from userauths.models import User
from .services import AuthenticationService, EmailService, GoogleOAuthService, TwoFactorService
import json
import qrcode
from io import BytesIO
import base64

def register_view(request):
    if request.user.is_authenticated:
        messages.info(request, _("You are already logged in."))
        return redirect("flame:home")
    
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Create user but don't activate until email verification
            user = form.save(commit=False)
            user.is_active = False  # Activate only after email verification
            user.phone_number = form.cleaned_data.get('phone_number', '')
            user.save()
            
            # Send verification email
            if EmailService.send_verification_email(user, request):
                messages.success(request, _(
                    f"Welcome {user.username}! Please check your Gmail inbox "
                    f"for a verification link to complete your registration."
                ))
                return redirect('userauths:registration-complete')
            else:
                messages.error(request, _("Failed to send verification email. Please try again."))
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = UserRegisterForm()

    context = {'form': form}
    return render(request, "userauths/sign-up.html", context)

def login_view(request):
    if request.user.is_authenticated:
        messages.info(request, _("You are already logged in."))
        return redirect("flame:home")
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user, error_message = AuthenticationService.authenticate_user(email, password, request)
            
            if user:
                # Check if email is verified
                if not user.is_email_verified:
                    messages.error(request, _(
                        "Please verify your email address before logging in. "
                        "Check your Gmail inbox for the verification link."
                    ))
                    return render(request, "userauths/sign-in.html", {'form': form})
                
                # Check for 2FA
                if user.two_factor_enabled:
                    # Store user ID in session for 2FA
                    request.session['pending_2fa_user_id'] = user.id
                    return redirect('userauths:two-factor-auth')
                
                # Complete login
                login(request, user)
                
                # Set session timeout
                if not remember_me:
                    request.session.set_expiry(0)  # Browser session
                else:
                    request.session.set_expiry(604800)  # 1 week
                
                messages.success(request, _(f"Welcome back, {user.username}!"))
                next_url = request.GET.get('next', 'flame:home')
                return redirect(next_url)
            else:
                messages.error(request, error_message)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = LoginForm()
    
    return render(request, "userauths/sign-in.html", {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        request.session.flush()
        messages.success(request, _(f"Goodbye {username}! You have been logged out successfully."))
    else: 
        messages.warning(request, _("No user is currently logged in."))
    return redirect("userauths:sign-in")

def verify_email_view(request, token):
    try:
        # Find user by token
        user = User.objects.get(email_verification_token=token)
        
        if user.verify_email(token):
            # Activate user account
            user.is_active = True
            user.save()
            
            # Send welcome email
            EmailService.send_welcome_email(user)
            
            messages.success(request, _(
                "Email verified successfully! Your account is now active. You can log in now."
            ))
            return redirect('userauths:sign-in')
        else:
            messages.error(request, _(
                "Invalid or expired verification link. Please request a new one."
            ))
            return redirect('userauths:resend-verification')
            
    except User.DoesNotExist:
        messages.error(request, _("Invalid verification link."))
        return redirect('userauths:sign-in')

def resend_verification_view(request):
    if request.method == "POST":
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            user = User.objects.get(email=email)
            
            if EmailService.send_verification_email(user, request):
                messages.success(request, _(
                    "Verification email sent! Please check your Gmail inbox."
                ))
            else:
                messages.error(request, _("Failed to send verification email. Please try again."))
            
            return redirect('userauths:resend-verification')
    else:
        form = EmailVerificationForm()
    
    return render(request, "userauths/resend-verification.html", {'form': form})

def registration_complete_view(request):
    return render(request, "userauths/registration-complete.html")

# Google OAuth Views
def google_login_view(request):
    oauth_url = GoogleOAuthService.get_google_oauth_url(request)
    return redirect(oauth_url)

def google_callback_view(request):
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    
    if error:
        messages.error(request, _("Google authentication was cancelled or failed."))
        return redirect('userauths:sign-in')
    
    if not code or not state:
        messages.error(request, _("Invalid Google authentication response."))
        return redirect('userauths:sign-in')
    
    user, error_message = GoogleOAuthService.authenticate_with_google(code, state, request)
    
    if user:
        # Check for 2FA
        if user.two_factor_enabled:
            request.session['pending_2fa_user_id'] = user.id
            return redirect('userauths:two-factor-auth')
        
        login(request, user)
        messages.success(request, _(f"Welcome, {user.username}! Logged in with Google."))
        return redirect('flame:home')
    else:
        messages.error(request, error_message)
        return redirect('userauths:sign-in')

# Two-Factor Authentication Views
def two_factor_setup_view(request):
    if not request.user.is_authenticated:
        return redirect('userauths:sign-in')
    
    if request.method == "POST":
        form = TwoFactorSetupForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data.get('token')
            
            if TwoFactorService.verify_totp(request.user.two_factor_secret, token):
                request.user.two_factor_enabled = True
                request.user.save()
                messages.success(request, _("Two-factor authentication enabled successfully!"))
                return redirect('userauths:profile')
            else:
                messages.error(request, _("Invalid verification code. Please try again."))
    else:
        # Generate secret and QR code
        if not request.user.two_factor_secret:
            secret = TwoFactorService.generate_secret()
            request.user.two_factor_secret = secret
            request.user.save()
        else:
            secret = request.user.two_factor_secret
        
        qr_code_url = TwoFactorService.get_qr_code_url(request.user, secret)
        
        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_image = base64.b64encode(buffer.getvalue()).decode()
        
        form = TwoFactorSetupForm()
        context = {
            'form': form,
            'secret': secret,
            'qr_code_image': qr_code_image
        }
        
    return render(request, "userauths/two-factor-setup.html", context)

def two_factor_auth_view(request):
    user_id = request.session.get('pending_2fa_user_id')
    if not user_id:
        return redirect('userauths:sign-in')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('userauths:sign-in')
    
    if request.method == "POST":
        form = TwoFactorForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data.get('token')
            
            if TwoFactorService.verify_totp(user.two_factor_secret, token):
                # Complete login
                login(request, user)
                del request.session['pending_2fa_user_id']
                
                # Log 2FA login
                AuthenticationService.log_login(user, request, '2fa', True)
                
                messages.success(request, _(f"Welcome back, {user.username}!"))
                return redirect('flame:home')
            else:
                messages.error(request, _("Invalid verification code. Please try again."))
    else:
        form = TwoFactorForm()
    
    context = {
        'form': form,
        'user_email': user.email
    }
    return render(request, "userauths/two-factor-auth.html", context)

@login_required
def disable_2fa_view(request):
    if request.method == "POST":
        TwoFactorService.disable_2fa(request.user)
        messages.success(request, _("Two-factor authentication has been disabled."))
    return redirect('userauths:profile')

@login_required
def profile_view(request):
    context = {
        'user': request.user,
        'recent_logins': request.user.login_history.all()[:5]
    }
    return render(request, "userauths/profile.html", context)

# API Views for AJAX requests
@require_http_methods(["POST"])
@csrf_exempt
def api_check_email_view(request):
    """API endpoint to check if email is valid Gmail"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').lower().strip()
        
        is_valid = EmailService.is_valid_gmail(email)
        exists = User.objects.filter(email=email).exists()
        
        return JsonResponse({
            'valid': is_valid,
            'exists': exists,
            'message': 'Valid Gmail address' if is_valid else 'Please use a Gmail address'
        })
    except:
        return JsonResponse({'valid': False, 'exists': False, 'message': 'Invalid request'})
