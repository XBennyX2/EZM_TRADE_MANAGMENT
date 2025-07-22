#!/usr/bin/env python
"""
Test different email configurations for EZM Trade Management
"""
import os
import sys
import django

def test_configuration(config_name, env_vars):
    """Test a specific email configuration"""
    print(f"\n{'='*60}")
    print(f"TESTING: {config_name}")
    print(f"{'='*60}")
    
    # Set environment variables
    for key, value in env_vars.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    
    # Reload Django settings
    from django.conf import settings
    if hasattr(settings, '_wrapped'):
        settings._wrapped = None
    
    # Setup Django again
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    
    from django.conf import settings
    from users.email_service import EZMEmailService
    
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"Email Host: {settings.EMAIL_HOST}")
    print(f"Email Port: {settings.EMAIL_PORT}")
    print(f"Email User: {settings.EMAIL_HOST_USER}")
    print(f"Email TLS: {settings.EMAIL_USE_TLS}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"SendGrid Key: {'Set' if getattr(settings, 'SENDGRID_API_KEY', None) else 'Not set'}")
    
    # Test email service
    try:
        email_service = EZMEmailService()
        print(f"Using SendGrid API: {email_service.use_sendgrid_api}")
        
        # Test sending email
        success, message = email_service.send_email(
            to_email="test@example.com",
            subject="Test Email Configuration",
            plain_content="Testing email configuration changes.",
            html_content="<p>Testing <strong>email configuration</strong> changes.</p>"
        )
        
        if success:
            print(f"✓ Email test successful: {message}")
        else:
            print(f"✗ Email test failed: {message}")
            
    except Exception as e:
        print(f"✗ Email service error: {e}")

def main():
    """Test different email configurations"""
    print("Testing Email Configuration Changes")
    print("This shows what happens when you modify .env settings")
    
    # Configuration 1: Console Backend (Current)
    test_configuration("Console Backend (Current Working)", {
        'FORCE_CONSOLE_EMAIL': 'True',
        'SENDGRID_API_KEY': None,
        'EMAIL_HOST': 'smtp.gmail.com',
        'EMAIL_HOST_USER': 'ezmtradeandinvestmentservice@gmail.com',
        'EMAIL_HOST_PASSWORD': 'existing-password',
        'DEFAULT_FROM_EMAIL': 'EZM Trade and Investment <ezmtradeandinvestmentservice@gmail.com>'
    })
    
    # Configuration 2: Gmail SMTP (if you have valid credentials)
    test_configuration("Gmail SMTP Configuration", {
        'FORCE_CONSOLE_EMAIL': None,
        'SENDGRID_API_KEY': None,
        'EMAIL_HOST': 'smtp.gmail.com',
        'EMAIL_HOST_USER': 'your-email@gmail.com',
        'EMAIL_HOST_PASSWORD': 'your-app-password',
        'DEFAULT_FROM_EMAIL': 'your-email@gmail.com'
    })
    
    # Configuration 3: SendGrid (if you have valid API key)
    test_configuration("SendGrid Configuration", {
        'FORCE_CONSOLE_EMAIL': None,
        'SENDGRID_API_KEY': 'SG.valid-api-key-here',
        'EMAIL_HOST': None,
        'EMAIL_HOST_USER': None,
        'EMAIL_HOST_PASSWORD': None,
        'DEFAULT_FROM_EMAIL': 'noreply@yourdomain.com'
    })
    
    # Configuration 4: Invalid Configuration
    test_configuration("Invalid Configuration (Fallback to Console)", {
        'FORCE_CONSOLE_EMAIL': None,
        'SENDGRID_API_KEY': None,
        'EMAIL_HOST': None,
        'EMAIL_HOST_USER': None,
        'EMAIL_HOST_PASSWORD': None,
        'DEFAULT_FROM_EMAIL': 'noreply@example.com'
    })
    
    print(f"\n{'='*60}")
    print("CONFIGURATION CHANGE GUIDE")
    print(f"{'='*60}")
    print("""
To change your email configuration:

1. EDIT YOUR .env FILE:
   - Open .env in your editor
   - Modify the email settings
   - Save the file

2. RESTART DJANGO SERVER:
   - Stop: Ctrl+C
   - Start: python manage.py runserver

3. TEST THE CHANGES:
   - Create a new user (admin panel)
   - Reset a user account
   - Check console output or email delivery

EXAMPLE .env CONFIGURATIONS:

# For Development (Console)
FORCE_CONSOLE_EMAIL=True

# For Gmail Production
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# For SendGrid Production
SENDGRID_API_KEY=SG.your-real-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
""")

if __name__ == '__main__':
    main()
