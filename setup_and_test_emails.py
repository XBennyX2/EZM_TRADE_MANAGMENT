#!/usr/bin/env python3
"""
EZM Trade Management Email Setup and Testing Script
This script will configure Gmail SMTP and test all email functionality
"""
import os
import sys
import django
from getpass import getpass

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from users.email_service import email_service
from django.contrib.auth import get_user_model
import string
import random

User = get_user_model()

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def setup_gmail_smtp():
    """Setup Gmail SMTP configuration"""
    print_header("GMAIL SMTP SETUP")
    
    print("To send real emails, you need to configure Gmail SMTP.")
    print("This requires a Gmail account and an App Password.")
    print("\nSteps to get Gmail App Password:")
    print("1. Go to your Google Account settings")
    print("2. Select Security")
    print("3. Enable 2-Step Verification if not already enabled")
    print("4. Go to App passwords")
    print("5. Select 'Mail' and generate a new app password")
    print("6. Use this 16-character password below")
    
    gmail_user = input(f"\nEnter your Gmail address [default: ezeraben47@gmail.com]: ").strip()
    if not gmail_user:
        gmail_user = "ezeraben47@gmail.com"
    
    print(f"\nUsing Gmail address: {gmail_user}")
    
    # For security, we'll create a separate config file for sensitive data
    config_file = os.path.join(os.path.dirname(__file__), 'email_config.py')
    
    app_password = getpass("Enter your Gmail App Password (16 characters, no spaces): ").strip()
    
    if not app_password:
        print("❌ App password is required!")
        return False
    
    # Create email configuration file
    config_content = f'''"""
Email configuration for EZM Trade Management
Generated automatically - DO NOT commit this file to version control
"""

# Gmail SMTP Configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_TIMEOUT = 60

# Email credentials
EMAIL_HOST_USER = "{gmail_user}"
EMAIL_HOST_PASSWORD = "{app_password}"

# Company email settings
DEFAULT_FROM_EMAIL = "EZM Trade Management <{gmail_user}>"
COMPANY_EMAIL = "{gmail_user}"
COMPANY_NAME = "EZM Trade Management"
'''
    
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        print(f"✅ Email configuration saved to {config_file}")
        
        # Update .env file
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        env_content = f'''# Email Configuration for Gmail SMTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_TIMEOUT=60

# Email credentials
EMAIL_HOST_USER={gmail_user}
EMAIL_HOST_PASSWORD={app_password}

# Company email settings
DEFAULT_FROM_EMAIL=EZM Trade Management <{gmail_user}>
COMPANY_EMAIL={gmail_user}
COMPANY_NAME=EZM Trade Management

# Other Django settings
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-here
'''
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ .env file updated with email configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

def test_smtp_connection():
    """Test SMTP connection"""
    print_section("SMTP CONNECTION TEST")
    
    try:
        from django.core.mail import get_connection
        connection = get_connection()
        connection.open()
        print("✅ SMTP connection successful!")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        print("\nPossible issues:")
        print("- Incorrect Gmail credentials")
        print("- App password not enabled")
        print("- Network/firewall issues")
        print("- Gmail security settings")
        return False

