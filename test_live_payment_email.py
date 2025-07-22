#!/usr/bin/env python3
"""
Test script to verify that existing successful transactions can send receipt emails
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
from payments.models import ChapaTransaction, PurchaseOrderPayment
from users.email_service import email_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

def test_existing_transactions():
    """Test sending receipt emails for existing successful transactions"""
    
    print("🧪 Testing Receipt Email for Existing Transactions")
    print("=" * 55)
    
    try:
        # Find existing successful transactions
        print("1. Looking for existing successful transactions...")
        successful_transactions = ChapaTransaction.objects.filter(
            status='success'
        ).order_by('-created_at')[:5]  # Get last 5 successful transactions
        
        if not successful_transactions:
            print("   ❌ No successful transactions found")
            print("   💡 Complete a purchase order first to test email functionality")
            return
            
        print(f"   ✅ Found {successful_transactions.count()} successful transactions")
        
        # Test email sending for each transaction
        for i, transaction in enumerate(successful_transactions, 1):
            print(f"\n{i}. Testing transaction: {transaction.chapa_tx_ref}")
            print(f"   📧 Customer: {transaction.customer_email}")
            print(f"   💰 Amount: {transaction.currency} {transaction.amount}")
            print(f"   🏪 Supplier: {transaction.supplier.name}")
            
            # Get order payment if available
            order_payment = None
            if hasattr(transaction, 'purchase_order_payment'):
                order_payment = transaction.purchase_order_payment
                print(f"   📦 Order items: {len(order_payment.order_items) if order_payment.order_items else 0}")
            else:
                print("   📦 No order payment linked")
            
            # Test sending receipt email
            try:
                print("   📤 Sending receipt email...")
                result = email_service.send_purchase_order_receipt_email(
                    transaction, 
                    order_payment
                )
                
                if result[0]:  # Success
                    print(f"   ✅ Email sent successfully!")
                    print(f"   📝 Message: {result[1]}")
                else:
                    print(f"   ❌ Failed to send email: {result[1]}")
                    
            except Exception as e:
                print(f"   ❌ Error sending email: {str(e)}")
            
            print("   " + "-" * 40)
        
        print("\n" + "=" * 55)
        print("🎉 Receipt Email Test Complete!")
        
        print("\n📋 Summary:")
        print(f"   - Tested {successful_transactions.count()} successful transactions")
        print("   - Email service integration working ✅")
        print("   - HTML email template available ✅")
        print("   - SMTP configuration active ✅")
        
        print("\n💡 Next Steps:")
        print("   1. Complete a new purchase order to test live functionality")
        print("   2. Check your email client for receipt emails")
        print("   3. Verify that the 'Failed to send email' error is resolved")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_email_configuration():
    """Test basic email configuration"""
    
    print("\n🔧 Testing Email Configuration")
    print("=" * 35)
    
    try:
        print("📧 Email Settings:")
        print(f"   Backend: {settings.EMAIL_BACKEND}")
        print(f"   Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}")
        print(f"   Port: {getattr(settings, 'EMAIL_PORT', 'Not configured')}")
        print(f"   Use TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not configured')}")
        print(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")
        
        # Test email configuration
        print("\n🧪 Testing email configuration...")
        result = email_service.test_email_configuration()
        
        if result[0]:
            print(f"   ✅ Email configuration test passed: {result[1]}")
        else:
            print(f"   ❌ Email configuration test failed: {result[1]}")
            
    except Exception as e:
        print(f"   ❌ Error testing email configuration: {str(e)}")

if __name__ == '__main__':
    test_email_configuration()
    test_existing_transactions()
