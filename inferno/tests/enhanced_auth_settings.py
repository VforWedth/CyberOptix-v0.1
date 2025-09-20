# Enhanced Authentication Settings Configuration
# Add these settings to your Django settings.py file

# ================================
# ENHANCED AUTHENTICATION SETTINGS
# ================================

import os
from decouple import config

# Email Configuration for Gmail Verification
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='your-email@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='your-app-password')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='LaptopMart Myanmar <noreply@laptopmart.com.mm>')

# Google OAuth2 Configuration
GOOGLE_OAUTH_CLIENT_ID = config('GOOGLE_OAUTH_CLIENT_ID', default='')
GOOGLE_OAUTH_CLIENT_SECRET = config('GOOGLE_OAUTH_CLIENT_SECRET', default='')

# JWT Configuration
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ACCESS_TOKEN_LIFETIME = 24 * 60 * 60  # 24 hours in seconds
JWT_REFRESH_TOKEN_LIFETIME = 7 * 24 * 60 * 60  # 7 days in seconds

# Security Settings
SESSION_COOKIE_SECURE = True if not DEBUG else False
CSRF_COOKIE_SECURE = True if not DEBUG else False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Enhanced User Model
AUTH_USER_MODEL = 'userauths.User'

# Login/Logout URLs
LOGIN_URL = '/auth/sign-in/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/sign-in/'

# Password Validation (Enhanced)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# File Upload Settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Maximum file upload size (10MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Cache Configuration (for rate limiting and sessions)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'auth.log'),
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'userauths': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# ================================
# ENVIRONMENT VARIABLES (.env file)
# ================================
"""
Create a .env file in your project root with these variables:

# Email Settings
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# Google OAuth2 Settings
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret

# JWT Settings (optional - uses Django's SECRET_KEY by default)
JWT_SECRET_KEY=your-super-secret-jwt-key

# Other Settings
DEFAULT_FROM_EMAIL=LaptopMart Myanmar <noreply@laptopmart.com.mm>
"""

# ================================
# GOOGLE OAUTH2 SETUP INSTRUCTIONS
# ================================
"""
1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable Google+ API and Gmail API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client IDs
5. Set Application Type to "Web application"
6. Add Authorized redirect URIs:
   - http://localhost:8000/auth/google/callback/ (for development)
   - https://yourdomain.com/auth/google/callback/ (for production)
7. Copy Client ID and Client Secret to your .env file
"""

# ================================
# GMAIL APP PASSWORD SETUP
# ================================
"""
1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account Settings → Security → App passwords
3. Generate an app password for "Mail"
4. Use this app password (not your Gmail password) in EMAIL_HOST_PASSWORD
"""

# ================================
# REQUIRED DJANGO APPS
# ================================
"""
Add these to your INSTALLED_APPS:

INSTALLED_APPS = [
    ...
    'userauths',
    'django.contrib.sessions',
    'django.contrib.messages',
    ...
]
"""

# ================================
# MIDDLEWARE CONFIGURATION
# ================================
"""
Ensure these middleware are in your MIDDLEWARE setting:

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
"""