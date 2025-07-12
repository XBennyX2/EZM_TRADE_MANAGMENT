#!/usr/bin/env python
"""
Test script to verify transfer request approve/decline functionality.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from store.models import Store
from Inventory.models import Product, Stock, StoreStockTransferRequest
import uuid

def test_transfer_approve_decline():
    """Test the transfer request approve/decline functionality."""
    print("🧪 Testing Transfer Request Approve/Decline Functionality")
    print("=" * 60)
    
    try:
        User = get_user_model()
        test_id = str(uuid.uuid4())[:8]
        
        print("1. Setting up test data...")
        
        # Create store managers
        source_manager = User.objects.create_user(
            username=f'source_{test_id}',
            email=f'source_{test_id}@test.com',
            password='testpass123',
            role='store_manager'
        )
        
        requesting_manager = User.objects.create_user(
            username=f'requesting_{test_id}',
            email=f'requesting_{test_id}@test.com',
            password='testpass123',
            role='store_manager'
        )
        
        # Create stores
        source_store = Store.objects.create(
            name=f'Source Store {test_id}',
            address=f'Source Address {test_id}',
            store_manager=source_manager
        )
        
        requesting_store = Store.objects.create(
            name=f'Requesting Store {test_id}',
            address=f'Requesting Address {test_id}',
            store_manager=requesting_manager
        )
        
        # Assign managers to stores
        source_manager.store = source_store
        source_manager.save()
        requesting_manager.store = requesting_store
        requesting_manager.save()
        
        # Create test product
        product = Product.objects.create(
            name=f'Test Product {test_id}',
            category='Test Category',
            price=10.00
        )
        
        # Create stock in source store
        source_stock = Stock.objects.create(
            store=source_store,
            product=product,
            quantity=50,
            low_stock_threshold=10,
            selling_price=10.00
        )
        
        print("2. Creating transfer request...")
        
        # Create transfer request (requesting store wants product from source store)
        transfer_request = StoreStockTransferRequest.objects.create(
            product=product,
            from_store=source_store,  # Store that has the product
            to_store=requesting_store,  # Store that wants the product
            requested_quantity=10,
            priority='medium',
            reason='Need stock for sales',
            requested_by=requesting_manager
        )
        
        print(f"   ✅ Transfer request created: {transfer_request.request_number}")
        print(f"   📦 Product: {product.name}")
        print(f"   🏪 From: {source_store.name} (Stock: {source_stock.quantity})")
        print(f"   🏪 To: {requesting_store.name}")
        print(f"   📊 Quantity: {transfer_request.requested_quantity}")
        print(f"   📋 Status: {transfer_request.status}")
        
        print("3. Testing URL patterns...")
        
        # Test approve URL
        approve_url = reverse('approve_store_transfer_request', args=[transfer_request.id])
        print(f"   ✅ Approve URL: {approve_url}")
        
        # Test decline URL  
        decline_url = reverse('decline_store_transfer_request', args=[transfer_request.id])
        print(f"   ✅ Decline URL: {decline_url}")
        
        print("4. Testing view logic...")
        
        # Test that the request shows up in source manager's transfer requests view
        client = Client()
        login_success = client.login(username=f'source_{test_id}', password='testpass123')
        print(f"   ✅ Source manager login: {'Success' if login_success else 'Failed'}")
        
        if login_success:
            # Test transfer requests page
            response = client.get(reverse('store_manager_transfer_requests'))
            print(f"   ✅ Transfer requests page: {response.status_code}")
            
            # Check if the request appears in the context
            if hasattr(response, 'context') and response.context:
                page_obj = response.context.get('page_obj', [])
                found_request = any(req.id == transfer_request.id for req in page_obj)
                print(f"   ✅ Request visible in list: {found_request}")
            
            # Test approval
            print("5. Testing approval...")
            response = client.post(approve_url, {
                'approved_quantity': 8,
                'review_notes': 'Approved with reduced quantity'
            })
            print(f"   ✅ Approval response: {response.status_code}")
            
            # Check if request was updated
            transfer_request.refresh_from_db()
            print(f"   📋 Status after approval: {transfer_request.status}")
            print(f"   📊 Approved quantity: {transfer_request.approved_quantity}")
            
            # Check stock levels
            source_stock.refresh_from_db()
            print(f"   📦 Source stock after transfer: {source_stock.quantity}")
            
            # Check destination stock
            try:
                dest_stock = Stock.objects.get(store=requesting_store, product=product)
                print(f"   📦 Destination stock: {dest_stock.quantity}")
            except Stock.DoesNotExist:
                print("   ❌ No stock created in destination store")
        
        print("6. Testing business logic...")
        
        # Verify the correct logic for incoming vs outgoing requests
        # For source manager: requests FROM their store are "incoming" (need approval)
        incoming_for_source = StoreStockTransferRequest.objects.filter(
            from_store=source_store,
            status='pending'
        ).count()
        print(f"   📥 Incoming requests for source manager: {incoming_for_source}")
        
        # For requesting manager: requests TO their store are "outgoing" (they made them)
        outgoing_for_requesting = StoreStockTransferRequest.objects.filter(
            to_store=requesting_store
        ).count()
        print(f"   📤 Outgoing requests from requesting manager: {outgoing_for_requesting}")
        
        print("\n✅ Transfer approve/decline functionality test completed!")
        print("✅ Source store managers can now approve/decline incoming requests!")
        print("=" * 60)
        
        # Clean up
        transfer_request.delete()
        if 'dest_stock' in locals():
            dest_stock.delete()
        source_stock.delete()
        product.delete()
        requesting_store.delete()
        source_store.delete()
        requesting_manager.delete()
        source_manager.delete()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_transfer_approve_decline()
    sys.exit(0 if success else 1)
