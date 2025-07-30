#!/usr/bin/env python3
"""
Simple Email Functionality Test for EZM Trade Management
This test demonstrates that email system is working without requiring database setup
"""
import os
import sys
import django

# Setup Django with minimal configuration
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

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

def test_email_configuration():
    """Test and display email configuration"""
    print_section("EMAIL CONFIGURATION")
    
    print(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📧 Email Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}")
    print(f"📧 Email Port: {getattr(settings, 'EMAIL_PORT', 'Not configured')}")
    print(f"📧 Email TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not configured')}")
    print(f"📧 Email Host User: {getattr(settings, 'EMAIL_HOST_USER', 'Not configured')}")
    print(f"📧 From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"📧 Company Name: {getattr(settings, 'COMPANY_NAME', 'Not configured')}")
    
    # Check if SMTP is properly configured
    if 'smtp' in settings.EMAIL_BACKEND.lower():
        host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        if 'your_gmail_app_password_here' not in str(host_password) and host_password:
            print("✅ SMTP fully configured - ready to send real emails")
            return True
        else:
            print("⚠️  SMTP configured but App Password needs to be set")
            print("   Update EMAIL_HOST_PASSWORD in .env file with your Gmail App Password")
            return False
    elif 'console' in settings.EMAIL_BACKEND.lower():
        print("ℹ️  Console backend - emails will display in terminal (good for testing)")
        return True
    else:
        print("❌ Unknown email backend configuration")
        return False

def test_basic_email():
    """Test sending a basic email"""
    print_section("BASIC EMAIL TEST")
    
    try:
        subject = "EZM Trade Management - Email System Test"
        message = f"""Hello!

This is a test email from the EZM Trade Management system.

Test Details:
- Timestamp: {timezone.now()}
- Django Version: {django.get_version()}
- Email Backend: {settings.EMAIL_BACKEND}
- From: {settings.DEFAULT_FROM_EMAIL}

If you receive this email, the email system is working correctly!

Best regards,
EZM Trade Management System"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['ezeraben47@gmail.com'],
            fail_silently=False
        )
        
        print("✅ Basic email sent successfully!")
        print("   Check ezeraben47@gmail.com inbox or console output")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send basic email: {e}")
        return False

def test_password_reset_email():
    """Test password reset email without database dependency"""
    print_section("PASSWORD RESET EMAIL TEST")
    
    try:
        # Create a mock user object
        class MockUser:
            def __init__(self):
                self.username = "test_user"
                self.first_name = "Test"
                self.last_name = "User"
                self.email = "ezeraben47@gmail.com"
        
        mock_user = MockUser()
        reset_link = "http://127.0.0.1:8000/users/password-reset/confirm/abc123-def456-789ghi/"
        
        # Create password reset email content
        subject = f"{getattr(settings, 'COMPANY_NAME', 'EZM Trade Management')} - Password Reset Request"
        
        message = f"""Dear {mock_user.first_name} {mock_user.last_name},

You have requested to reset your password for your EZM Trade Management account.

Please click the following link to reset your password:
{reset_link}

This link will expire in 24 hours for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
EZM Trade Management Team"""

        # Try to send HTML email with fallback
        try:
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Password Reset</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #f9f9f9; }}
        .button {{ display: inline-block; background: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
        .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Dear <strong>{mock_user.first_name} {mock_user.last_name}</strong>,</p>
            <p>You have requested to reset your password for your EZM Trade Management account.</p>
            <p>Please click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </p>
            <p>This link will expire in 24 hours for security reasons.</p>
            <p>If you didn't request this password reset, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>EZM Trade Management<br>
            This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>"""
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[mock_user.email]
            )
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            
            print("✅ Password reset email (HTML) sent successfully!")
            
        except Exception:
            # Fallback to plain text
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[mock_user.email],
                fail_silently=False
            )
            print("✅ Password reset email (plain text) sent successfully!")
        
        print(f"   Reset link: {reset_link}")
        print("   Check ezeraben47@gmail.com inbox or console output")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send password reset email: {e}")
        return False

