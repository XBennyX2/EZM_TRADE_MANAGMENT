#!/usr/bin/env python3
"""
Comprehensive Delivery Confirmation Diagnostic Tool
Identifies and fixes common issues causing "Unable to confirm delivery" errors
"""

import os
import sys
import traceback
import importlib.util
from pathlib import Path

def check_django_setup():
    """Check if Django is properly configured"""
    print("🔍 Checking Django Setup...")
    
    try:
        import django
        print(f"✅ Django version: {django.get_version()}")
        
        # Check settings module
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE')
        if not settings_module:
            print("❌ DJANGO_SETTINGS_MODULE not set")
            print("💡 Fix: Set DJANGO_SETTINGS_MODULE environment variable")
            return False
        
        print(f"✅ Settings module: {settings_module}")
        
        # Try to setup Django
        django.setup()
        print("✅ Django setup successful")
        return True
        
    except ImportError:
        print("❌ Django not installed")
        print("💡 Fix: pip install django")
        return False
    except Exception as e:
        print(f"❌ Django setup error: {str(e)}")
        return False

def check_imports():
    """Check if all required imports are available"""
    print("\n🔍 Checking Required Imports...")
    
    required_imports = [
        ('django.db', 'transaction'),
        ('django.contrib.auth', 'get_user_model'),
        ('django.core.files.storage', 'default_storage'),
        ('django.core.files.base', 'ContentFile'),
        ('django.utils', 'timezone'),
        ('Inventory.models', ['PurchaseOrder', 'DeliveryConfirmation', 'OrderStatusHistory']),
        ('payments.notification_service', 'supplier_notification_service'),
    ]
    
    all_imports_ok = True
    
    for module_path, items in required_imports:
        try:
            module = importlib.import_module(module_path)
            if isinstance(items, list):
                for item in items:
                    if not hasattr(module, item):
                        print(f"❌ Missing: {module_path}.{item}")
                        all_imports_ok = False
                    else:
                        print(f"✅ Found: {module_path}.{item}")
            else:
                if not hasattr(module, items):
                    print(f"❌ Missing: {module_path}.{items}")
                    all_imports_ok = False
                else:
                    print(f"✅ Found: {module_path}.{items}")
        except ImportError as e:
            print(f"❌ Import error: {module_path} - {str(e)}")
            all_imports_ok = False
    
    return all_imports_ok

def check_database_models():
    """Check if database models are properly configured"""
    print("\n🔍 Checking Database Models...")
    
    try:
        from Inventory.models import PurchaseOrder, DeliveryConfirmation, OrderStatusHistory
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Check if tables exist
        print("Checking model fields...")
        
        # Check PurchaseOrder fields
        po_fields = [f.name for f in PurchaseOrder._meta.get_fields()]
        required_po_fields = ['status', 'items', 'delivered_at', 'confirmed_by', 'delivery_notes']
        
        for field in required_po_fields:
            if field in po_fields:
                print(f"✅ PurchaseOrder.{field}")
            else:
                print(f"❌ Missing PurchaseOrder.{field}")
        
        # Check DeliveryConfirmation model
        dc_fields = [f.name for f in DeliveryConfirmation._meta.get_fields()]
        required_dc_fields = ['purchase_order', 'confirmed_by', 'delivery_condition', 'all_items_received']
        
        for field in required_dc_fields:
            if field in dc_fields:
                print(f"✅ DeliveryConfirmation.{field}")
            else:
                print(f"❌ Missing DeliveryConfirmation.{field}")
                
        return True
        
    except Exception as e:
        print(f"❌ Model check error: {str(e)}")
        traceback.print_exc()
        return False

def check_database_constraints():
    """Check database constraints and relationships"""
    print("\n🔍 Checking Database Constraints...")
    
    try:
        from Inventory.models import PurchaseOrder, DeliveryConfirmation
        from django.db import connection
        
        # Check if we can query the database
        orders_count = PurchaseOrder.objects.count()
        print(f"✅ PurchaseOrder table accessible ({orders_count} records)")
        
        # Check for existing delivery confirmations
        dc_count = DeliveryConfirmation.objects.count()
        print(f"✅ DeliveryConfirmation table accessible ({dc_count} records)")
        
        # Check for orders that can be confirmed
        confirmable_orders = PurchaseOrder.objects.filter(status__in=['in_transit', 'payment_confirmed'])
        print(f"✅ Found {confirmable_orders.count()} orders that can be confirmed")
        
        return True
        
    except Exception as e:
        print(f"❌ Database constraint check error: {str(e)}")
        return False

