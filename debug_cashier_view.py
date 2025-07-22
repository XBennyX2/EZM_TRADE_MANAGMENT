#!/usr/bin/env python3
"""
Debug script to check cashier transactions view
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
from store.models import Store
from transactions.models import Transaction, Receipt
from decimal import Decimal
from django.db.models import Sum

User = get_user_model()

def debug_cashier_view():
    """Debug the cashier transactions view logic"""
    
    print("🔍 Debugging Cashier View Logic")
    print("=" * 40)
    
    try:
        # Find a cashier user
        cashier = User.objects.filter(role='cashier').first()
        if not cashier:
            print("❌ No cashier found")
            return
            
        print(f"✅ Cashier: {cashier.username}")
        print(f"🏪 Store: {cashier.store}")
        
        # Test the exact logic from the view
        print("\n📊 Testing receipts query...")
        receipts = Receipt.objects.filter(
            transaction__store=cashier.store,
            transaction__transaction_type='sale'
        ).select_related('transaction').order_by('-timestamp')[:50]
        
        print(f"   Found {receipts.count()} receipts")
        
        print("\n💰 Testing revenue calculation...")
        total_revenue = Receipt.objects.filter(
            transaction__store=cashier.store,
            transaction__transaction_type='sale'
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        print(f"   Total revenue: ETB {total_revenue:,.2f}")
        
        # Test the view function directly
        print("\n🧪 Testing view function directly...")
        from django.http import HttpRequest
        from django.contrib.auth.models import AnonymousUser
        from store.views import cashier_transactions
        
        # Create a mock request
        request = HttpRequest()
        request.user = cashier
        request.method = 'GET'
        
        # Add session and messages
        from django.contrib.sessions.backends.db import SessionStore
        from django.contrib.messages.storage.fallback import FallbackStorage
        
        request.session = SessionStore()
        request._messages = FallbackStorage(request)
        
        try:
            response = cashier_transactions(request)
            print(f"   ✅ View executed successfully")
            print(f"   📊 Response status: {response.status_code}")
            
            # Check if it's a redirect
            if hasattr(response, 'url'):
                print(f"   🔄 Redirect to: {response.url}")
            else:
                print(f"   📄 Template response generated")
                
        except Exception as view_error:
            print(f"   ❌ View error: {str(view_error)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 40)
        print("🎉 Debug Complete!")
        
    except Exception as e:
        print(f"\n❌ Debug failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_cashier_view()
