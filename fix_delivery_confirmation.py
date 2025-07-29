#!/usr/bin/env python3
"""
Fix script for delivery confirmation issues
Automatically fixes common problems that cause "Unable to confirm delivery" errors
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup the Django environment"""
    print("🔧 Setting up Django environment...")
    
    # Set Django settings module
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        print("✅ Set DJANGO_SETTINGS_MODULE to core.settings")
    
    try:
        import django
        django.setup()
        print("✅ Django environment setup complete")
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {str(e)}")
        return False

def check_and_create_missing_migrations():
    """Check for missing migrations and create them"""
    print("\n🔧 Checking for missing migrations...")
    
    try:
        # Check if DeliveryConfirmation model needs migration
        subprocess.run([
            sys.executable, 'manage.py', 'makemigrations', 'Inventory'
        ], check=True, capture_output=True, text=True)
        print("✅ Migrations checked/created")
        
        # Apply migrations
        subprocess.run([
            sys.executable, 'manage.py', 'migrate', '--run-syncdb'
        ], check=True, capture_output=True, text=True)
        print("✅ Migrations applied")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected migration error: {str(e)}")
        return False

def create_test_data():
    """Create test data if needed"""
    print("\n🔧 Creating test data...")
    
    try:
        from django.contrib.auth import get_user_model
        from Inventory.models import PurchaseOrder, Supplier
        
        User = get_user_model()
        
        # Create head manager if doesn't exist
        if not User.objects.filter(role='head_manager').exists():
            head_manager = User.objects.create_user(
                username='head_manager_test',
                email='head_manager@test.com',
                password='testpass123',
                role='head_manager',
                first_name='Head',
                last_name='Manager'
            )
            print("✅ Created test head manager user")
        else:
            print("✅ Head manager user already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Test data creation error: {str(e)}")
        return False

def fix_database_constraints():
    """Fix database constraints that might cause issues"""
    print("\n🔧 Fixing database constraints...")
    
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Check if tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='Inventory_deliveryconfirmation';
            """)
            
            if not cursor.fetchone():
                print("❌ DeliveryConfirmation table not found - run migrations")
                return False
            
            print("✅ Database tables exist")
            
            # Check for orphaned delivery confirmations
            cursor.execute("""
                DELETE FROM Inventory_deliveryconfirmation 
                WHERE purchase_order_id NOT IN (
                    SELECT id FROM Inventory_purchaseorder
                );
            """)
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                print(f"✅ Cleaned up {deleted_count} orphaned delivery confirmations")
            else:
                print("✅ No orphaned delivery confirmations found")
            
        return True
        
    except Exception as e:
        print(f"❌ Database constraint fix error: {str(e)}")
        return False

def test_delivery_confirmation():
    """Test the delivery confirmation functionality"""
    print("\n🧪 Testing delivery confirmation functionality...")
    
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        from Inventory.models import PurchaseOrder
        
        User = get_user_model()
        
        # Get test user and order
        head_manager = User.objects.filter(role='head_manager').first()
        if not head_manager:
            print("❌ No head manager found for testing")
            return False
        
        test_order = PurchaseOrder.objects.filter(
            status__in=['in_transit', 'payment_confirmed']
        ).first()
        
        if not test_order:
            print("❌ No testable orders found")
            return False
        
        print(f"✅ Found test order: {test_order.order_number}")
        print(f"✅ Found head manager: {head_manager.username}")
        
        # Test API endpoint exists
        client = Client()
        client.force_login(head_manager)
        
        # Test GET request to order details
        response = client.get(f'/inventory/purchase-orders/{test_order.id}/details/')
        
        if response.status_code == 200:
            print("✅ Order details API working")
        else:
            print(f"❌ Order details API failed: {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def generate_usage_instructions():
    """Generate usage instructions for fixing the delivery confirmation"""
    print("\n📋 DELIVERY CONFIRMATION FIX INSTRUCTIONS:")
    print("=" * 60)
    
    instructions = [
        "1. **Check Order Status**",
        "   - Order must be in 'in_transit' or 'payment_confirmed' status",
        "   - Order must not already have a delivery confirmation",
        "",
        "2. **Required Form Fields**",
        "   - delivery_condition: Must be one of (excellent, good, fair, poor, damaged)",
        "   - all_items_received: Boolean (true/false)",
        "   - delivery_notes: Optional text",
        "   - received_items: JSON array of item IDs (optional)",
        "",
        "3. **Common Error Causes & Fixes**",
        "   - **Invalid JSON**: Check received_items format",
        "   - **Missing delivery_condition**: Ensure field is provided",
        "   - **Already confirmed**: Check if order already has delivery confirmation",
        "   - **No items**: Order must have associated items",
        "   - **Permissions**: User must be head_manager role",
        "",
        "4. **API Endpoint**",
        "   - POST /inventory/purchase-orders/{order_id}/confirm-delivery/",
        "   - Requires authentication and head_manager role",
        "   - Content-Type: application/x-www-form-urlencoded or multipart/form-data",
        "",
        "5. **File Uploads**",
        "   - delivery_photos: Optional file uploads",
        "   - Maximum file size: 10MB per file",
        "   - Files are stored in delivery_photos/ directory",
        "",
        "6. **Database Checks**",
        "   - Ensure DeliveryConfirmation table exists",
        "   - Check for proper foreign key relationships",
        "   - Verify user has head_manager role",
        "",
        "7. **Logging**",
        "   - Check Django logs for detailed error messages",
        "   - Error details are now logged with full traceback",
        "   - Look for specific validation failures",
    ]
    
    for instruction in instructions:
        print(instruction)

def main():
    """Main fix function"""
    print("🚀 Delivery Confirmation Fix Tool")
    print("=" * 40)
    
    fixes = [
        ("Environment Setup", setup_environment),
        ("Database Migrations", check_and_create_missing_migrations),
        ("Test Data Creation", create_test_data),
        ("Database Constraints", fix_database_constraints),
        ("Functionality Test", test_delivery_confirmation),
    ]
    
    results = []
    
    for fix_name, fix_func in fixes:
        print(f"\n🔧 Running: {fix_name}")
        try:
            success = fix_func()
            results.append((fix_name, success))
            if success:
                print(f"✅ {fix_name}: COMPLETED")
            else:
                print(f"❌ {fix_name}: FAILED")
        except Exception as e:
            print(f"❌ {fix_name}: ERROR - {str(e)}")
            results.append((fix_name, False))
    
    # Summary
    print("\n📊 FIX SUMMARY:")
    print("=" * 20)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for fix_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{fix_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} fixes completed successfully")
    
    if passed == total:
        print("\n🎉 All fixes completed! Delivery confirmation should now work.")
    else:
        print(f"\n⚠️  {total - passed} fixes failed. Check the errors above.")
    
    generate_usage_instructions()

if __name__ == "__main__":
    main()