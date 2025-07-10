#!/usr/bin/env python
"""
Debug script to investigate notification dropdown display issues
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from users.notifications import NotificationManager
from Inventory.models import SystemNotification, UserNotificationStatus

User = get_user_model()

def debug_api_response():
    """Debug the API response structure"""
    print("🔍 Debugging API Response Structure...")
    
    client = Client()
    login_success = client.login(username='head_manager_test', password='password123')
    
    if not login_success:
        print("❌ Failed to login")
        return
    
    print("✅ Logged in successfully")
    
    # Test API endpoint
    response = client.get('/api/notifications/')
    print(f"📡 API Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📊 Response Keys: {list(data.keys())}")
        print(f"📊 Success: {data.get('success')}")
        print(f"📊 Unread Count: {data.get('unread_count')}")
        print(f"📊 Notifications Length: {len(data.get('notifications', []))}")
        
        # Check first notification structure
        notifications = data.get('notifications', [])
        if notifications:
            first_notif = notifications[0]
            print(f"\n📋 First Notification Structure:")
            print(f"   Keys: {list(first_notif.keys())}")
            print(f"   Notification Keys: {list(first_notif.get('notification', {}).keys())}")
            print(f"   Title: {first_notif.get('notification', {}).get('title')}")
            print(f"   Message: {first_notif.get('notification', {}).get('message')}")
            print(f"   Is Read: {first_notif.get('is_read')}")
        else:
            print("❌ No notifications in response")
    else:
        print(f"❌ API Error: {response.content}")

def debug_database_state():
    """Debug the database state"""
    print("\n🗄️ Debugging Database State...")
    
    # Check SystemNotification table
    total_notifications = SystemNotification.objects.count()
    active_notifications = SystemNotification.objects.filter(is_active=True).count()
    print(f"📊 Total Notifications: {total_notifications}")
    print(f"📊 Active Notifications: {active_notifications}")
    
    # Check specific notifications
    recent_notifications = SystemNotification.objects.filter(is_active=True).order_by('-created_at')[:5]
    print(f"\n📋 Recent Active Notifications:")
    for notif in recent_notifications:
        print(f"   ID: {notif.id} | Type: {notif.notification_type} | Title: {notif.title}")
        print(f"   Target Roles: {notif.target_roles}")
        print(f"   Expires: {notif.expires_at}")
        print(f"   ---")

def debug_user_notifications():
    """Debug user-specific notification retrieval"""
    print("\n👤 Debugging User Notification Retrieval...")
    
    try:
        head_manager = User.objects.get(username='head_manager_test')
        print(f"✅ Found user: {head_manager.username} (Role: {head_manager.role})")
        
        # Test NotificationManager directly
        notifications = NotificationManager.get_user_notifications(head_manager, include_read=False)
        unread_count = NotificationManager.get_unread_count(head_manager)
        
        print(f"📊 Direct Manager Call - Notifications: {len(notifications)}")
        print(f"📊 Direct Manager Call - Unread Count: {unread_count}")
        
        # Check UserNotificationStatus
        user_statuses = UserNotificationStatus.objects.filter(user=head_manager)
        print(f"📊 User Notification Statuses: {user_statuses.count()}")
        
        for status in user_statuses[:3]:
            print(f"   Notification: {status.notification.title}")
            print(f"   Read: {status.is_read} | Dismissed: {status.is_dismissed}")
        
    except User.DoesNotExist:
        print("❌ Head manager test user not found")

def debug_javascript_template():
    """Debug the JavaScript template rendering"""
    print("\n🎨 Debugging Template Rendering...")
    
    client = Client()
    login_success = client.login(username='head_manager_test', password='password123')
    
    if login_success:
        # Get head manager dashboard
        response = client.get('/users/head-manager/')
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for notification components
            checks = [
                ('Notification container', 'notification-container' in content),
                ('Notification bell button', 'notificationBell' in content),
                ('Notification badge', 'notificationBadge' in content),
                ('Notification dropdown', 'notification-dropdown' in content),
                ('Notification list', 'notificationList' in content),
                ('Notification template', 'notificationItemTemplate' in content),
                ('JavaScript file', 'notifications.js' in content),
            ]
            
            print("🔍 Template Component Checks:")
            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}")
                
            # Check for specific IDs and classes
            if 'notificationList' in content:
                print("\n📋 Found notification list container")
            else:
                print("\n❌ Missing notification list container")
                
            if 'notificationItemTemplate' in content:
                print("📋 Found notification item template")
            else:
                print("❌ Missing notification item template")
        else:
            print(f"❌ Failed to load dashboard: {response.status_code}")

def debug_css_conflicts():
    """Check for CSS display conflicts"""
    print("\n🎨 Checking for CSS Display Issues...")
    
    client = Client()
    login_success = client.login(username='head_manager_test', password='password123')
    
    if login_success:
        response = client.get('/users/head-manager/')
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Look for potential CSS conflicts
            css_checks = [
                ('Display none on list', 'display: none' in content and 'notificationList' in content),
                ('Hidden class', 'hidden' in content),
                ('Visibility hidden', 'visibility: hidden' in content),
                ('Bootstrap display utilities', 'd-none' in content),
            ]
            
            print("🔍 CSS Conflict Checks:")
            for check_name, result in css_checks:
                status = "⚠️" if result else "✅"
                print(f"   {status} {check_name}")

def main():
    """Run all debugging checks"""
    print("🚀 EZM Notification System Debug Suite")
    print("=" * 60)
    
    debug_api_response()
    debug_database_state()
    debug_user_notifications()
    debug_javascript_template()
    debug_css_conflicts()
    
    print("\n" + "=" * 60)
    print("🔍 Debug Summary Complete")

if __name__ == '__main__':
    main()
