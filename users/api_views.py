"""
API views for the notification system.
Handles AJAX requests for real-time notification updates.
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.urls import reverse
import json
import logging

from .notifications import NotificationManager, NotificationTriggers

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """
    Get notifications for the current user.
    Returns JSON with notifications and unread count.
    """
    try:
        # Get user notifications
        notifications_data = NotificationManager.get_user_notifications(
            user=request.user,
            include_read=False,  # Only unread for dropdown
            limit=20
        )
        
        # Get unread count
        unread_count = NotificationManager.get_unread_count(request.user)
        
        # Format notifications for JSON response
        notifications = []
        for item in notifications_data:
            notification = item['notification']
            
            # Build action URL if available
            action_url = notification.action_url
            if action_url and not action_url.startswith('http'):
                try:
                    # Handle relative URLs
                    if action_url.startswith('/'):
                        action_url = action_url
                    else:
                        action_url = f"/{action_url}"
                except:
                    action_url = '#'
            
            notifications.append({
                'notification': {
                    'id': notification.id,
                    'notification_type': notification.notification_type,
                    'title': notification.title,
                    'message': notification.message,
                    'priority': notification.priority,
                    'action_url': action_url,
                    'action_text': notification.action_text,
                    'created_at': notification.created_at.isoformat(),
                },
                'is_read': item['is_read'],
                'is_dismissed': item['is_dismissed']
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications,
            'unread_count': unread_count,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications for user {request.user.id}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to load notifications'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """
    Mark a specific notification as read for the current user.
    """
    try:
        success = NotificationManager.mark_as_read(request.user, notification_id)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Notification marked as read'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to mark notification as read'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read for user {request.user.id}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to mark notification as read'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """
    Mark all notifications as read for the current user.
    """
    try:
        success = NotificationManager.mark_all_as_read(request.user)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'All notifications marked as read'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to mark all notifications as read'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error marking all notifications as read for user {request.user.id}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to mark all notifications as read'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_notification_count(request):
    """
    Get just the unread notification count for the current user.
    Lightweight endpoint for frequent polling.
    """
    try:
        unread_count = NotificationManager.get_unread_count(request.user)
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting notification count for user {request.user.id}: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get notification count'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def trigger_notification_check(request):
    """
    Manually trigger notification checks for testing purposes.
    Only available to admin and head manager roles.
    """
    if request.user.role not in ['admin', 'head_manager']:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied'
        }, status=403)
    
    try:
        # Trigger various notification checks
        NotificationTriggers.check_unassigned_store_managers()
        
        # Check for pending requests
        from Inventory.models import RestockRequest, StoreStockTransferRequest
        
        pending_restock = RestockRequest.objects.filter(status='pending').count()
        pending_transfer = StoreStockTransferRequest.objects.filter(status='pending').count()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification checks completed',
            'stats': {
                'pending_restock_requests': pending_restock,
                'pending_transfer_requests': pending_transfer,
            }
        })
        
    except Exception as e:
        logger.error(f"Error triggering notification check: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to trigger notification check'
        }, status=500)


def get_notification_stats(request):
    """
    Get notification statistics for admin dashboard.
    """
    if not request.user.is_authenticated or request.user.role not in ['admin', 'head_manager']:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied'
        }, status=403)
    
    try:
        from Inventory.models import SystemNotification, UserNotificationStatus
        from users.models import CustomUser
        from store.models import Store
        from Inventory.models import RestockRequest, StoreStockTransferRequest
        
        # Get various statistics
        stats = {
            'total_notifications': SystemNotification.objects.filter(is_active=True).count(),
            'unread_notifications': UserNotificationStatus.objects.filter(is_read=False).count(),
            'unassigned_store_managers': CustomUser.objects.filter(
                role='store_manager',
                is_active=True
            ).exclude(
                id__in=Store.objects.values_list('store_manager_id', flat=True)
            ).count(),
            'pending_restock_requests': RestockRequest.objects.filter(status='pending').count(),
            'pending_transfer_requests': StoreStockTransferRequest.objects.filter(status='pending').count(),
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get notification statistics'
        }, status=500)
