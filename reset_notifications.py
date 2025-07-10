#!/usr/bin/env python
"""
Reset notifications and create fresh unread ones for testing
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.notifications import NotificationManager, NotificationTriggers
from Inventory.models import SystemNotification, UserNotificationStatus

User = get_user_model()

def reset_notification_status():
    """Reset all notifications to unread status"""
    print("🔄 Resetting notification read status...")
    
    # Delete all UserNotificationStatus records to make everything unread
    deleted_count = UserNotificationStatus.objects.all().delete()[0]
    print(f"✅ Reset {deleted_count} notification statuses to unread")

def create_fresh_notifications():
    """Create fresh notifications for testing"""
    print("🔔 Creating fresh notifications...")
    
    # Create a variety of notifications
    notifications_created = []
    
    # 1. System announcement
    notif1 = NotificationManager.create_notification(
        notification_type='system_announcement',
        title='System Maintenance Scheduled',
        message='The EZM Trade Management system will undergo maintenance on Sunday at 2 AM.',
        target_roles=['head_manager', 'admin', 'store_manager'],
        priority='medium',
        action_url='/admin/',
        action_text='View Details',
        expires_hours=72
    )
    if notif1:
        notifications_created.append(notif1)
    
    # 2. Low stock alert
    notif2 = NotificationManager.create_notification(
        notification_type='low_stock_alert',
        title='Low Stock Alert: Product ABC',
        message='Product ABC is running low in Downtown Store. Current stock: 5 units.',
        target_roles=['head_manager', 'store_manager'],
        priority='high',
        action_url='/inventory/',
        action_text='Manage Inventory',
        expires_hours=48
    )
    if notif2:
        notifications_created.append(notif2)
    
    # 3. Pending request notification
    notif3 = NotificationManager.create_notification(
        notification_type='pending_restock_request',
        title='New Restock Request: Office Supplies',
        message='Mall Store requests 50 units of office supplies for restocking.',
        target_roles=['head_manager'],
        priority='medium',
        action_url='/users/head-manager/restock-requests/',
        action_text='Review Request',
        expires_hours=72
    )
    if notif3:
        notifications_created.append(notif3)
    
    print(f"✅ Created {len(notifications_created)} fresh notifications")
    return notifications_created

def trigger_existing_checks():
    """Trigger existing notification checks"""
    print("🔍 Triggering notification checks...")
    
    try:
        NotificationTriggers.check_unassigned_store_managers()
        print("✅ Checked for unassigned store managers")
    except Exception as e:
        print(f"❌ Error checking unassigned store managers: {e}")

def test_user_notifications():
    """Test notification retrieval for different users"""
    print("👤 Testing notification retrieval...")
    
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
            
            for item in notifications[:2]:  # Show first 2
                notif = item['notification']
                print(f"   📋 {notif.title}")
                
        except User.DoesNotExist:
            print(f"❌ User {username} not found")
        except Exception as e:
            print(f"❌ Error testing {username}: {e}")

def main():
    """Run notification reset and testing"""
    print("🚀 EZM Notification System Reset & Test")
    print("=" * 50)
    
    reset_notification_status()
    create_fresh_notifications()
    trigger_existing_checks()
    test_user_notifications()
    
    print("\n" + "=" * 50)
    print("✅ Notification reset complete!")
    print("\n🎯 Next Steps:")
    print("1. Login as head_manager_test / password123")
    print("2. Check the notification bell - should show badge count")
    print("3. Click the bell to see notifications in dropdown")
    print("4. Test mark-as-read functionality")

if __name__ == '__main__':
    main()
