#!/usr/bin/env python3
"""
Test Gmail SMTP Configuration
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Send a test email"""
    print("📧 Testing Gmail SMTP configuration...")
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"Email Host: {settings.EMAIL_HOST}")
    print(f"Email User: {settings.EMAIL_HOST_USER}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    
    try:
        send_mail(
            subject='EZM Trade Management - Email Test',
            message="""Hello!

This is a test email from EZM Trade Management system.

If you receive this email, the Gmail SMTP configuration is working correctly!

Test completed successfully.

Best regards,
EZM Trade Management System""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['ezeraben47@gmail.com'],
            fail_silently=False
        )
        print("✅ Test email sent successfully to ezeraben47@gmail.com")
        print("   Please check your inbox!")
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        print("\nCommon issues:")
        print("- App password not set or incorrect")
        print("- 2-Step verification not enabled on Gmail")
        print("- Network/firewall blocking SMTP")

if __name__ == "__main__":
    test_email()
