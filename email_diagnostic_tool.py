#!/usr/bin/env python
"""
Email Diagnostic Tool for EZM Trade Management System

This tool helps diagnose and fix email functionality issues by:
1. Testing network connectivity
2. Checking email configuration
3. Testing email sending functionality
4. Providing solutions for common issues
"""

import os
import sys
import django
import socket
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from users.email_service import EZMEmailService

def test_network_connectivity():
    """Test basic network connectivity"""
    print("🔍 Testing Network Connectivity...")
    
    # Test DNS resolution
    try:
        import socket
        host = getattr(settings, 'EMAIL_HOST', 'smtp.gmail.com')
        ip = socket.gethostbyname(host)
        print(f"✅ DNS Resolution: {host} -> {ip}")
    except Exception as e:
        print(f"❌ DNS Resolution failed: {e}")
        return False
    
    # Test SMTP port connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        port = getattr(settings, 'EMAIL_PORT', 465)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ SMTP Port {port} is accessible")
            return True
        else:
            print(f"❌ SMTP Port {port} is not accessible")
            return False
    except Exception as e:
        print(f"❌ Network connectivity test failed: {e}")
        return False

def check_email_configuration():
    """Check email configuration settings"""
    print("\n🔍 Checking Email Configuration...")
    
    config = {
        'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', 'Not set'),
        'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'Not set'),
        'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'Not set'),
        'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'Not set'),
        'EMAIL_HOST_PASSWORD': 'Set' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'Not set',
        'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', False),
        'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', False),
        'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set'),
    }
    
    issues = []
    
    for key, value in config.items():
        if value == 'Not set':
            print(f"❌ {key}: {value}")
            issues.append(f"{key} is not configured")
        else:
            print(f"✅ {key}: {value}")
    
    return len(issues) == 0, issues

def test_email_service():
    """Test the email service functionality"""
    print("\n🔍 Testing Email Service...")
    
    try:
        email_service = EZMEmailService()
        
        # Test network connectivity
        network_ok = email_service.test_network_connectivity()
        if network_ok:
            print("✅ Network connectivity test passed")
        else:
            print("❌ Network connectivity test failed")
        
        # Get backend status
        status = email_service.get_email_backend_status()
        print(f"📊 Email Backend Status:")
        for key, value in status.items():
            if key == 'network_accessible':
                status_icon = "✅" if value else "❌"
                print(f"   {status_icon} {key}: {value}")
            else:
                print(f"   📋 {key}: {value}")
        
        # Test email configuration
        success, message = email_service.test_email_configuration()
        if success:
            print(f"✅ Email configuration test: {message}")
        else:
            print(f"❌ Email configuration test: {message}")
        
        return success
        
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        return False

def provide_solutions():
    """Provide solutions for common email issues"""
    print("\n🔧 Common Email Issues and Solutions:")
    
    print("\n1. Network Connectivity Issues:")
    print("   • Check your internet connection")
    print("   • Verify firewall settings (allow outbound SMTP)")
    print("   • Try using a different network")
    print("   • Check if your ISP blocks SMTP ports")
    
    print("\n2. Gmail SMTP Issues:")
    print("   • Enable 2-factor authentication on your Gmail account")
    print("   • Generate an App Password (not your regular password)")
    print("   • Use port 465 with SSL (not TLS)")
    print("   • Update your .env file with correct credentials")
    
    print("\n3. Configuration Issues:")
    print("   • Check your .env file for correct email settings")
    print("   • Ensure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set")
    print("   • Verify EMAIL_USE_SSL=True and EMAIL_USE_TLS=False for Gmail")
    
    print("\n4. Development vs Production:")
    print("   • For development: Use console backend (emails shown in terminal)")
    print("   • For production: Use SMTP backend with proper credentials")
    print("   • Consider using SendGrid or other email services for production")

def create_fallback_config():
    """Create a fallback configuration for development"""
    print("\n🔧 Creating Fallback Configuration...")
    
    # Check if .env file exists
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file exists")
        
        # Read current .env content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check if console backend is already configured
        if 'EMAIL_BACKEND' in content and 'console' in content:
            print("✅ Console backend already configured in .env")
        else:
            print("📝 Adding console backend configuration to .env...")
            
            # Add console backend configuration
            console_config = """
# Development Email Configuration (Console Backend)
EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
"""
            
            with open(env_file, 'a') as f:
                f.write(console_config)
            
            print("✅ Console backend configuration added to .env")
    else:
        print("❌ .env file not found")
        print("📝 Creating .env file with console backend configuration...")
        
        console_config = """# Development Email Configuration
EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL='EZM Trade Management <noreply@ezmtrade.com>'
COMPANY_NAME='EZM Trade Management System'
COMPANY_EMAIL='noreply@ezmtrade.com'
"""
        
        with open(env_file, 'w') as f:
            f.write(console_config)
        
        print("✅ .env file created with console backend configuration")

def main():
    """Main diagnostic function"""
    print("=" * 60)
    print("  EZM TRADE MANAGEMENT - EMAIL DIAGNOSTIC TOOL")
    print("=" * 60)
    
    # Test network connectivity
    network_ok = test_network_connectivity()
    
    # Check email configuration
    config_ok, config_issues = check_email_configuration()
    
    # Test email service
    service_ok = test_email_service()
    
    # Provide solutions
    provide_solutions()
    
    # Summary
    print("\n" + "=" * 60)
    print("  DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    print(f"Network Connectivity: {'✅ OK' if network_ok else '❌ FAILED'}")
    print(f"Email Configuration: {'✅ OK' if config_ok else '❌ ISSUES FOUND'}")
    print(f"Email Service: {'✅ OK' if service_ok else '❌ FAILED'}")
    
    if not network_ok:
        print("\n⚠️  NETWORK ISSUE DETECTED")
        print("The system cannot reach the SMTP server. This could be due to:")
        print("• Network connectivity problems")
        print("• Firewall blocking outbound connections")
        print("• ISP blocking SMTP ports")
        
        response = input("\nWould you like to create a fallback console configuration? (y/n): ")
        if response.lower() == 'y':
            create_fallback_config()
            print("\n✅ Fallback configuration created!")
            print("Restart your Django server to apply the changes.")
    
    elif not config_ok:
        print(f"\n⚠️  CONFIGURATION ISSUES FOUND:")
        for issue in config_issues:
            print(f"• {issue}")
    
    elif not service_ok:
        print("\n⚠️  EMAIL SERVICE ISSUE")
        print("The email service is not working properly.")
    
    else:
        print("\n✅ ALL TESTS PASSED!")
        print("Your email functionality should be working correctly.")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main() 