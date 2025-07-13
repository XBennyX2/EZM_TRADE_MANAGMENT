"""
Order tracking and delivery confirmation views for Head Managers
"""

import json
import logging
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Sum

from .models import PurchaseOrder, PurchaseOrderItem, DeliveryConfirmation, IssueReport, OrderStatusHistory
from payments.notification_service import supplier_notification_service


def is_head_manager(user):
    """Check if user is a head manager"""
    return user.is_authenticated and user.role == 'head_manager'

logger = logging.getLogger(__name__)


@login_required
@user_passes_test(is_head_manager)
def purchase_order_details_api(request, order_id):
    """
    API endpoint to get purchase order details for modals
    """
    try:
        order = get_object_or_404(PurchaseOrder, id=order_id)
        
        # Serialize order data
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'supplier': {
                'id': order.supplier.id,
                'name': order.supplier.name,
                'email': order.supplier.email,
                'phone': order.supplier.phone,
            },
            'total_amount': float(order.total_amount),
            'status': order.status,
            'order_date': order.order_date.isoformat(),
            'expected_delivery_date': order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
            'estimated_delivery_datetime': order.estimated_delivery_datetime.isoformat() if order.estimated_delivery_datetime else None,
            'delivery_countdown_seconds': order.delivery_countdown_seconds,
            'tracking_number': order.tracking_number,
            'items': []
        }
        
        # Add order items
        for item in order.items.all():
            order_data['items'].append({
                'id': item.id,
                'product_name': item.warehouse_product.product_name,
                'quantity_ordered': item.quantity_ordered,
                'quantity_received': item.quantity_received,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price),
                'is_confirmed_received': item.is_confirmed_received,
                'has_issues': item.has_issues,
                'issue_description': item.issue_description,
            })
        
        return JsonResponse(order_data)
        
    except Exception as e:
        logger.error(f"Error fetching order details for {order_id}: {str(e)}")
        return JsonResponse({'error': 'Unable to fetch order details'}, status=500)


@login_required
@user_passes_test(is_head_manager)
def countdown_data_api(request):
    """
    API endpoint to get updated countdown data for all orders
    """
    try:
        orders = PurchaseOrder.objects.filter(
            status__in=['payment_confirmed', 'in_transit']
        ).select_related('supplier')
        
        countdown_data = {
            'orders': [],
            'statistics': {
                'in_transit': 0,
                'overdue': 0,
                'delivered_today': 0,
                'issues_reported': 0,
            }
        }
        
        for order in orders:
            countdown_data['orders'].append({
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'countdown_seconds': order.delivery_countdown_seconds,
                'is_overdue': order.is_overdue,
            })
            
            # Update statistics
            if order.status == 'in_transit':
                countdown_data['statistics']['in_transit'] += 1
            if order.is_overdue:
                countdown_data['statistics']['overdue'] += 1
        
        # Get today's delivered orders
        today = timezone.now().date()
        delivered_today = PurchaseOrder.objects.filter(
            status='delivered',
            delivered_at__date=today
        ).count()
        countdown_data['statistics']['delivered_today'] = delivered_today
        
        # Get orders with issues
        issues_count = PurchaseOrder.objects.filter(
            status='issue_reported'
        ).count()
        countdown_data['statistics']['issues_reported'] = issues_count
        
        return JsonResponse(countdown_data)
        
    except Exception as e:
        logger.error(f"Error fetching countdown data: {str(e)}")
        return JsonResponse({'error': 'Unable to fetch countdown data'}, status=500)


@login_required
@user_passes_test(is_head_manager)
@require_POST
def mark_order_in_transit(request, order_id):
    """
    Mark an order as in transit
    """
    try:
        order = get_object_or_404(PurchaseOrder, id=order_id)
        
        if order.status != 'payment_confirmed':
            return JsonResponse({
                'success': False,
                'message': 'Order must be in payment confirmed status to mark as in transit'
            })
        
        # Get tracking number from request
        data = json.loads(request.body) if request.body else {}
        tracking_number = data.get('tracking_number', '')
        
        with transaction.atomic():
            # Update order status
            previous_status = order.status
            order.mark_in_transit(tracking_number)
            
            # Create status history record
            OrderStatusHistory.objects.create(
                purchase_order=order,
                previous_status=previous_status,
                new_status=order.status,
                changed_by=request.user,
                reason='Marked as in transit by Head Manager',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send notification to supplier
            try:
                supplier_notification_service.send_order_status_change_notification(
                    order, previous_status, order.status, request.user
                )
            except Exception as e:
                logger.error(f"Failed to send status change notification: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Order marked as in transit successfully',
            'new_status': order.status,
            'countdown_seconds': order.delivery_countdown_seconds
        })
        
    except Exception as e:
        logger.error(f"Error marking order {order_id} as in transit: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Unable to update order status'
        }, status=500)


