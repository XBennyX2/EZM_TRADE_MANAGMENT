#!/usr/bin/env python3
"""
Test script to verify improved email error handling
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/home/silence/Documents/EZM_TRADE_MANAGMENT')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from store.models import Store
from transactions.models import Transaction, Receipt
from decimal import Decimal
import json

User = get_user_model()

def test_email_error_scenarios():
    """Test various email error scenarios"""
    
    print("🧪 Testing Email Error Handling Scenarios")
    print("=" * 50)
    
    try:
        # Setup test data
        cashier = User.objects.filter(role='cashier').first()
        if not cashier:
            print("❌ No cashier found")
            return
            
        receipt = Receipt.objects.filter(transaction__store=cashier.store).first()
        if not receipt:
            print("❌ No receipt found")
            return
            
        print(f"✅ Using cashier: {cashier.username}")
        print(f"✅ Using receipt: #{receipt.id}")
        
        client = Client()
        client.force_login(cashier)
        
        # Test scenarios
        test_scenarios = [
            {
                'name': 'Valid Email',
                'email': 'test@example.com',
                'expected_success': True
            },
            {
                'name': 'Invalid Email Format',
                'email': 'invalid-email',
                'expected_success': False
            },
            {
                'name': 'Empty Email',
                'email': '',
                'expected_success': False
            },
            {
                'name': 'Email with Spaces',
                'email': '  test@example.com  ',
                'expected_success': True  # Should be trimmed
            }
        ]
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}. Testing: {scenario['name']}")
            print(f"   📧 Email: '{scenario['email']}'")
            
            email_data = {"email": scenario['email']}
            response = client.post(
                f'/stores/receipt/{receipt.id}/email/',
                data=json.dumps(email_data),
                content_type='application/json'
            )
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code in [200, 400, 500]:
                try:
                    response_data = response.json()
                    print(f"   📝 Response: {response_data}")
                    
                    success = response_data.get('success', False)
                    if success == scenario['expected_success']:
                        print("   ✅ Expected result")
                    else:
                        print(f"   ⚠️  Unexpected result: got {success}, expected {scenario['expected_success']}")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response: {response.content}")
            else:
                print(f"   ❌ Unexpected status code: {response.status_code}")
        
        # Test with malformed JSON
        print(f"\n{len(test_scenarios) + 1}. Testing: Malformed JSON")
        response = client.post(
            f'/stores/receipt/{receipt.id}/email/',
            data='{"email": invalid json}',
            content_type='application/json'
        )
        print(f"   📊 Status: {response.status_code}")
        if response.status_code in [200, 400, 500]:
            try:
                response_data = response.json()
                print(f"   📝 Response: {response_data}")
            except:
                print(f"   📝 Raw response: {response.content}")
        
        print("\n" + "=" * 50)
        print("🎉 Email Error Handling Test Complete!")
        
        print("\n💡 Key Improvements Made:")
        print("   1. Better JavaScript error logging")
        print("   2. Consistent server response format")
        print("   3. More detailed error messages")
        print("   4. HTTP status code checking")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_email_error_scenarios()
