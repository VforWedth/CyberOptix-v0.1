import jwt
import requests
import secrets
import pyotp
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.contrib.auth import authenticate
from .models import User, EmailVerificationLog, LoginHistory
import logging

logger = logging.getLogger(__name__)

class AuthenticationService:
    """Enhanced authentication service with JWT, Google OAuth, and email verification"""
    
    @staticmethod
    def generate_jwt_token(user, token_type='access'):
        """Generate JWT token for user"""
        now = timezone.now()
        
        if token_type == 'access':
            expiry = now + timedelta(hours=24)
        elif token_type == 'refresh':
            expiry = now + timedelta(days=7)
        else:
            expiry = now + timedelta(hours=1)
        
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'token_type': token_type,
            'exp': expiry,
            'iat': now,
            'jti': secrets.token_hex(16)  # JWT ID for token blacklisting
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    @staticmethod
    def verify_jwt_token(token):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            return user, payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
            return None, None
    
    @staticmethod
    def authenticate_user(email, password, request=None):
        """Enhanced user authentication with security features"""
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return None, "Invalid email or password"
        
        # Check if account is locked
        if user.is_account_locked():
            return None, f"Account is locked until {user.account_locked_until.strftime('%Y-%m-%d %H:%M')}"
        
        # Authenticate user
        if user.check_password(password):
            # Reset failed attempts on successful login
            user.reset_failed_attempts()
            
            # Log successful login
            if request:
                AuthenticationService.log_login(
                    user, request, 'email', True
                )
            
            return user, None
        else:
            # Increment failed attempts
            user.increment_failed_attempts()
            
            # Log failed login
            if request:
                AuthenticationService.log_login(
                    user, request, 'email', False, 'Invalid password'
                )
            
            return None, "Invalid email or password"
    
    @staticmethod
    def log_login(user, request, method='email', success=True, failure_reason=''):
        """Log user login attempt"""
        ip_address = AuthenticationService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        LoginHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            login_method=method,
            success=success,
            failure_reason=failure_reason
        )
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class EmailService:
    """Email verification and notification service"""
    
    @staticmethod
    def is_valid_gmail(email):
        """Check if email is a valid Gmail address"""
        if not email.lower().endswith('@gmail.com'):
            return False
        
        # Additional validation using Google's Gmail API (optional)
        try:
            # This is a simplified check - in production you might want to use Gmail API
            import re
            gmail_pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
            return bool(re.match(gmail_pattern, email.lower()))
        except:
            return False
    
    @staticmethod
    def send_verification_email(user, request):
        """Send email verification link to user"""
        token = user.generate_email_verification_token()
        
        # Build verification URL
        verification_url = request.build_absolute_uri(
            f'/auth/verify-email/{token}/'
        )
        
        # Email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'LaptopMart Myanmar',
            'expiry_hours': 24
        }
        
        # Render email templates
        html_message = render_to_string('userauths/emails/verification_email.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=f'Verify your {context["site_name"]} account',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Log verification email
            EmailVerificationLog.objects.create(
                user=user,
                email=user.email,
                token=token,
                ip_address=AuthenticationService.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email after successful verification"""
        context = {
            'user': user,
            'site_name': 'LaptopMart Myanmar'
        }
        
        html_message = render_to_string('userauths/emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        try:
            send_mail(
                subject=f'Welcome to {context["site_name"]}!',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=True,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False

class GoogleOAuthService:
    """Google OAuth integration service"""
    
    GOOGLE_OAUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
    GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
    
    @staticmethod
    def get_google_oauth_url(request):
        """Generate Google OAuth authorization URL"""
        from django.urls import reverse
        
        # Build proper callback URL using Django's URL routing
        callback_path = reverse('userauths:google-callback')
        redirect_uri = request.build_absolute_uri(callback_path)
        
        params = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'state': secrets.token_urlsafe(32),
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        # Store state in session for security
        request.session['google_oauth_state'] = params['state']
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f'{GoogleOAuthService.GOOGLE_OAUTH_URL}?{query_string}'
    
    @staticmethod
    def exchange_code_for_tokens(code, request):
        """Exchange authorization code for access tokens"""
        from django.urls import reverse
        
        # Build proper callback URL using Django's URL routing
        callback_path = reverse('userauths:google-callback')
        redirect_uri = request.build_absolute_uri(callback_path)
        
        data = {
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
        }
        
        try:
            response = requests.post(GoogleOAuthService.GOOGLE_TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Google token exchange failed: {str(e)}")
            return None
    
    @staticmethod
    def get_user_info(access_token):
        """Get user info from Google API"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        try:
            response = requests.get(GoogleOAuthService.GOOGLE_USER_INFO_URL, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Google user info fetch failed: {str(e)}")
            return None
    
    @staticmethod
    def authenticate_with_google(code, state, request):
        """Complete Google OAuth authentication flow"""
        # Verify state parameter
        session_state = request.session.get('google_oauth_state')
        if not session_state or session_state != state:
            return None, "Invalid OAuth state parameter"
        
        # Exchange code for tokens
        tokens = GoogleOAuthService.exchange_code_for_tokens(code, request)
        if not tokens:
            return None, "Failed to exchange authorization code"
        
        # Get user info
        user_info = GoogleOAuthService.get_user_info(tokens['access_token'])
        if not user_info:
            return None, "Failed to get user information"
        
        # Check if email is Gmail
        if not EmailService.is_valid_gmail(user_info['email']):
            return None, "Only Gmail accounts are supported"
        
        # Find or create user
        try:
            user = User.objects.get(email=user_info['email'])
            # Update Google OAuth info
            user.google_id = user_info['id']
            user.google_access_token = tokens['access_token']
            if 'refresh_token' in tokens:
                user.google_refresh_token = tokens['refresh_token']
            user.google_token_expires = timezone.now() + timedelta(seconds=tokens['expires_in'])
            user.is_email_verified = True  # Gmail accounts are pre-verified
            user.save()
            
        except User.DoesNotExist:
            # Create new user
            username = user_info['email'].split('@')[0]
            # Ensure unique username
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User.objects.create(
                email=user_info['email'],
                username=username,
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
                google_id=user_info['id'],
                google_access_token=tokens['access_token'],
                google_refresh_token=tokens.get('refresh_token', ''),
                google_token_expires=timezone.now() + timedelta(seconds=tokens['expires_in']),
                is_email_verified=True,
                is_active=True
            )
            
            # Send welcome email
            EmailService.send_welcome_email(user)
        
        # Log successful login
        AuthenticationService.log_login(user, request, 'google', True)
        
        return user, None

class TwoFactorService:
    """Two-factor authentication service"""
    
    @staticmethod
    def generate_secret():
        """Generate TOTP secret for user"""
        return pyotp.random_base32()
    
    @staticmethod
    def get_qr_code_url(user, secret):
        """Generate QR code URL for TOTP setup"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user.email,
            issuer_name='LaptopMart Myanmar'
        )
    
    @staticmethod
    def verify_totp(secret, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def enable_2fa(user):
        """Enable 2FA for user"""
        if not user.two_factor_secret:
            user.two_factor_secret = TwoFactorService.generate_secret()
        user.two_factor_enabled = True
        user.save()
        return user.two_factor_secret
    
    @staticmethod
    def disable_2fa(user):
        """Disable 2FA for user"""
        user.two_factor_enabled = False
        user.two_factor_secret = ''
        user.save()