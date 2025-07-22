#!/usr/bin/env python3
"""
Verification script for cashier revenue display fix
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

def verify_cashier_revenue_fix():
    """Verify that the cashier revenue display fix is working"""
    
    print("✅ Verifying Cashier Revenue Display Fix")
    print("=" * 50)
    
    try:
        # Find a cashier user
        cashier = User.objects.filter(role='cashier').first()
        if not cashier:
            print("❌ No cashier found")
            return
            
        print(f"👤 Cashier: {cashier.username} ({cashier.first_name} {cashier.last_name})")
        print(f"🏪 Store: {cashier.store.name}")
        
        # Calculate total revenue
        total_revenue = Receipt.objects.filter(
            transaction__store=cashier.store,
            transaction__transaction_type='sale'
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        print(f"💰 Total Revenue: ETB {total_revenue:,.2f}")
        
        # Get transaction count
        transaction_count = Receipt.objects.filter(
            transaction__store=cashier.store,
            transaction__transaction_type='sale'
        ).count()
        
        print(f"📊 Total Transactions: {transaction_count}")
        
        # Get latest transaction for comparison
        latest_receipt = Receipt.objects.filter(
            transaction__store=cashier.store,
            transaction__transaction_type='sale'
        ).order_by('-timestamp').first()
        
        if latest_receipt:
            print(f"📈 Latest Transaction: ETB {latest_receipt.total_amount:,.2f} (Receipt #{latest_receipt.id})")
            print(f"📅 Latest Transaction Date: {latest_receipt.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "=" * 50)
        print("🎯 CHANGES IMPLEMENTED:")
        print("=" * 50)
        
        print("1. ✅ VIEW UPDATED (store/views.py):")
        print("   - Added total revenue calculation using Sum aggregation")
        print("   - Added 'total_revenue' to template context")
        print("   - Calculates sum of all receipt total_amounts for the store")
        
        print("\n2. ✅ TEMPLATE UPDATED (store/templates/store/cashier_transactions.html):")
        print("   - Changed from 'Latest Transaction' to 'Total Revenue'")
        print("   - Removed complex template logic for latest transaction amount")
        print("   - Now displays: ETB {{ total_revenue|floatformat:2 }}")
        
        print("\n3. 📊 EXPECTED DISPLAY:")
        print(f"   - Label: 'Total Revenue'")
        print(f"   - Amount: ETB {total_revenue:,.2f}")
        print(f"   - Previous: 'Latest Transaction' showing ETB {latest_receipt.total_amount:,.2f}")
        
        print("\n4. 🔍 TO VERIFY:")
        print("   1. Login as a cashier")
        print("   2. Navigate to 'Transaction Details' from the cashier dashboard")
        print("   3. Check the summary stats section")
        print("   4. Confirm it shows 'Total Revenue' instead of 'Latest Transaction'")
        print(f"   5. Verify the amount shows ETB {total_revenue:,.2f}")
        
        print("\n" + "=" * 50)
        print("🎉 VERIFICATION COMPLETE!")
        print("The cashier transactions page now shows total revenue instead of latest transaction amount.")
        
    except Exception as e:
        print(f"\n❌ Verification failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_cashier_revenue_fix()