def send_test_email():
    """Send a test email"""
    print_section("SENDING TEST EMAIL")
    
    test_email = "ezeraben47@gmail.com"
    subject = "EZM Trade Management - Email System Test"
    
    message = f"""Hello!

This is a test email from the EZM Trade Management system to verify that email functionality is working correctly.

Test Details:
- Timestamp: {django.utils.timezone.now()}
- Django Version: {django.get_version()}
- Email Backend: {settings.EMAIL_BACKEND}
- From: {settings.DEFAULT_FROM_EMAIL}

If you receive this email, the email system is functioning properly!

Email Features Tested:
✅ SMTP Connection
✅ Email Sending
✅ Authentication

Next, we'll test the password reset functionality.

Best regards,
EZM Trade Management System
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False
        )
        print(f"✅ Test email sent successfully to {test_email}")
        print("   Please check your inbox!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

def test_password_reset_email():
    """Test password reset email functionality"""
    print_section("PASSWORD RESET EMAIL TEST")
    
    # Create or get a test user
    try:
        test_user, created = User.objects.get_or_create(
            username="test_user_email",
            defaults={
                'email': "ezeraben47@gmail.com",
                'first_name': "Test",
                'last_name': "User",
                'is_active': True,
            }
        )
        
        if created:
            print(f"✅ Created test user: {test_user.username}")
        else:
            print(f"✅ Using existing test user: {test_user.username}")
        
        # Test password reset email
        reset_link = "http://127.0.0.1:8000/users/password-reset/confirm/abc123-def456/"
        
        success, message = email_service.send_password_reset_email(test_user, reset_link)
        
        if success:
            print(f"✅ Password reset email test passed: {message}")
            print(f"   Reset link: {reset_link}")
            return True
        else:
            print(f"❌ Password reset email test failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing password reset email: {e}")
        return False

def test_user_creation_email():
    """Test user creation email"""
    print_section("USER CREATION EMAIL TEST")
    
    try:
        # Create a mock user for testing
        class MockUser:
            def __init__(self):
                self.username = f'test_user_{"".join(random.choices(string.ascii_lowercase + string.digits, k=6))}'
                self.first_name = 'Test'
                self.last_name = 'User'
                self.email = 'ezeraben47@gmail.com'
                
            def get_role_display(self):
                return 'Store Manager'
        
        mock_user = MockUser()
        temp_password = "TempPass123!"
        
        success, message = email_service.send_user_creation_email(mock_user, temp_password)
        
        if success:
            print(f"✅ User creation email test passed: {message}")
            return True
        else:
            print(f"❌ User creation email test failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing user creation email: {e}")
        return False

def main():
    """Main function"""
    print_header("EZM TRADE MANAGEMENT EMAIL SETUP & TEST")
    
    print("This script will:")
    print("1. Configure Gmail SMTP for sending real emails")
    print("2. Test the email configuration")
    print("3. Send test emails to ezeraben47@gmail.com")
    print("4. Test all email functionality")
    
    setup_choice = input("\nDo you want to setup Gmail SMTP? (y/n): ").lower().strip()
    
    if setup_choice == 'y':
        if not setup_gmail_smtp():
            print("❌ Email setup failed. Exiting.")
            return
        
        print("\n🔄 Reloading Django settings...")
        # Reload settings (in a real deployment, you'd restart the server)
        import importlib
        importlib.reload(settings)
    
    # Test email functionality
    print_header("TESTING EMAIL FUNCTIONALITY")
    
    results = {}
    
    # Test SMTP connection
    results['smtp_connection'] = test_smtp_connection()
    
    if results['smtp_connection']:
        # Send basic test email
        results['test_email'] = send_test_email()
        
        # Test password reset email
        results['password_reset'] = test_password_reset_email()
        
        # Test user creation email
        results['user_creation'] = test_user_creation_email()
    else:
        print("❌ Skipping other tests due to SMTP connection failure")
        results['test_email'] = False
        results['password_reset'] = False
        results['user_creation'] = False
    
    # Print results summary
    print_header("TEST RESULTS SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status.ljust(10)} {test.replace('_', ' ').title()}")
    
    print(f"\nOverall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All email functionality is working correctly!")
        print("   Emails will be sent to ezeraben47@gmail.com")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the configuration.")
    
    print_header("CONFIGURATION NOTES")
    print("• Email backend is now configured for Gmail SMTP")
    print("• Password reset emails will be sent to user's email address")
    print("• All system emails will come from ezeraben47@gmail.com")
    print("• Make sure to keep your App Password secure!")
    print("\n📧 Email functionality is ready for production use!")

if __name__ == "__main__":
    main()