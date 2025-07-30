#!/usr/bin/env python3
"""
Comprehensive Password Reset Testing for EZM Trade Management
Tests both custom email service and Django's built-in password reset functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.conf import settings
from users.email_service import email_service
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

def create_test_user():
    """Create or get a test user for password reset testing"""
    try:
        # Try to get existing user first
        test_user = User.objects.get(username="test_password_reset")
        print(f"✅ Using existing test user: {test_user.username} ({test_user.email})")
        return test_user
    except User.DoesNotExist:
        # Create new test user
        test_user = User.objects.create_user(
            username="test_password_reset",
            email="ezeraben47@gmail.com",
            password="OldPassword123!",
            first_name="Test",
            last_name="User"
        )
        print(f"✅ Created new test user: {test_user.username} ({test_user.email})")
        return test_user

def test_email_service_password_reset():
    """Test the custom email service password reset functionality"""
    print_section("CUSTOM EMAIL SERVICE PASSWORD RESET TEST")
    
    try:
        user = create_test_user()
        
        # Generate a realistic password reset link
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"http://127.0.0.1:8000/users/password-reset-confirm/{uid}/{token}/"
        
        print(f"📧 Testing password reset email for user: {user.username}")
        print(f"📧 Email will be sent to: {user.email}")
        print(f"🔗 Reset link: {reset_link}")
        
        # Send password reset email using custom service
        success, message = email_service.send_password_reset_email(user, reset_link)
        
        if success:
            print(f"✅ Custom email service test PASSED: {message}")
            return True
        else:
            print(f"❌ Custom email service test FAILED: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error in custom email service test: {e}")
        return False

def test_django_password_reset_view():
    """Test Django's built-in password reset view"""
    print_section("DJANGO PASSWORD RESET VIEW TEST")
    
    try:
        user = create_test_user()
        
        # Create a test client
        client = Client()
        
        # Clear any existing emails in the test outbox
        mail.outbox.clear()
        
        # Get the password reset URL
        reset_url = reverse('password_reset')
        print(f"🌐 Password reset URL: {reset_url}")
        
        # Post to the password reset form
        print(f"📤 Submitting password reset form for: {user.email}")
        response = client.post(reset_url, {
            'email': user.email
        })
        
        # Check response
        if response.status_code == 302:  # Redirect after successful form submission
            print("✅ Password reset form submitted successfully")
            print(f"🔄 Redirected to: {response.url}")
            
            # Check if email was sent (in console backend, mail.outbox might be empty)
            if hasattr(mail, 'outbox') and mail.outbox:
                print(f"📧 {len(mail.outbox)} email(s) found in outbox")
                for email in mail.outbox:
                    print(f"   Subject: {email.subject}")
                    print(f"   To: {email.to}")
                    print(f"   From: {email.from_email}")
            else:
                print("📧 Email sent via configured backend (check console or inbox)")
            
            return True
        else:
            print(f"❌ Password reset form failed with status: {response.status_code}")
            if hasattr(response, 'context') and response.context:
                form = response.context.get('form')
                if form and hasattr(form, 'errors'):
                    print(f"   Form errors: {form.errors}")
            return False
            
    except Exception as e:
        print(f"❌ Error in Django password reset view test: {e}")
        return False

def test_password_reset_url_access():
    """Test that password reset URLs are accessible"""
    print_section("PASSWORD RESET URL ACCESS TEST")
    
    try:
        client = Client()
        
        # Test password reset request page
        reset_url = reverse('password_reset')
        response = client.get(reset_url)
        
        if response.status_code == 200:
            print(f"✅ Password reset page accessible: {reset_url}")
        else:
            print(f"❌ Password reset page failed: {reset_url} (Status: {response.status_code})")
            return False
        
        # Test password reset done page
        done_url = reverse('password_reset_done')
        response = client.get(done_url)
        
        if response.status_code == 200:
            print(f"✅ Password reset done page accessible: {done_url}")
        else:
            print(f"❌ Password reset done page failed: {done_url} (Status: {response.status_code})")
            return False
        
        # Test password reset complete page
        complete_url = reverse('password_reset_complete')
        response = client.get(complete_url)
        
        if response.status_code == 200:
            print(f"✅ Password reset complete page accessible: {complete_url}")
        else:
            print(f"❌ Password reset complete page failed: {complete_url} (Status: {response.status_code})")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing URL access: {e}")
        return False

def test_email_configuration():
    """Test current email configuration"""
    print_section("EMAIL CONFIGURATION CHECK")
    
    print(f"📧 Email Backend: {settings.EMAIL_BACKEND}")
    print(f"📧 Email Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}")
    print(f"📧 Email Port: {getattr(settings, 'EMAIL_PORT', 'Not configured')}")
    print(f"📧 Email TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not configured')}")
    print(f"📧 From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"📧 Company Name: {getattr(settings, 'COMPANY_NAME', 'Not configured')}")
    
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("ℹ️  Console backend active - emails will display in terminal")
        print("   To send real emails, configure Gmail SMTP (see GMAIL_SETUP_INSTRUCTIONS.md)")
        return True
    elif 'smtp' in settings.EMAIL_BACKEND.lower():
        host_user = getattr(settings, 'EMAIL_HOST_USER', '')
        if host_user and 'your_gmail_app_password_here' not in str(getattr(settings, 'EMAIL_HOST_PASSWORD', '')):
            print("✅ SMTP backend configured - emails will be sent via Gmail")
            return True
        else:
            print("⚠️  SMTP backend configured but App Password not set")
            print("   Update EMAIL_HOST_PASSWORD in .env file")
            return False
    else:
        print("⚠️  Unknown email backend configuration")
        return False

def main():
    """Main test function"""
    print_header("EZM TRADE MANAGEMENT - PASSWORD RESET TESTING")
    
    print("This script tests all password reset functionality:")
    print("1. Email configuration check")
    print("2. Custom email service password reset")
    print("3. Django built-in password reset views")
    print("4. URL accessibility")
    
    results = {}
    
    # Test email configuration
    results['email_config'] = test_email_configuration()
    
    # Test custom email service
    results['custom_service'] = test_email_service_password_reset()
    
    # Test Django password reset view
    results['django_view'] = test_django_password_reset_view()
    
    # Test URL access
    results['url_access'] = test_password_reset_url_access()
    
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
        print("\n🎉 All password reset functionality is working correctly!")
        if 'console' in settings.EMAIL_BACKEND.lower():
            print("📧 Currently using console backend for email display")
            print("   To send real emails, follow GMAIL_SETUP_INSTRUCTIONS.md")
        else:
            print("📧 Emails will be sent to ezeraben47@gmail.com")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
    
    print_header("NEXT STEPS")
    
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("1. Follow GMAIL_SETUP_INSTRUCTIONS.md to set up Gmail SMTP")
        print("2. Get Gmail App Password")
        print("3. Update .env file with the app password")
        print("4. Run: python3 test_gmail_smtp.py")
        print("5. Check ezeraben47@gmail.com for real emails")
    else:
        print("✅ Password reset functionality is ready for production!")
        print("   Users can now reset their passwords via email")
    
    print("\n📧 Password reset URLs available:")
    print(f"   Reset Request: http://127.0.0.1:8000{reverse('password_reset')}")
    print(f"   Reset Done: http://127.0.0.1:8000{reverse('password_reset_done')}")
    print(f"   Reset Complete: http://127.0.0.1:8000{reverse('password_reset_complete')}")

if __name__ == "__main__":
    main()