@login_required
@user_passes_test(is_head_manager)
@require_POST
def confirm_delivery(request, order_id):
    """
    Confirm delivery of an order
    """
    try:
        order = get_object_or_404(PurchaseOrder, id=order_id)
        
        if order.status not in ['in_transit', 'payment_confirmed']:
            return JsonResponse({
                'success': False,
                'message': 'Order must be in transit or payment confirmed to confirm delivery'
            })
        
        # Parse form data
        delivery_condition = request.POST.get('delivery_condition')
        all_items_received = request.POST.get('all_items_received') == 'true'
        delivery_notes = request.POST.get('delivery_notes', '')
        received_items = json.loads(request.POST.get('received_items', '[]'))
        
        if not delivery_condition:
            return JsonResponse({
                'success': False,
                'message': 'Delivery condition is required'
            })
        
        with transaction.atomic():
            # Create delivery confirmation
            delivery_confirmation = DeliveryConfirmation.objects.create(
                purchase_order=order,
                confirmed_by=request.user,
                delivery_condition=delivery_condition,
                all_items_received=all_items_received,
                delivery_notes=delivery_notes
            )
            
            # Handle photo uploads
            photos = []
            for i, file in enumerate(request.FILES.getlist('delivery_photos')):
                if file:
                    filename = f"delivery_photos/{order.order_number}_{i}_{file.name}"
                    path = default_storage.save(filename, ContentFile(file.read()))
                    photos.append(path)
            
            if photos:
                delivery_confirmation.delivery_photos = photos
                delivery_confirmation.save()
            
            # Update order items
            for item_id in received_items:
                try:
                    item = PurchaseOrderItem.objects.get(id=item_id, purchase_order=order)
                    item.is_confirmed_received = True
                    item.quantity_received = item.quantity_ordered
                    item.confirmed_at = timezone.now()
                    item.save()
                except PurchaseOrderItem.DoesNotExist:
                    continue
            
            # Update order status
            previous_status = order.status
            order.confirm_delivery(request.user, delivery_notes)
            
            # Create status history record
            OrderStatusHistory.objects.create(
                purchase_order=order,
                previous_status=previous_status,
                new_status=order.status,
                changed_by=request.user,
                reason='Delivery confirmed by Head Manager',
                notes=f"Condition: {delivery_condition}, All items received: {all_items_received}",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send notification to supplier
            try:
                supplier_notification_service.send_delivery_confirmation_notification(delivery_confirmation)
            except Exception as e:
                logger.error(f"Failed to send delivery confirmation notification: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Delivery confirmed successfully',
            'new_status': order.status
        })
        
    except Exception as e:
        logger.error(f"Error confirming delivery for order {order_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Unable to confirm delivery'
        }, status=500)


@login_required
@user_passes_test(is_head_manager)
@require_POST
def report_delivery_issue(request, order_id):
    """
    Report delivery issues for an order
    """
    try:
        order = get_object_or_404(PurchaseOrder, id=order_id)
        
        if order.status not in ['in_transit', 'payment_confirmed']:
            return JsonResponse({
                'success': False,
                'message': 'Can only report issues for orders that are in transit or payment confirmed'
            })
        
        # Parse form data
        issue_type = request.POST.get('issue_type')
        severity = request.POST.get('severity')
        title = request.POST.get('title')
        description = request.POST.get('description')
        affected_items = json.loads(request.POST.get('affected_items', '[]'))
        
        if not all([issue_type, severity, title, description]):
            return JsonResponse({
                'success': False,
                'message': 'All issue fields are required'
            })
        
        with transaction.atomic():
            # Create issue report
            issue_report = IssueReport.objects.create(
                purchase_order=order,
                reported_by=request.user,
                issue_type=issue_type,
                severity=severity,
                title=title,
                description=description
            )
            
            # Handle photo uploads
            photos = []
            for i, file in enumerate(request.FILES.getlist('issue_photos')):
                if file:
                    filename = f"issue_photos/{order.order_number}_{i}_{file.name}"
                    path = default_storage.save(filename, ContentFile(file.read()))
                    photos.append(path)
            
            if photos:
                issue_report.issue_photos = photos
                issue_report.save()
            
            # Add affected items
            for item_id in affected_items:
                try:
                    item = PurchaseOrderItem.objects.get(id=item_id, purchase_order=order)
                    issue_report.affected_items.add(item)
                    item.has_issues = True
                    item.save()
                except PurchaseOrderItem.DoesNotExist:
                    continue
            
            # Update order status
            previous_status = order.status
            order.report_issue(request.user, f"{title}: {description}")
            
            # Create status history record
            OrderStatusHistory.objects.create(
                purchase_order=order,
                previous_status=previous_status,
                new_status=order.status,
                changed_by=request.user,
                reason='Delivery issue reported by Head Manager',
                notes=f"Issue: {title} ({severity} severity)",
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send notification to supplier
            try:
                supplier_notification_service.send_delivery_issue_notification(issue_report)
            except Exception as e:
                logger.error(f"Failed to send delivery issue notification: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Issue reported successfully. Supplier has been notified.',
            'new_status': order.status
        })
        
    except Exception as e:
        logger.error(f"Error reporting issue for order {order_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Unable to report issue'
        }, status=500)


@login_required
@user_passes_test(is_head_manager)
def order_statistics_api(request):
    """
    API endpoint for real-time order statistics
    """
    try:
        stats = {
            'in_transit': PurchaseOrder.objects.filter(status='in_transit').count(),
            'overdue': PurchaseOrder.objects.filter(
                status__in=['payment_confirmed', 'in_transit']
            ).filter(
                Q(expected_delivery_date__lt=timezone.now().date()) |
                Q(shipped_at__lt=timezone.now() - timedelta(hours=168))  # 7 days default
            ).count(),
            'delivered_today': PurchaseOrder.objects.filter(
                status='delivered',
                delivered_at__date=timezone.now().date()
            ).count(),
            'issues_reported': PurchaseOrder.objects.filter(status='issue_reported').count(),
            'total_orders': PurchaseOrder.objects.count(),
        }
        
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"Error fetching order statistics: {str(e)}")
        return JsonResponse({'error': 'Unable to fetch statistics'}, status=500)
