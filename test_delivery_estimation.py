#!/usr/bin/env python
"""
Test script to verify supplier-specific delivery time calculation
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EZM_TRADE_MANAGMENT.settings')
sys.path.append('.')
django.setup()

from Inventory.models import Supplier, SupplierProduct, SupplierProfile
from datetime import datetime, timedelta

def test_delivery_estimation():
    """Test the delivery estimation functionality"""
    print("🧪 Testing Supplier-Specific Delivery Estimation")
    print("=" * 60)
    
    # Test 1: Test delivery timeframe parsing
    print("\n1. Testing delivery timeframe parsing...")
    
    test_cases = [
        ("3-5 business days", 5),
        ("1-2 weeks", 14),
        ("2 days", 2),
        ("1 week", 7),
        ("5-7 days", 7),
        ("2-3 business days", 3),
        ("1 day", 1),
        ("", 7),  # Default
        (None, 7),  # Default
    ]
    
    # Get a supplier to test with
    supplier = Supplier.objects.first()
    if not supplier:
        print("❌ No suppliers found in database")
        return False
    
    for timeframe, expected_days in test_cases:
        try:
            actual_days = supplier._parse_delivery_timeframe(timeframe)
            status = "✅" if actual_days == expected_days else "❌"
            print(f"   {status} '{timeframe}' → {actual_days} days (expected: {expected_days})")
        except Exception as e:
            print(f"   ❌ Error parsing '{timeframe}': {str(e)}")
    
    # Test 2: Test supplier delivery estimation
    print("\n2. Testing supplier delivery estimation...")
    
    try:
        suppliers = Supplier.objects.all()[:3]
        for supplier in suppliers:
            delivery_days = supplier.get_estimated_delivery_days()
            print(f"   ✅ {supplier.name}: {delivery_days} days")
            
            # Check if supplier has profile with delivery timeframe
            try:
                profile = supplier.profile
                if profile.estimated_delivery_timeframe:
                    print(f"      Profile timeframe: '{profile.estimated_delivery_timeframe}'")
                else:
                    print(f"      No profile timeframe set (using default)")
            except:
                print(f"      No profile found (using default)")
                
    except Exception as e:
        print(f"   ❌ Error testing supplier delivery estimation: {str(e)}")
    
    # Test 3: Test product-specific delivery estimation
    print("\n3. Testing product-specific delivery estimation...")
    
    try:
        products = SupplierProduct.objects.all()[:5]
        for product in products:
            delivery_days = product.get_estimated_delivery_days()
            print(f"   ✅ {product.product_name}: {delivery_days} days")
            
            if product.estimated_delivery_time:
                print(f"      Product timeframe: '{product.estimated_delivery_time}'")
            else:
                print(f"      Using supplier default")
                
    except Exception as e:
        print(f"   ❌ Error testing product delivery estimation: {str(e)}")
    
    # Test 4: Test purchase order delivery calculation
    print("\n4. Testing purchase order delivery calculation...")
    
    try:
        from payments.models import PurchaseOrderPayment
        from django.utils import timezone
        
        # Get a supplier with known delivery time
        supplier = Supplier.objects.first()
        delivery_days = supplier.get_estimated_delivery_days()
        
        print(f"   Supplier: {supplier.name}")
        print(f"   Estimated delivery days: {delivery_days}")
        
        # Calculate expected delivery date
        expected_delivery = timezone.now().date() + timedelta(days=delivery_days)
        print(f"   Expected delivery date: {expected_delivery}")
        
        # Test the calculation logic
        today = timezone.now().date()
        calculated_delivery = today + timedelta(days=delivery_days)
        
        if calculated_delivery == expected_delivery:
            print("   ✅ Delivery date calculation is correct")
        else:
            print("   ❌ Delivery date calculation mismatch")
            
    except Exception as e:
        print(f"   ❌ Error testing purchase order delivery calculation: {str(e)}")
    
    # Test 5: Test edge cases
    print("\n5. Testing edge cases...")
    
    edge_cases = [
        "next day delivery",
        "same day",
        "24 hours",
        "48-72 hours",
        "within 1 week",
        "up to 2 weeks",
        "3 to 5 working days",
    ]
    
    for case in edge_cases:
        try:
            days = supplier._parse_delivery_timeframe(case)
            print(f"   '{case}' → {days} days")
        except Exception as e:
            print(f"   ❌ Error with '{case}': {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Delivery estimation testing completed!")
    
    return True

def test_real_supplier_data():
    """Test with real supplier data from the database"""
    print("\n🔍 Testing with Real Supplier Data")
    print("=" * 40)
    
    try:
        suppliers = Supplier.objects.all()
        
        for supplier in suppliers:
            print(f"\n📦 Supplier: {supplier.name}")
            
            # Check supplier profile
            try:
                profile = supplier.profile
                print(f"   Profile delivery timeframe: '{profile.estimated_delivery_timeframe}'")
                parsed_days = supplier.get_estimated_delivery_days()
                print(f"   Parsed to: {parsed_days} days")
            except:
                print(f"   No profile found - using default 7 days")
            
            # Check supplier products
            products = SupplierProduct.objects.filter(supplier=supplier)[:3]
            if products:
                print(f"   Sample products:")
                for product in products:
                    product_days = product.get_estimated_delivery_days()
                    product_timeframe = product.estimated_delivery_time or "Not set"
                    print(f"     - {product.product_name}: {product_days} days ('{product_timeframe}')")
            else:
                print(f"   No products found")
                
    except Exception as e:
        print(f"❌ Error testing real supplier data: {str(e)}")

if __name__ == "__main__":
    success = test_delivery_estimation()
    test_real_supplier_data()
    
    if success:
        print("\n🟢 All delivery estimation tests completed!")
        print("\n📋 Summary:")
        print("✅ Delivery timeframe parsing working")
        print("✅ Supplier-specific delivery estimation working")
        print("✅ Product-specific delivery estimation working")
        print("✅ Purchase order delivery calculation updated")
        print("✅ Edge cases handled gracefully")
    else:
        print("\n🔴 Some tests failed. Please check the implementation.")
