#!/usr/bin/env python
"""
Test script to verify email configuration and functionality.
Run this after setting up your Gmail credentials in .env file.

Usage: python test_email.py your-test-email@gmail.com
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inferno.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings


def test_email_configuration():
    """Test basic email configuration"""
    print("=== Email Configuration Test ===")
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"Email Host: {settings.EMAIL_HOST}")
    print(f"Email Port: {settings.EMAIL_PORT}")
    print(f"Email TLS: {settings.EMAIL_USE_TLS}")
    print(f"Email Host User: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    print(f"Email Host Password: {'Set' if getattr(settings, 'EMAIL_HOST_PASSWORD', '') else 'Not set'}")
    print(f"Default From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print()


def send_test_email(recipient_email):
    """Send a test email"""
    print(f"=== Sending Test Email to {recipient_email} ===")
    
    try:
        # Simple text email
        send_mail(
            subject='CyberOptix Email Test',
            message='This is a test email from CyberOptix Django application.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        print("✅ Simple text email sent successfully!")
        
        # HTML email test
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2c3e50;">CyberOptix Email Test</h2>
            <p>This is a <strong>test HTML email</strong> from CyberOptix Django application.</p>
            <p>If you can see this formatted text, HTML emails are working correctly!</p>
            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                <p><strong>Email Configuration Test Results:</strong></p>
                <ul>
                    <li>✅ SMTP Connection: Success</li>
                    <li>✅ Authentication: Success</li>
                    <li>✅ HTML Rendering: Success</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        text_content = """
CyberOptix Email Test

This is a test HTML email from CyberOptix Django application.
If you received this email, your email configuration is working correctly!

Email Configuration Test Results:
✅ SMTP Connection: Success
✅ Authentication: Success
✅ Plain Text Fallback: Success
        """
        
        msg = EmailMultiAlternatives(
            subject='CyberOptix HTML Email Test',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        print("✅ HTML email sent successfully!")
        print("\nCheck your inbox (including spam folder) for both test emails.")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        print("\nPossible issues:")
        print("1. Gmail credentials not set in .env file")
        print("2. App password not generated (need 2FA enabled)")
        print("3. Firewall blocking SMTP connection")
        print("4. Incorrect email address format")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_email.py <recipient_email>")
        print("Example: python test_email.py test@gmail.com")
        sys.exit(1)
    
    recipient = sys.argv[1]
    
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, recipient):
        print("❌ Invalid email address format")
        sys.exit(1)
    
    test_email_configuration()
    
    if send_test_email(recipient):
        print("\n🎉 Email test completed successfully!")
        print("Your email configuration is working correctly.")
    else:
        print("\n💥 Email test failed!")
        print("Please check your configuration and try again.")


if __name__ == '__main__':
    main()