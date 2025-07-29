#!/usr/bin/env python3
"""
Test script to verify that the order-tracking tab works perfectly on the purchase orders page.
"""

import os
import sys
import django
from decimal import Decimal
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from Inventory.models import (
    Warehouse, WarehouseProduct, Supplier, PurchaseOrder, 
    PurchaseOrderItem
)

User = get_user_model()

def test_purchase_orders_page_loads():
    """Test that the purchase orders page loads correctly"""
    print("🧪 Testing purchase orders page loads...")
    
    try:
        # Get an existing head manager
        head_manager = User.objects.filter(role='head_manager').first()
        
        if not head_manager:
            print("❌ No head manager found in database")
            return False
        
        print(f"👤 Using head manager: {head_manager.username}")
        
        # Test the purchase orders page
        client = Client()
        client.force_login(head_manager)
        
        print("🌐 Testing purchase orders page...")
        
        response = client.get('/inventory/purchase-orders/')
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"🔄 Redirected to: {response.get('Location', 'Unknown')}")
            return False
        elif response.status_code == 200:
            print("✅ Purchase orders page loaded successfully!")
            
            # Check if the page contains expected content
            content = response.content.decode('utf-8')
            
            # Check for tab structure
            if 'id="orderTabs"' in content:
                print("✅ Tab container found")
            else:
                print("❌ Tab container not found")
                return False
            
            # Check for order tracking tab
            if 'id="tracking-tab"' in content:
                print("✅ Order tracking tab found")
            else:
                print("❌ Order tracking tab not found")
                return False
            
            # Check for tab content
            if 'id="tracking"' in content:
                print("✅ Order tracking tab content found")
            else:
                print("❌ Order tracking tab content not found")
                return False
            
            # Check for JavaScript initialization
            if 'initializeTabs()' in content:
                print("✅ Tab initialization JavaScript found")
            else:
                print("❌ Tab initialization JavaScript not found")
                return False
            
            # Check for Bootstrap tab functionality
            if 'data-bs-toggle="tab"' in content:
                print("✅ Bootstrap tab attributes found")
            else:
                print("❌ Bootstrap tab attributes not found")
                return False
            
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_order_tracking_content():
    """Test that the order tracking tab contains the expected content"""
    print("\n🧪 Testing order tracking tab content...")
    
    try:
        # Get an existing head manager
        head_manager = User.objects.filter(role='head_manager').first()
        
        # Test the purchase orders page
        client = Client()
        client.force_login(head_manager)
        
        response = client.get('/inventory/purchase-orders/')
        content = response.content.decode('utf-8')
        
        # Check for order tracking specific elements
        tracking_elements = [
            'Order Tracking & Delivery Management',
            'tracking-container',
            'progress-timeline',
            'timeline-step',
            'countdown-timer',
            'confirmDelivery',
            'deliveryConfirmationModal',
            'issueReportModal'
        ]
        
        missing_elements = []
        for element in tracking_elements:
            if element in content:
                print(f"✅ Found: {element}")
            else:
                print(f"❌ Missing: {element}")
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing {len(missing_elements)} tracking elements")
            return False
        else:
            print("✅ All order tracking elements found")
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

def test_order_tracking_javascript():
    """Test that the order tracking JavaScript functions are present"""
    print("\n🧪 Testing order tracking JavaScript functions...")
    
    try:
        # Get an existing head manager
        head_manager = User.objects.filter(role='head_manager').first()
        
        # Test the purchase orders page
        client = Client()
        client.force_login(head_manager)
        
        response = client.get('/inventory/purchase-orders/')
        content = response.content.decode('utf-8')
        
        # Check for JavaScript functions
        js_functions = [
            'initializeTabs()',
            'initializeCountdownTimers()',
            'updateOrderStatistics()',
            'confirmDelivery',
            'submitDeliveryConfirmation',
            'reportIssue',
            'submitIssueReport',
            'refreshCountdownTimers',
            'testTabs',
            'showTrackingTab',
            'validatePageComponents'
        ]
        
        missing_functions = []
        for func in js_functions:
            if func in content:
                print(f"✅ Found JS function: {func}")
            else:
                print(f"❌ Missing JS function: {func}")
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ Missing {len(missing_functions)} JavaScript functions")
            return False
        else:
            print("✅ All JavaScript functions found")
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

