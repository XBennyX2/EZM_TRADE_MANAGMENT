#!/usr/bin/env python3
"""
Test script to debug the cashier email receipt functionality
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

def test_cashier_email_functionality():
    """Test the cashier email receipt functionality"""
    
    print("🧪 Testing Cashier Email Receipt Functionality")
    print("=" * 55)
    
    try:
        # Check email configuration
        print("1. Checking email configuration...")
        print(f"   EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not configured')}")
        print(f"   EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not configured')}")
        print(f"   DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')}")
        
        # Find a cashier user
        print("\n2. Finding cashier user...")
        cashier = User.objects.filter(role='cashier').first()
        if not cashier:
            print("   ❌ No cashier found. Creating test cashier...")
            # Get or create a store first
            store, created = Store.objects.get_or_create(
                name='Test Store',
                defaults={
                    'address': 'Test Address',
                    'phone_number': '+251911000000'
                }
            )
            
            cashier = User.objects.create_user(
                username='test_cashier',
                email='cashier@example.com',
                password='testpass123',
                first_name='Test',
                last_name='Cashier',
                role='cashier',
                store=store
            )
            print(f"   ✅ Created test cashier: {cashier.username}")
        else:
            print(f"   ✅ Found cashier: {cashier.username} ({cashier.email})")
            print(f"   🏪 Store: {cashier.store.name if cashier.store else 'No store assigned'}")
        
        # Find or create a receipt
        print("\n3. Finding test receipt...")
        receipt = Receipt.objects.filter(transaction__store=cashier.store).first()
        
        if not receipt:
            print("   ❌ No receipt found. Creating test receipt...")
            
            # Create a test transaction
            transaction = Transaction.objects.create(
                quantity=1,
                transaction_type='sale',
                store=cashier.store,
                total_amount=Decimal('25.00'),
                payment_type='cash'
            )
            
            # Create a test receipt
            receipt = Receipt.objects.create(
                transaction=transaction,
                total_amount=Decimal('25.00'),
                items_data=[
                    {
                        'name': 'Test Product',
                        'quantity': 1,
                        'price': 25.00,
                        'total': 25.00
                    }
                ]
            )
            print(f"   ✅ Created test receipt: #{receipt.id}")
        else:
            print(f"   ✅ Found receipt: #{receipt.id}")
            print(f"   💰 Amount: ${receipt.total_amount}")
        
        # Test the email receipt endpoint
        print("\n4. Testing email receipt endpoint...")
        
        client = Client()
        client.force_login(cashier)
        
        # Test with valid email
        test_email = "abeneman123@gmail.com"
        print(f"   📧 Testing with email: {test_email}")
        
        email_data = {"email": test_email}
        response = client.post(
            f'/stores/receipt/{receipt.id}/email/',
            data=json.dumps(email_data),
            content_type='application/json'
        )
        
        print(f"   📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"   📝 Response: {response_data}")
            
            if response_data.get('success'):
                print("   ✅ Email sent successfully!")
            else:
                print(f"   ❌ Email failed: {response_data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   📝 Error: {error_data}")
            except:
                print(f"   📝 Response content: {response.content}")
        
        # Test email configuration directly
        print("\n5. Testing email sending directly...")
        try:
            from django.core.mail import EmailMessage
            
            test_email_msg = EmailMessage(
                subject='Test Email from EZM Trade Management',
                body='This is a test email to verify email configuration.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[test_email],
            )
            
            test_email_msg.send()
            print("   ✅ Direct email test successful!")
            
        except Exception as e:
            print(f"   ❌ Direct email test failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 55)
        print("🎉 Cashier Email Receipt Test Complete!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_cashier_email_functionality()
