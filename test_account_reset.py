#!/usr/bin/env python
"""
Test script for the enhanced account reset functionality
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/silence/Documents/EZM_TRADE_MANAGMENT')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.forms import AccountResetForm
from users.models import CustomUser

def test_account_reset_form():
    """Test the AccountResetForm functionality"""
    print("Testing AccountResetForm...")
    
    # Create a test user if it doesn't exist
    test_user, created = CustomUser.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'store_manager'
        }
    )
    
    if created:
        print(f"Created test user: {test_user.username}")
    else:
        print(f"Using existing test user: {test_user.username}")
    
    # Test 1: Valid form data
    print("\n1. Testing valid form data...")
    form_data = {
        'new_email': 'newemail@example.com',
        'reset_reason': 'Testing account reset functionality',
        'confirm_reset': True
    }
    
    form = AccountResetForm(data=form_data, user_being_reset=test_user)
    if form.is_valid():
        print("✓ Form is valid with correct data")
    else:
        print("✗ Form validation failed:")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
    
    # Test 2: Email uniqueness validation
    print("\n2. Testing email uniqueness validation...")
    
    # Create another user with a different email
    other_user, created = CustomUser.objects.get_or_create(
        username='otheruser',
        defaults={
            'email': 'other@example.com',
            'first_name': 'Other',
            'last_name': 'User',
            'role': 'cashier'
        }
    )
    
    # Try to use the other user's email
    form_data_duplicate = {
        'new_email': 'other@example.com',
        'reset_reason': 'Testing duplicate email',
        'confirm_reset': True
    }
    
    form = AccountResetForm(data=form_data_duplicate, user_being_reset=test_user)
    if not form.is_valid() and 'new_email' in form.errors:
        print("✓ Email uniqueness validation working correctly")
    else:
        print("✗ Email uniqueness validation failed")
    
    # Test 3: Same user can keep their own email
    print("\n3. Testing user can keep their own email...")
    form_data_same = {
        'new_email': test_user.email,
        'reset_reason': 'Keeping same email',
        'confirm_reset': True
    }
    
    form = AccountResetForm(data=form_data_same, user_being_reset=test_user)
    if form.is_valid():
        print("✓ User can keep their own email")
    else:
        print("✗ User cannot keep their own email (unexpected)")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
    
    # Test 4: Missing required fields
    print("\n4. Testing missing required fields...")
    form_data_incomplete = {
        'reset_reason': 'Missing email and confirmation',
    }
    
    form = AccountResetForm(data=form_data_incomplete, user_being_reset=test_user)
    if not form.is_valid():
        print("✓ Form correctly rejects missing required fields")
        missing_fields = [field for field in ['new_email', 'confirm_reset'] if field in form.errors]
        print(f"  Missing fields detected: {missing_fields}")
    else:
        print("✗ Form should reject missing required fields")
    
    # Test 5: Invalid email format
    print("\n5. Testing invalid email format...")
    form_data_invalid_email = {
        'new_email': 'invalid-email-format',
        'reset_reason': 'Testing invalid email',
        'confirm_reset': True
    }
    
    form = AccountResetForm(data=form_data_invalid_email, user_being_reset=test_user)
    if not form.is_valid() and 'new_email' in form.errors:
        print("✓ Invalid email format correctly rejected")
    else:
        print("✗ Invalid email format should be rejected")
    
    print("\nAccount reset form testing completed!")

def test_form_initialization():
    """Test form initialization with user data"""
    print("\nTesting form initialization...")
    
    test_user = CustomUser.objects.filter(username='testuser').first()
    if not test_user:
        print("✗ Test user not found")
        return
    
    form = AccountResetForm(user_being_reset=test_user)
    
    if form.fields['new_email'].initial == test_user.email:
        print("✓ Form correctly pre-populates with user's current email")
    else:
        print("✗ Form should pre-populate with user's current email")
        print(f"  Expected: {test_user.email}")
        print(f"  Got: {form.fields['new_email'].initial}")

if __name__ == '__main__':
    print("=== Enhanced Account Reset Functionality Test ===")
    test_account_reset_form()
    test_form_initialization()
    print("\n=== Test Complete ===")
