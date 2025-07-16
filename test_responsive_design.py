#!/usr/bin/env python
"""
Test responsive design functionality
"""

import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

User = get_user_model()

def test_responsive_elements():
    """Test if responsive design elements are present in templates"""
    print("=== Testing Responsive Design Elements ===")
    
    client = Client()
    
    # Login as Head Manager
    login_data = {'username': 'HeadManager', 'password': 'password123'}
    response = client.post('/users/login/', login_data)
    
    if response.status_code == 302:
        # Test Head Manager dashboard
        response = client.get('/users/head-manager/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for mobile toggle button
            has_mobile_toggle = 'mobile-toggle' in content or 'mobileToggle' in content
            print(f"✓ Mobile toggle button: {'✓' if has_mobile_toggle else '✗'}")
            
            # Check for sidebar overlay
            has_sidebar_overlay = 'sidebar-overlay' in content
            print(f"✓ Sidebar overlay: {'✓' if has_sidebar_overlay else '✗'}")
            
            # Check for sidebar close button
            has_sidebar_close = 'sidebar-close' in content
            print(f"✓ Sidebar close button: {'✓' if has_sidebar_close else '✗'}")
            
            # Check for responsive JavaScript functions
            has_toggle_function = 'toggleSidebar' in content
            has_close_function = 'closeSidebar' in content
            print(f"✓ Toggle sidebar function: {'✓' if has_toggle_function else '✗'}")
            print(f"✓ Close sidebar function: {'✓' if has_close_function else '✗'}")
            
            # Check for EZM theme CSS
            has_ezm_theme = 'ezm-theme.css' in content
            print(f"✓ EZM theme CSS: {'✓' if has_ezm_theme else '✗'}")
            
            # Check for Bootstrap icons
            has_bootstrap_icons = 'bootstrap-icons' in content
            print(f"✓ Bootstrap icons: {'✓' if has_bootstrap_icons else '✗'}")
            
            # Check for viewport meta tag
            has_viewport = 'viewport' in content and 'width=device-width' in content
            print(f"✓ Responsive viewport: {'✓' if has_viewport else '✗'}")
            
            print(f"\n✓ Head Manager dashboard loaded successfully: 200")
            
        else:
            print(f"✗ Head Manager dashboard failed: {response.status_code}")
    else:
        print(f"✗ Login failed: {response.status_code}")

def test_different_roles():
    """Test responsive design across different role dashboards"""
    print("\n=== Testing Responsive Design Across Roles ===")
    
    test_cases = [
        ('HeadManager', 'password123', '/users/head-manager/', 'Head Manager'),
        ('store_manager1', 'password123', '/users/store-manager/', 'Store Manager'),
    ]
    
    for username, password, url, role_name in test_cases:
        client = Client()
        login_data = {'username': username, 'password': password}
        response = client.post('/users/login/', login_data)
        
        if response.status_code == 302:
            response = client.get(url)
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                has_mobile_elements = ('mobile-toggle' in content and 
                                     'sidebar-overlay' in content and 
                                     'toggleSidebar' in content)
                print(f"✓ {role_name} responsive elements: {'✓' if has_mobile_elements else '✗'}")
            else:
                print(f"✗ {role_name} dashboard failed: {response.status_code}")
        else:
            print(f"✗ {role_name} login failed: {response.status_code}")

def test_css_media_queries():
    """Test if CSS file contains proper media queries"""
    print("\n=== Testing CSS Media Queries ===")
    
    try:
        with open('static/css/ezm-theme.css', 'r') as f:
            css_content = f.read()
            
        # Check for mobile media query
        has_mobile_query = '@media (max-width: 768px)' in css_content
        print(f"✓ Mobile media query (768px): {'✓' if has_mobile_query else '✗'}")
        
        # Check for tablet media query
        has_tablet_query = '@media (max-width: 1024px)' in css_content
        print(f"✓ Tablet media query (1024px): {'✓' if has_tablet_query else '✗'}")
        
        # Check for small mobile query
        has_small_mobile = '@media (max-width: 480px)' in css_content
        print(f"✓ Small mobile query (480px): {'✓' if has_small_mobile else '✗'}")
        
        # Check for sidebar responsive classes
        has_sidebar_show = '.sidebar.show' in css_content
        has_sidebar_overlay = '.sidebar-overlay' in css_content
        has_mobile_toggle = '.mobile-toggle' in css_content
        
        print(f"✓ Sidebar show class: {'✓' if has_sidebar_show else '✗'}")
        print(f"✓ Sidebar overlay class: {'✓' if has_sidebar_overlay else '✗'}")
        print(f"✓ Mobile toggle class: {'✓' if has_mobile_toggle else '✗'}")
        
        # Check for EZM color variables
        has_color_vars = '--primary-dark' in css_content and '--accent-cyan' in css_content
        print(f"✓ EZM color variables: {'✓' if has_color_vars else '✗'}")
        
    except FileNotFoundError:
        print("✗ CSS file not found")

if __name__ == "__main__":
    print("Testing Responsive Design Implementation...")
    
    test_responsive_elements()
    test_different_roles()
    test_css_media_queries()
    
    print("\nResponsive design testing completed!")
