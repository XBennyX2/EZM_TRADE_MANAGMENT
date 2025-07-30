#!/usr/bin/env python3
"""
Simple Email Configuration Script for EZM Trade Management
This script configures Gmail SMTP for real email sending
"""
import os

def setup_gmail_smtp_config():
    """Configure Gmail SMTP in .env file"""
    print("🔧 Configuring Gmail SMTP for EZM Trade Management")
    
    # Update .env file with Gmail SMTP configuration
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    # You would need to replace 'your_gmail_app_password_here' with an actual App Password
    env_content = '''# Email Configuration for Gmail SMTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_TIMEOUT=60

# Email credentials - REPLACE with real App Password
EMAIL_HOST_USER=ezeraben47@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password_here

# Company email settings
DEFAULT_FROM_EMAIL=EZM Trade Management <ezeraben47@gmail.com>
COMPANY_EMAIL=ezeraben47@gmail.com
COMPANY_NAME=EZM Trade Management

# Other Django settings
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-here
'''
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ .env file updated with Gmail SMTP configuration")
        print(f"📝 Configuration saved to: {env_file}")
        
        print("\n⚠️  IMPORTANT: To send real emails, you need to:")
        print("1. Get a Gmail App Password:")
        print("   - Go to Google Account Settings")
        print("   - Security → 2-Step Verification (enable if not already)")
        print("   - App passwords → Mail → Generate")
        print("2. Replace 'your_gmail_app_password_here' in .env with the actual 16-character password")
        print("3. Restart Django server to load new settings")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def create_email_test_script():
    """Create a simple email test script"""
    test_script = os.path.join(os.path.dirname(__file__), 'test_gmail_smtp.py')
    
    script_content = '''#!/usr/bin/env python3
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
        print("\\nCommon issues:")
        print("- App password not set or incorrect")
        print("- 2-Step verification not enabled on Gmail")
        print("- Network/firewall blocking SMTP")

if __name__ == "__main__":
    test_email()
'''
    
    try:
        with open(test_script, 'w') as f:
            f.write(script_content)
        print(f"✅ Email test script created: {test_script}")
        return True
    except Exception as e:
        print(f"❌ Error creating test script: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("  EZM TRADE MANAGEMENT EMAIL CONFIGURATION")
    print("=" * 60)
    
    print("This script will configure Gmail SMTP for real email sending.")
    
    if setup_gmail_smtp_config():
        create_email_test_script()
        
        print("\n" + "=" * 60)
        print("  CONFIGURATION COMPLETE")
        print("=" * 60)
        
        print("✅ Gmail SMTP configuration is ready!")
        print("\nNext steps:")
        print("1. Get your Gmail App Password")
        print("2. Edit .env file and replace 'your_gmail_app_password_here'")
        print("3. Run: python3 test_gmail_smtp.py")
        print("4. Check ezeraben47@gmail.com for test email")
        
        print("\n📧 Once configured, all system emails will be sent via Gmail!")
    else:
        print("❌ Configuration failed!")

if __name__ == "__main__":
    main()