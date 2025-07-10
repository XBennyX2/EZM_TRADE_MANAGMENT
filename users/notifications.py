"""
Notification system utilities for EZM Trade Management.
Handles creation, management, and delivery of real-time notifications.
"""

from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Central manager for handling all notification operations.
    """
    
    @staticmethod
    def create_notification(
        notification_type: str,
        title: str,
        message: str,
        target_roles: List[str] = None,
        target_users: List = None,
        priority: str = 'medium',
        action_url: str = '',
        action_text: str = '',
        related_object_type: str = None,
        related_object_id: int = None,
        related_user_id: int = None,
        expires_hours: int = None
    ):
        """
        Create a new system notification.
        """
        from Inventory.models import SystemNotification, NotificationCategory
        
        try:
            # Get or create category
            category_map = {
                'unassigned_store_manager': 'user_management',
                'pending_restock_request': 'requests',
                'pending_transfer_request': 'requests',
                'new_supplier_registration': 'suppliers',
                'request_approved': 'requests',
                'request_rejected': 'requests',
                'low_stock_alert': 'inventory',
                'system_announcement': 'system',
            }
            
            category_name = category_map.get(notification_type, 'general')
            category, created = NotificationCategory.objects.get_or_create(
                name=category_name,
                defaults={
                    'display_name': category_name.replace('_', ' ').title(),
                    'icon': 'bi-bell',
                    'priority': 1
                }
            )
            
            # Calculate expiration
            expires_at = None
            if expires_hours:
                expires_at = timezone.now() + timezone.timedelta(hours=expires_hours)
            
            # Create notification
            notification = SystemNotification.objects.create(
                notification_type=notification_type,
                category=category,
                title=title,
                message=message,
                priority=priority,
                target_roles=target_roles or [],
                action_url=action_url,
                action_text=action_text,
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                related_user_id=related_user_id,
                expires_at=expires_at
            )
            
            # Add specific target users
            if target_users:
                notification.target_users.set(target_users)
            
            logger.info(f"Created notification: {notification.title}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
    
    @staticmethod
    def get_user_notifications(user, include_read=False, limit=50):
        """
        Get notifications for a specific user.
        """
        from Inventory.models import SystemNotification, UserNotificationStatus
        
        try:
            # Get notifications targeted to user's role or specifically to user
            # Filter by role using JSON field lookup or direct user targeting
            from django.db.models import Q
            import json

            # Build role-based query
            role_query = Q()

            # Check if target_roles contains the user's role
            # For SQLite compatibility, we'll check if the role appears in the JSON array
            all_notifications = SystemNotification.objects.filter(is_active=True).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )

            # Filter notifications that target this user's role or user directly
            notifications = []
            for notif in all_notifications:
                if (user.role in notif.target_roles or
                    notif.target_users.filter(id=user.id).exists()):
                    notifications.append(notif)

            # Convert back to queryset for consistency
            if notifications:
                notification_ids = [n.id for n in notifications]
                notifications = SystemNotification.objects.filter(
                    id__in=notification_ids
                ).order_by('-created_at')[:limit]
            else:
                notifications = SystemNotification.objects.none()
            
            # Get user's read status for these notifications
            notification_data = []
            for notification in notifications[:limit]:
                try:
                    status = UserNotificationStatus.objects.get(
                        user=user, 
                        notification=notification
                    )
                    is_read = status.is_read
                    is_dismissed = status.is_dismissed
                except UserNotificationStatus.DoesNotExist:
                    is_read = False
                    is_dismissed = False
                
                # Skip read notifications if not requested
                if not include_read and is_read:
                    continue
                
                # Skip dismissed notifications
                if is_dismissed:
                    continue
                
                notification_data.append({
                    'notification': notification,
                    'is_read': is_read,
                    'is_dismissed': is_dismissed
                })
            
            return notification_data
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    @staticmethod
    def mark_as_read(user, notification_id):
        """
        Mark a notification as read for a user.
        """
        from Inventory.models import SystemNotification, UserNotificationStatus
        
        try:
            notification = SystemNotification.objects.get(id=notification_id)
            status, created = UserNotificationStatus.objects.get_or_create(
                user=user,
                notification=notification
            )
            status.mark_as_read()
            return True
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    @staticmethod
    def mark_all_as_read(user):
        """
        Mark all notifications as read for a user.
        """
        from Inventory.models import UserNotificationStatus
        
        try:
            # Get all unread notifications for user
            unread_notifications = NotificationManager.get_user_notifications(user, include_read=False)
            
            for item in unread_notifications:
                notification = item['notification']
                status, created = UserNotificationStatus.objects.get_or_create(
                    user=user,
                    notification=notification
                )
                status.mark_as_read()
            
            return True
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return False
    
    @staticmethod
    def get_unread_count(user):
        """
        Get count of unread notifications for a user.
        """
        unread_notifications = NotificationManager.get_user_notifications(user, include_read=False)
        return len(unread_notifications)


class NotificationTriggers:
    """
    Specific notification triggers for different events.
    """
    
    @staticmethod
    def check_unassigned_store_managers():
        """
        Check for store managers without store assignments and create notifications.
        """
        from users.models import CustomUser
        from store.models import Store

        try:
            # Find store managers without stores
            unassigned_managers = CustomUser.objects.filter(
                role='store_manager',
                is_active=True
            ).exclude(
                id__in=Store.objects.values_list('store_manager_id', flat=True)
            )

            for manager in unassigned_managers:
                # Check if notification already exists
                from Inventory.models import SystemNotification
                existing = SystemNotification.objects.filter(
                    notification_type='unassigned_store_manager',
                    related_user_id=manager.id,
                    is_active=True
                ).exists()

                if not existing:
                    NotificationManager.create_notification(
                        notification_type='unassigned_store_manager',
                        title=f'Store Manager Needs Assignment',
                        message=f'{manager.get_full_name() or manager.username} is a store manager but has no store assigned.',
                        target_roles=['head_manager', 'admin'],
                        priority='high',
                        action_url=reverse('manage_users'),
                        action_text='Assign Store',
                        related_user_id=manager.id,
                        expires_hours=168  # 1 week
                    )

        except Exception as e:
            logger.error(f"Error checking unassigned store managers: {e}")

    @staticmethod
    def check_empty_stores():
        """
        Check for stores without assigned store managers and create notifications.
        """
        from store.models import Store

        try:
            # Find stores without store managers
            empty_stores = Store.objects.filter(
                store_manager__isnull=True
            )

            for store in empty_stores:
                # Check if notification already exists
                from Inventory.models import SystemNotification
                existing = SystemNotification.objects.filter(
                    notification_type='empty_store',
                    related_object_type='store',
                    related_object_id=store.id,
                    is_active=True
                ).exists()

                if not existing:
                    NotificationManager.create_notification(
                        notification_type='empty_store',
                        title=f'Store Needs Manager Assignment',
                        message=f'{store.name} ({store.location}) has no assigned store manager.',
                        target_roles=['head_manager', 'admin'],
                        priority='high',
                        action_url=reverse('manage_users'),
                        action_text='Assign Manager',
                        related_object_type='store',
                        related_object_id=store.id,
                        expires_hours=168  # 1 week
                    )

        except Exception as e:
            logger.error(f"Error checking empty stores: {e}")

    @staticmethod
    def check_low_stock_alerts():
        """
        Check for products with low stock across all stores and create notifications.
        """
        from Inventory.models import Stock, Product
        from store.models import Store

        try:
            # Define low stock threshold (can be made configurable)
            LOW_STOCK_THRESHOLD = 10

            # Get all stores
            active_stores = Store.objects.all()

            for store in active_stores:
                # Find products with low stock in this store
                low_stock_items = Stock.objects.filter(
                    store=store,
                    quantity__lte=LOW_STOCK_THRESHOLD,
                    quantity__gt=0  # Exclude completely out of stock
                ).select_related('product')

                for stock_item in low_stock_items:
                    # Check if notification already exists for this product/store combination
                    from Inventory.models import SystemNotification
                    existing = SystemNotification.objects.filter(
                        notification_type='low_stock_alert',
                        related_object_type='stock',
                        related_object_id=stock_item.id,
                        is_active=True
                    ).exists()

                    if not existing:
                        NotificationManager.create_notification(
                            notification_type='low_stock_alert',
                            title=f'Low Stock Alert: {stock_item.product.name}',
                            message=f'{stock_item.product.name} is running low in {store.name}. Current stock: {stock_item.quantity} units.',
                            target_roles=['head_manager', 'store_manager'],
                            priority='medium' if stock_item.quantity > 5 else 'high',
                            action_url=f'/inventory/',
                            action_text='Manage Inventory',
                            related_object_type='stock',
                            related_object_id=stock_item.id,
                            expires_hours=48  # 2 days
                        )

        except Exception as e:
            logger.error(f"Error checking low stock alerts: {e}")
    
    @staticmethod
    def notify_pending_restock_request(restock_request):
        """
        Create notification for pending restock request.
        """
        try:
            NotificationManager.create_notification(
                notification_type='pending_restock_request',
                title=f'New Restock Request: {restock_request.product.name}',
                message=f'{restock_request.store.name} requests {restock_request.requested_quantity} units of {restock_request.product.name}',
                target_roles=['head_manager'],
                priority=restock_request.priority,
                action_url=reverse('head_manager_restock_requests'),
                action_text='Review Request',
                related_object_type='restock_request',
                related_object_id=restock_request.id,
                expires_hours=72  # 3 days
            )
        except Exception as e:
            logger.error(f"Error creating restock request notification: {e}")
    
    @staticmethod
    def notify_pending_transfer_request(transfer_request):
        """
        Create notification for pending transfer request.
        """
        try:
            NotificationManager.create_notification(
                notification_type='pending_transfer_request',
                title=f'New Transfer Request: {transfer_request.product.name}',
                message=f'Transfer {transfer_request.requested_quantity} units from {transfer_request.from_store.name} to {transfer_request.to_store.name}',
                target_roles=['head_manager'],
                priority=transfer_request.priority,
                action_url=reverse('head_manager_transfer_requests'),
                action_text='Review Request',
                related_object_type='transfer_request',
                related_object_id=transfer_request.id,
                expires_hours=72  # 3 days
            )
        except Exception as e:
            logger.error(f"Error creating transfer request notification: {e}")
    
    @staticmethod
    def notify_new_supplier_registration(supplier_user):
        """
        Create notification for new supplier registration.
        """
        try:
            NotificationManager.create_notification(
                notification_type='new_supplier_registration',
                title=f'New Supplier Registration',
                message=f'{supplier_user.get_full_name() or supplier_user.username} has completed supplier profile setup',
                target_roles=['head_manager', 'admin'],
                priority='medium',
                action_url='#',  # TODO: Add supplier management URL
                action_text='Review Supplier',
                related_user_id=supplier_user.id,
                expires_hours=168  # 1 week
            )
        except Exception as e:
            logger.error(f"Error creating supplier registration notification: {e}")
    
    @staticmethod
    def notify_request_status_change(request_obj, status, reviewed_by):
        """
        Notify store manager when their request status changes.
        """
        try:
            if hasattr(request_obj, 'store'):
                # Restock request
                store_manager = request_obj.store.store_manager
                product_name = request_obj.product.name
                request_type = 'restock'
            else:
                # Transfer request
                store_manager = request_obj.requested_by
                product_name = request_obj.product.name
                request_type = 'transfer'
            
            if store_manager:
                title = f'Request {status.title()}: {product_name}'
                message = f'Your {request_type} request for {product_name} has been {status} by {reviewed_by.get_full_name() or reviewed_by.username}'
                
                NotificationManager.create_notification(
                    notification_type=f'request_{status}',
                    title=title,
                    message=message,
                    target_users=[store_manager],
                    priority='medium',
                    expires_hours=168  # 1 week
                )
        except Exception as e:
            logger.error(f"Error creating request status notification: {e}")