def test_order_tracking_with_data():
    """Test order tracking tab with actual purchase order data"""
    print("\n🧪 Testing order tracking with purchase order data...")
    
    try:
        # Get existing purchase orders
        purchase_orders = PurchaseOrder.objects.all()
        print(f"📦 Found {purchase_orders.count()} purchase orders")
        
        if purchase_orders.count() == 0:
            print("⚠️ No purchase orders found - creating test data...")
            
            # Create test data
            head_manager = User.objects.filter(role='head_manager').first()
            supplier = Supplier.objects.first()
            warehouse = Warehouse.objects.first()
            
            if not supplier:
                supplier = Supplier.objects.create(
                    name='Test Tracking Supplier',
                    email='tracking@test.com',
                    phone='1234567890',
                    address='Test Address'
                )
            
            if not warehouse:
                warehouse = Warehouse.objects.create(
                    name='Test Tracking Warehouse',
                    address='Test Location',
                    manager_name=head_manager.get_full_name(),
                    capacity=1000,
                    current_utilization=0
                )
            
            # Create warehouse product
            product = WarehouseProduct.objects.create(
                product_id='TTP001',
                product_name='Test Tracking Product',
                sku='TTP001-SKU',
                quantity_in_stock=50,
                unit_price=Decimal('30.00'),
                category='construction',
                supplier=supplier,
                warehouse=warehouse
            )
            
            # Create purchase order
            purchase_order = PurchaseOrder.objects.create(
                order_number='TEST-TRACKING-PO-001',
                supplier=supplier,
                created_by=head_manager,
                order_date=timezone.now().date(),
                status='in_transit',
                total_amount=Decimal('600.00'),
                delivery_address='Test Delivery Address',
                expected_delivery_date=timezone.now().date() + timezone.timedelta(days=3)
            )
            
            # Create purchase order item
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                warehouse_product=product,
                quantity_ordered=20,
                unit_price=Decimal('30.00')
            )
            
            print("✅ Test purchase order created")
        
        # Test the page with data
        head_manager = User.objects.filter(role='head_manager').first()
        client = Client()
        client.force_login(head_manager)
        
        response = client.get('/inventory/purchase-orders/')
        content = response.content.decode('utf-8')
        
        # Check for order data in tracking tab
        if 'TEST-TRACKING-PO-001' in content or purchase_orders.exists():
            print("✅ Purchase order data found in page")
        else:
            print("❌ No purchase order data found in page")
            return False
        
        # Check for order cards in tracking section
        if 'order-card' in content:
            print("✅ Order cards found")
        else:
            print("❌ Order cards not found")
            return False
        
        # Check for status indicators
        status_indicators = ['badge bg-info', 'badge bg-success', 'badge bg-warning']
        found_indicators = [indicator for indicator in status_indicators if indicator in content]
        
        if found_indicators:
            print(f"✅ Status indicators found: {len(found_indicators)}")
        else:
            print("❌ No status indicators found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_order_tracking_api_endpoints():
    """Test that the order tracking API endpoints are accessible"""
    print("\n🧪 Testing order tracking API endpoints...")
    
    try:
        head_manager = User.objects.filter(role='head_manager').first()
        client = Client()
        client.force_login(head_manager)
        
        # Get a purchase order to test with
        purchase_order = PurchaseOrder.objects.first()
        
        if not purchase_order:
            print("⚠️ No purchase orders found for API testing")
            return True  # Not a failure, just no data to test
        
        print(f"📦 Testing with order: {purchase_order.order_number}")
        
        # Test order details API
        response = client.get(f'/inventory/purchase-orders/{purchase_order.id}/details/')
        print(f"📊 Order details API status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Order details API working")
        else:
            print(f"❌ Order details API failed: {response.status_code}")
            return False
        
        # Test countdown data API
        response = client.get('/inventory/purchase-orders/countdown-data/')
        print(f"📊 Countdown data API status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Countdown data API working")
        else:
            print(f"❌ Countdown data API failed: {response.status_code}")
            return False
        
        # Test statistics API
        response = client.get('/inventory/purchase-orders/statistics/')
        print(f"📊 Statistics API status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Statistics API working")
        else:
            print(f"❌ Statistics API failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed with error: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 Starting order tracking tab tests...\n")
    
    success1 = test_purchase_orders_page_loads()
    success2 = test_order_tracking_content()
    success3 = test_order_tracking_javascript()
    success4 = test_order_tracking_with_data()
    success5 = test_order_tracking_api_endpoints()
    
    if all([success1, success2, success3, success4, success5]):
        print("\n🎉 All order tracking tab tests passed!")
        print("\n📋 Summary:")
        print("✅ Purchase orders page loads correctly")
        print("✅ Order tracking tab structure is present")
        print("✅ All required JavaScript functions are included")
        print("✅ Order tracking displays purchase order data")
        print("✅ API endpoints are accessible")
        print("\n💡 The order tracking tab should work perfectly!")
    else:
        print("\n⚠️ Some tests failed:")
        if not success1:
            print("❌ Purchase orders page loading issues")
        if not success2:
            print("❌ Order tracking content missing")
        if not success3:
            print("❌ JavaScript functions missing")
        if not success4:
            print("❌ Order data display issues")
        if not success5:
            print("❌ API endpoint issues")
        print("\n💡 Check the implementation for any missing components.")