def check_notification_service():
    """Check if notification service is working"""
    print("\n🔍 Checking Notification Service...")
    
    try:
        from payments.notification_service import supplier_notification_service
        print("✅ Notification service import successful")
        
        # Check if the service has required methods
        if hasattr(supplier_notification_service, 'send_delivery_confirmation_notification'):
            print("✅ send_delivery_confirmation_notification method exists")
        else:
            print("❌ send_delivery_confirmation_notification method missing")
            
        return True
        
    except ImportError as e:
        print(f"❌ Notification service import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Notification service error: {str(e)}")
        return False

def check_file_storage():
    """Check if file storage is working"""
    print("\n🔍 Checking File Storage...")
    
    try:
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        # Test file creation
        test_content = ContentFile(b"test")
        test_path = default_storage.save("test_delivery.txt", test_content)
        print(f"✅ File storage test successful: {test_path}")
        
        # Clean up test file
        if default_storage.exists(test_path):
            default_storage.delete(test_path)
            print("✅ Test file cleaned up")
            
        return True
        
    except Exception as e:
        print(f"❌ File storage error: {str(e)}")
        return False

def test_delivery_confirmation_logic():
    """Test the core delivery confirmation logic"""
    print("\n🔍 Testing Delivery Confirmation Logic...")
    
    try:
        from Inventory.models import PurchaseOrder
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Find a test order
        test_order = PurchaseOrder.objects.filter(status__in=['in_transit', 'payment_confirmed']).first()
        if not test_order:
            print("❌ No test order found in confirmable status")
            return False
        
        print(f"✅ Found test order: {test_order.order_number}")
        
        # Check if order has items
        items_count = test_order.items.count()
        if items_count == 0:
            print("❌ Test order has no items")
            return False
        
        print(f"✅ Test order has {items_count} items")
        
        # Find a head manager user
        head_manager = User.objects.filter(role='head_manager').first()
        if not head_manager:
            print("❌ No head manager user found")
            return False
        
        print(f"✅ Found head manager: {head_manager.username}")
        
        return True
        
    except Exception as e:
        print(f"❌ Logic test error: {str(e)}")
        traceback.print_exc()
        return False

def generate_fixes():
    """Generate fix recommendations"""
    print("\n🔧 RECOMMENDED FIXES:")
    print("=" * 50)
    
    fixes = [
        {
            "issue": "Missing JSON import in order_tracking_views.py",
            "fix": "Add 'import json' to the imports section",
            "file": "Inventory/order_tracking_views.py"
        },
        {
            "issue": "Database transaction rollback on error",
            "fix": "Ensure proper transaction handling with rollback on exceptions",
            "file": "Inventory/order_tracking_views.py"
        },
        {
            "issue": "Better error logging",
            "fix": "Add more detailed error logging to identify specific failure points",
            "file": "Inventory/order_tracking_views.py"
        },
        {
            "issue": "Notification service error handling",
            "fix": "Make notification sending non-blocking to prevent transaction rollback",
            "file": "Inventory/order_tracking_views.py"
        },
        {
            "issue": "File upload validation",
            "fix": "Add proper validation for file uploads before processing",
            "file": "Inventory/order_tracking_views.py"
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"{i}. {fix['issue']}")
        print(f"   Fix: {fix['fix']}")
        print(f"   File: {fix['file']}")
        print()

def main():
    """Main diagnostic function"""
    print("🚀 Delivery Confirmation Diagnostic Tool")
    print("=" * 50)
    
    # Run all checks
    checks = [
        ("Django Setup", check_django_setup),
        ("Required Imports", check_imports),
        ("Database Models", check_database_models),
        ("Database Constraints", check_database_constraints),
        ("Notification Service", check_notification_service),
        ("File Storage", check_file_storage),
        ("Delivery Logic", test_delivery_confirmation_logic),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} check failed: {str(e)}")
            results[check_name] = False
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY:")
    print("=" * 30)
    passed = sum(results.values())
    total = len(results)
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed < total:
        generate_fixes()
    else:
        print("\n🎉 All checks passed! The delivery confirmation should be working.")

if __name__ == "__main__":
    # Try to setup environment
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    
    main()