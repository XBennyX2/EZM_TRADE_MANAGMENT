#!/usr/bin/env python
"""
Simple login test to debug authentication issues
"""

import os
import django
from django.test import Client
from django.contrib.auth import get_user_model, authenticate

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

User = get_user_model()

def test_authentication():
    """Test basic authentication"""
    print("=== Testing Basic Authentication ===")
    
    # Test authenticate function directly
    user = authenticate(username='HeadManager', password='password123')
    if user:
        print(f"✓ Authentication successful: {user.username}")
        print(f"  Role: {user.role}")
        print(f"  Active: {user.is_active}")
        print(f"  First Login: {user.is_first_login}")
    else:
        print("✗ Authentication failed")
    
    # Test with Django test client
    client = Client()
    
    # Test login form submission
    login_data = {
        'username': 'HeadManager',
        'password': 'password123'
    }
    
    response = client.post('/users/login/', login_data)
    print(f"\nLogin POST response: {response.status_code}")
    
    if hasattr(response, 'url'):
        print(f"Redirect URL: {response.url}")
    
    # Check if we can access Head Manager page after login
    response = client.get('/users/head-manager/')
    print(f"Head Manager page access: {response.status_code}")
    
    # Check session
    if hasattr(client, 'session'):
        print(f"Session keys: {list(client.session.keys())}")

if __name__ == "__main__":
    test_authentication()
