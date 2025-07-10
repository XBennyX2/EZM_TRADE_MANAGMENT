"""
API URL patterns for the notification system.
Separate from main users URLs to avoid duplication.
"""

from django.urls import path
from . import api_views

urlpatterns = [
    # Notification API URLs
    path('notifications/', api_views.get_notifications, name='api_notifications'),
    path('notifications/count/', api_views.get_notification_count, name='api_notification_count'),
    path('notifications/<int:notification_id>/mark-read/', api_views.mark_notification_read, name='api_mark_notification_read'),
    path('notifications/mark-all-read/', api_views.mark_all_notifications_read, name='api_mark_all_notifications_read'),
    path('notifications/trigger-check/', api_views.trigger_notification_check, name='api_trigger_notification_check'),
    path('notifications/stats/', api_views.get_notification_stats, name='api_notification_stats'),
]
