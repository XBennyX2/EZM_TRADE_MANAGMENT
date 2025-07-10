#!/usr/bin/env python
"""
Test the complete store manager restock workflow and notification system
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from users.notifications import NotificationManager, NotificationTriggers
from Inventory.models import SystemNotification, RestockRequest, Product, Stock
from store.models import Store

User = get_user_model()

def test_store_manager_restock_submission():
    """Test store manager submitting a restock request"""
    print("📦 Testing Store Manager Restock Request Submission...")
    
    client = Client()
    
    # Login as store manager
    login_success = client.login(username='store_manager1', password='password123')
    if not login_success:
        print("❌ Failed to login as store manager")
        return False
    
    print("✅ Logged in as store_manager1")
    
    # Get store manager's store and a product
    try:
        store_manager = User.objects.get(username='store_manager1')
        store = Store.objects.get(store_manager=store_manager)
        
        # Get a product that exists in the store
        stock_item = Stock.objects.filter(store=store).first()
        if not stock_item:
            print("❌ No stock items found for store manager's store")
            return False
        
        product = stock_item.product
        print(f"📋 Using product: {product.name} from store: {store.name}")
        
        # Count existing restock requests
        initial_requests = RestockRequest.objects.count()
        initial_notifications = SystemNotification.objects.filter(
            notification_type='pending_restock_request'
        ).count()
        
        print(f"📊 Initial restock requests: {initial_requests}")
        print(f"📊 Initial restock notifications: {initial_notifications}")
        
        # Submit restock request
        restock_data = {
            'product_id': product.id,
            'requested_quantity': 25,
            'current_stock': stock_item.quantity,
            'priority': 'medium',
            'reason': 'Running low on inventory for this product'
        }
        
        response = client.post('/users/store-manager/submit-restock-request/', restock_data)
        print(f"📡 Restock submission response: {response.status_code}")
        
        if response.status_code == 302:  # Redirect after successful submission
            # Check if request was created
            new_requests = RestockRequest.objects.count()
            new_notifications = SystemNotification.objects.filter(
                notification_type='pending_restock_request'
            ).count()
            
            print(f"📊 New restock requests: {new_requests}")
            print(f"📊 New restock notifications: {new_notifications}")
            
            if new_requests > initial_requests:
                print("✅ Restock request created successfully")
                
                if new_notifications > initial_notifications:
                    print("✅ Notification created for restock request")
                    return True
                else:
                    print("❌ No notification created for restock request")
                    return False
            else:
                print("❌ Restock request was not created")
                return False
        else:
            print(f"❌ Restock submission failed: {response.content}")
            return False
            
    except Exception as e:
        print(f"❌ Error in restock submission test: {e}")
        return False

def test_head_manager_notification_receipt():
    """Test that head manager receives the notification"""
    print("\n👤 Testing Head Manager Notification Receipt...")
    
    client = Client()
    
    # Login as head manager
    login_success = client.login(username='head_manager_test', password='password123')
    if not login_success:
        print("❌ Failed to login as head manager")
        return False
    
    print("✅ Logged in as head_manager_test")
    
    # Check notifications via API
    response = client.get('/api/notifications/')
    if response.status_code == 200:
        data = response.json()
        notifications = data.get('notifications', [])
        unread_count = data.get('unread_count', 0)
        
        print(f"📊 Total notifications: {len(notifications)}")
        print(f"📊 Unread count: {unread_count}")
        
        # Look for restock request notifications
        restock_notifications = [
            n for n in notifications 
            if n['notification']['notification_type'] == 'pending_restock_request'
        ]
        
        print(f"📦 Restock request notifications: {len(restock_notifications)}")
        
        if restock_notifications:
            for notif in restock_notifications:
                print(f"   📋 {notif['notification']['title']}")
                print(f"   📝 {notif['notification']['message']}")
                print(f"   📖 Read: {notif['is_read']}")
            return True
        else:
            print("❌ No restock request notifications found")
            return False
    else:
        print(f"❌ Failed to get notifications: {response.status_code}")
        return False

def test_notification_triggers():
    """Test all notification triggers"""
    print("\n🔔 Testing All Notification Triggers...")
    
    try:
        # Test unassigned store managers
        print("👥 Checking unassigned store managers...")
        NotificationTriggers.check_unassigned_store_managers()
        
        # Test empty stores
        print("🏪 Checking empty stores...")
        NotificationTriggers.check_empty_stores()
        
        # Test low stock alerts
        print("📦 Checking low stock alerts...")
        NotificationTriggers.check_low_stock_alerts()
        
        print("✅ All notification triggers executed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error in notification triggers: {e}")
        return False

def test_notification_counts():
    """Test notification counts for different user roles"""
    print("\n📊 Testing Notification Counts by Role...")
    
    test_users = [
        ('head_manager_test', 'head_manager'),
        ('store_manager1', 'store_manager'),
    ]
    
    for username, expected_role in test_users:
        try:
            user = User.objects.get(username=username)
            notifications = NotificationManager.get_user_notifications(user, include_read=False)
            unread_count = NotificationManager.get_unread_count(user)
            
            print(f"👤 {username} ({user.role}):")
            print(f"   📊 Unread notifications: {len(notifications)}")
            print(f"   📊 Unread count: {unread_count}")
            
            # Show notification types
            notification_types = {}
            for item in notifications:
                try:
                    notif = item['notification']
                    notif_type = notif['notification_type']
                    notification_types[notif_type] = notification_types.get(notif_type, 0) + 1
                except (KeyError, TypeError) as e:
                    print(f"   ❌ Error processing notification: {e}")
                    continue

            for notif_type, count in notification_types.items():
                print(f"   📋 {notif_type}: {count}")
                
        except User.DoesNotExist:
            print(f"❌ User {username} not found")
        except Exception as e:
            print(f"❌ Error testing {username}: {e}")

def test_mark_as_read_functionality():
    """Test marking notifications as read"""
    print("\n✅ Testing Mark as Read Functionality...")
    
    client = Client()
    login_success = client.login(username='head_manager_test', password='password123')
    
    if login_success:
        # Get current unread count
        response = client.get('/api/notifications/')
        if response.status_code == 200:
            data = response.json()
            initial_count = data.get('unread_count', 0)
            notifications = data.get('notifications', [])
            
            print(f"📊 Initial unread count: {initial_count}")
            
            if notifications:
                # Mark first notification as read
                first_notif_id = notifications[0]['notification']['id']
                mark_response = client.post(f'/api/notifications/{first_notif_id}/mark-read/')
                
                if mark_response.status_code == 200:
                    print("✅ Successfully marked notification as read")
                    
                    # Check updated count
                    updated_response = client.get('/api/notifications/')
                    if updated_response.status_code == 200:
                        updated_data = updated_response.json()
                        new_count = updated_data.get('unread_count', 0)
                        print(f"📊 Updated unread count: {new_count}")
                        
                        if new_count < initial_count:
                            print("✅ Unread count decreased correctly")
                            return True
                        else:
                            print("❌ Unread count did not decrease")
                            return False
                else:
                    print(f"❌ Failed to mark as read: {mark_response.status_code}")
                    return False
            else:
                print("❌ No notifications to mark as read")
                return False
        else:
            print("❌ Failed to get initial notifications")
            return False
    else:
        print("❌ Failed to login for mark as read test")
        return False

def main():
    """Run complete workflow test"""
    print("🚀 EZM Store Manager Restock Workflow Test")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Restock Submission", test_store_manager_restock_submission()))
    results.append(("Head Manager Receipt", test_head_manager_notification_receipt()))
    results.append(("Notification Triggers", test_notification_triggers()))
    results.append(("Mark as Read", test_mark_as_read_functionality()))
    
    test_notification_counts()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Notification system is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")

if __name__ == '__main__':
    main()
