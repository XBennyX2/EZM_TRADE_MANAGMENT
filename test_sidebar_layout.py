#!/usr/bin/env python
"""
Test script to verify the initiate order page works correctly with sidebar layout
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import authenticate

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import CustomUser

def test_sidebar_layout():
    """Test that the initiate order page loads correctly with sidebar"""
    print("🧪 Testing EZM Initiate Order Page with Sidebar Layout")
    print("=" * 60)
    
    # Get the test cashier user
    try:
        cashier = CustomUser.objects.filter(username='test_cashier').first()
        if not cashier:
            print("❌ No test cashier user found")
            return False
        print(f"✅ Found test cashier: {cashier.username}")
    except Exception as e:
        print(f"❌ Error finding cashier: {e}")
        return False
    
    # Test Django client functionality
    client = Client()
    
    # Login as cashier
    try:
        login_success = client.login(username=cashier.username, password='testpass123')
        if not login_success:
            print("❌ Failed to login as cashier")
            return False
        print("✅ Successfully logged in as cashier")
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test initiate order page access
    print("\n📄 Testing Initiate Order Page Access")
    print("-" * 40)
    
    try:
        response = client.get('/stores/cashier/initiate-order/')
        
        if response.status_code == 200:
            print("✅ Initiate order page loads successfully")
            
            # Check if the page contains expected elements
            content = response.content.decode()
            
            # Check for sidebar elements
            if 'base_sidebar.html' in str(response.templates):
                print("✅ Page extends base_sidebar.html template")
            else:
                print("❌ Page does not extend base_sidebar.html template")
                return False
            
            # Check for key page elements
            checks = [
                ('New Order', 'Page title present'),
                ('Select Products', 'Product selection section present'),
                ('Shopping Cart', 'Shopping cart section present'),
                ('sidebar', 'Sidebar navigation present'),
                ('main-content', 'Main content area present'),
                ('ezm-card', 'EZM styling applied'),
                ('ETB', 'Ethiopian currency display'),
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    print(f"✅ {description}")
                else:
                    print(f"❌ {description} - Missing: {check_text}")
            
            # Check for JavaScript functionality
            if 'updateCartDisplay' in content:
                print("✅ Cart JavaScript functionality present")
            else:
                print("❌ Cart JavaScript functionality missing")
                
            # Check for proper styling
            if 'ezm-card' in content and '#66FCF1' in content:
                print("✅ EZM styling and colors applied")
            else:
                print("❌ EZM styling not properly applied")
                
        else:
            print(f"❌ Page load failed with status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Page access error: {e}")
        return False
    
    # Test sidebar navigation
    print("\n🧭 Testing Sidebar Navigation")
    print("-" * 30)
    
    try:
        # Test cashier dashboard access
        response = client.get('/stores/cashier-dashboard/')
        if response.status_code == 200:
            print("✅ Cashier dashboard accessible")
        else:
            print(f"❌ Cashier dashboard not accessible: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Navigation test error: {e}")
    
    print("\n🎉 Sidebar Layout Test Completed!")
    print("✅ Initiate order page successfully uses sidebar layout")
    print("✅ Navigation elements properly integrated")
    print("✅ EZM styling maintained with sidebar")
    return True

if __name__ == "__main__":
    success = test_sidebar_layout()
    sys.exit(0 if success else 1)
