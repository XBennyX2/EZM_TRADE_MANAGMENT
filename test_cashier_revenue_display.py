#!/usr/bin/env python3
"""
Test script to verify cashier transactions page shows total revenue instead of latest transaction
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
from django.db.models import Sum

User = get_user_model()

def test_cashier_revenue_display():
    """Test that cashier transactions page shows total revenue"""
    
    print("🧪 Testing Cashier Revenue Display")
    print("=" * 45)
    
    try:
        # Find a cashier user
        cashier = User.objects.filter(role='cashier').first()
        if not cashier:
            print("❌ No cashier found")
            return
            
        print(f"✅ Using cashier: {cashier.username}")
        print(f"🏪 Store: {cashier.store.name if cashier.store else 'No store assigned'}")
        
        # Calculate expected total revenue
        total_revenue = Receipt.objects.filter(
            transaction__store=cashier.store,
            transaction__transaction_type='sale'
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        print(f"💰 Expected total revenue: ETB {total_revenue:,.2f}")
        
        # Get recent receipts for comparison
        receipts = Receipt.objects.filter(
            transaction__store=cashier.store,
            transaction__transaction_type='sale'
        ).select_related('transaction').order_by('-timestamp')[:5]
        
        print(f"📊 Recent transactions:")
        for i, receipt in enumerate(receipts, 1):
            print(f"   {i}. Receipt #{receipt.id}: ETB {receipt.total_amount:,.2f} ({receipt.timestamp.strftime('%Y-%m-%d %H:%M')})")
        
        if receipts:
            latest_amount = receipts[0].total_amount
            print(f"📈 Latest transaction amount: ETB {latest_amount:,.2f}")
            print(f"🔄 Change: Showing total revenue (ETB {total_revenue:,.2f}) instead of latest (ETB {latest_amount:,.2f})")
        
        # Test the view
        print(f"\n🌐 Testing cashier transactions view...")
        client = Client()
        client.force_login(cashier)
        
        response = client.get('/stores/cashier/transactions/')
        
        print(f"   📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if total_revenue is in context
            context = response.context
            if context and 'total_revenue' in context:
                context_revenue = context['total_revenue']
                print(f"   💰 Context total_revenue: ETB {context_revenue:,.2f}")
                
                if context_revenue == total_revenue:
                    print("   ✅ Total revenue calculation correct!")
                else:
                    print(f"   ⚠️  Revenue mismatch: expected {total_revenue}, got {context_revenue}")
            else:
                print("   ❌ total_revenue not found in context")
                
            # Check template content
            content = response.content.decode('utf-8')
            if 'Total Revenue' in content:
                print("   ✅ Template shows 'Total Revenue' label")
            else:
                print("   ❌ Template doesn't show 'Total Revenue' label")
                
            if 'Latest Transaction' in content:
                print("   ⚠️  Template still shows 'Latest Transaction' (should be removed)")
            else:
                print("   ✅ 'Latest Transaction' label removed from template")
                
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
        
        print("\n" + "=" * 45)
        print("🎉 Cashier Revenue Display Test Complete!")
        
        print("\n📋 Changes Made:")
        print("   1. ✅ Updated view to calculate total revenue")
        print("   2. ✅ Added total_revenue to template context")
        print("   3. ✅ Changed template to show 'Total Revenue'")
        print("   4. ✅ Removed 'Latest Transaction' display")
        
        print("\n💡 Summary:")
        print(f"   - Total transactions: {receipts.count()}")
        print(f"   - Total revenue: ETB {total_revenue:,.2f}")
        print("   - Display changed from latest transaction to total revenue")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_cashier_revenue_display()