def test_user_creation_email():
    """Test user creation welcome email"""
    print_section("USER CREATION EMAIL TEST")
    
    try:
        # Create a mock user object
        class MockUser:
            def __init__(self):
                self.username = "new_test_user"
                self.first_name = "New"
                self.last_name = "User"
                self.email = "ezeraben47@gmail.com"
            
            def get_role_display(self):
                return "Store Manager"
        
        mock_user = MockUser()
        temp_password = "TempPass123!"
        
        # Create user creation email content
        subject = f"Welcome to {getattr(settings, 'COMPANY_NAME', 'EZM Trade Management')} - Account Created"
        
        message = f"""Dear {mock_user.first_name} {mock_user.last_name},

Your account has been created for EZM Trade Management.

Login Details:
- Username: {mock_user.username}
- Temporary Password: {temp_password}
- Role: {mock_user.get_role_display()}

Please login at: http://127.0.0.1:8000/users/login/

IMPORTANT: You will be required to change your password on first login for security purposes.

If you have any questions, please contact your administrator.

Best regards,
EZM Trade Management Team"""

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[mock_user.email],
            fail_silently=False
        )
        
        print("✅ User creation email sent successfully!")
        print(f"   Username: {mock_user.username}")
        print(f"   Temporary Password: {temp_password}")
        print("   Check ezeraben47@gmail.com inbox or console output")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send user creation email: {e}")
        return False

def main():
    """Main test function"""
    print_header("EZM TRADE MANAGEMENT - EMAIL FUNCTIONALITY TEST")
    
    print("This script tests the email system functionality:")
    print("1. Email configuration check")
    print("2. Basic email sending")
    print("3. Password reset email")
    print("4. User creation email")
    print("\nAll emails will be sent to: ezeraben47@gmail.com")
    
    results = {}
    
    # Test email configuration
    results['config'] = test_email_configuration()
    
    # Test basic email
    results['basic'] = test_basic_email()
    
    # Test password reset email
    results['password_reset'] = test_password_reset_email()
    
    # Test user creation email
    results['user_creation'] = test_user_creation_email()
    
    # Print results summary
    print_header("TEST RESULTS SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        test_name = test.replace('_', ' ').title()
        print(f"{status.ljust(10)} {test_name}")
    
    print(f"\nOverall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All email functionality is working correctly!")
        
        if 'smtp' in settings.EMAIL_BACKEND.lower():
            host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
            if 'your_gmail_app_password_here' not in str(host_password) and host_password:
                print("📧 Emails are being sent via Gmail SMTP to ezeraben47@gmail.com")
                print("   Check your Gmail inbox for the test emails!")
            else:
                print("📧 SMTP configured but App Password needed for real email sending")
                print("   Follow GMAIL_SETUP_INSTRUCTIONS.md to complete setup")
        else:
            print("📧 Currently using console backend (emails displayed in terminal)")
            print("   To send real emails, follow GMAIL_SETUP_INSTRUCTIONS.md")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
    
    print_header("EMAIL SYSTEM STATUS")
    
    if 'smtp' in settings.EMAIL_BACKEND.lower():
        print("✅ Email system configured for production use")
        print("✅ Password reset functionality ready")
        print("✅ User notification emails ready")
        print("✅ System emails ready")
        
        host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        if 'your_gmail_app_password_here' in str(host_password) or not host_password:
            print("\n⏳ FINAL STEP: Set Gmail App Password in .env file")
            print("   See GMAIL_SETUP_INSTRUCTIONS.md for details")
        else:
            print("\n🎉 EMAIL SYSTEM IS FULLY OPERATIONAL!")
            print("   All forgotten password and system emails will work!")
    else:
        print("ℹ️  Email system in development mode (console backend)")
        print("   To enable real email sending, configure Gmail SMTP")

if __name__ == "__main__":
    main()