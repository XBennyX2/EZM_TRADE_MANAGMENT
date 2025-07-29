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
    logger.info(f"Checking if user {user.username} is head manager. Role: {user.role}")
    return user.is_authenticated and user.role == 'head_manager'

logger = logging.getLogger(__name__)


@login_required
@user_passes_test(is_head_manager)
def order_tracking_dashboard(request):
    """
    Order tracking dashboard for Head Managers
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    supplier_filter = request.GET.get('supplier', '')
    search_query = request.GET.get('search', '')

    # Base queryset
    orders = PurchaseOrder.objects.all().select_related('supplier', 'created_by')

    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    if supplier_filter:
        orders = orders.filter(supplier_id=supplier_filter)
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(supplier__name__icontains=search_query) |
            Q(payment_reference__icontains=search_query)
        )

    # Order by most recent
    orders = orders.order_by('-created_date')

    # Get statistics
    stats = {
        'total_orders': PurchaseOrder.objects.count(),
        'payment_confirmed': PurchaseOrder.objects.filter(status='payment_confirmed').count(),
        'in_transit': PurchaseOrder.objects.filter(status='in_transit').count(),
        'delivered': PurchaseOrder.objects.filter(status='delivered').count(),
        'issues_reported': PurchaseOrder.objects.filter(status='issue_reported').count(),
    }

    # Get suppliers for filter dropdown
    from Inventory.models import Supplier
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')

    context = {
        'orders': orders,
        'stats': stats,
        'suppliers': suppliers,
        'status_filter': status_filter,
        'supplier_filter': supplier_filter,
        'search_query': search_query,
        'page_title': 'Order Tracking Dashboard'
    }

    return render(request, 'inventory/order_tracking_dashboard.html', context)


@login_required
@user_passes_test(is_head_manager)
def order_tracking_detail(request, order_id):
    """
    Detailed view of a specific order for tracking
    """
    order = get_object_or_404(PurchaseOrder, id=order_id)

    # Get order history
    status_history = OrderStatusHistory.objects.filter(
        purchase_order=order
    ).order_by('-changed_at')

    # Get delivery confirmation if exists
    delivery_confirmation = None
    try:
        delivery_confirmation = DeliveryConfirmation.objects.get(purchase_order=order)
    except DeliveryConfirmation.DoesNotExist:
        pass

    # Get issue reports if any
    issue_reports = IssueReport.objects.filter(purchase_order=order).order_by('-reported_at')

    context = {
        'order': order,
        'status_history': status_history,
        'delivery_confirmation': delivery_confirmation,
        'issue_reports': issue_reports,
        'page_title': f'Order Tracking - {order.order_number}'
    }

    return render(request, 'inventory/order_tracking_detail.html', context)


@login_required
def purchase_order_details_api(request, order_id):
    """
    API endpoint to get purchase order details for modals
    """
    logger.info(f"purchase_order_details_api called with order_id: {order_id}, user: {request.user.username}, role: {request.user.role}")

    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            logger.error(f"Unauthenticated user attempted to access order details")
            return JsonResponse({'error': 'Authentication required'}, status=401)

        # Check if user is head manager
        if not is_head_manager(request.user):
            logger.warning(f"User {request.user.username} (role: {request.user.role}) attempted to access order details but is not a head manager")
            return JsonResponse({'error': 'Access denied. Head Manager role required.'}, status=403)

        logger.info(f"Fetching order details for order_id: {order_id}")

        try:
            order = get_object_or_404(PurchaseOrder, id=order_id)
            logger.info(f"Found order: {order.order_number}")
        except Exception as e:
            logger.error(f"Order {order_id} not found: {str(e)}")
            return JsonResponse({'error': f'Order not found: {str(e)}'}, status=404)

        # Serialize order data with error handling
        try:
            order_data = {
                'id': order.id,
                'order_number': order.order_number,
                'supplier': {
                    'id': order.supplier.id if order.supplier else None,
                    'name': order.supplier.name if order.supplier else 'Unknown',
                    'email': order.supplier.email if order.supplier else '',
                    'phone': order.supplier.phone if order.supplier else '',
                },
                'total_amount': float(order.total_amount) if order.total_amount else 0.0,
                'status': order.status,
                'order_date': order.order_date.isoformat() if order.order_date else None,
                'expected_delivery_date': order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
                'estimated_delivery_datetime': order.estimated_delivery_datetime.isoformat() if order.estimated_delivery_datetime else None,
                'delivery_countdown_seconds': order.delivery_countdown_seconds if hasattr(order, 'delivery_countdown_seconds') else 0,
                'tracking_number': order.tracking_number or '',
                'items': []
            }
            logger.info(f"Successfully created order_data with id: {order_data['id']}")
        except Exception as serialization_error:
            logger.error(f"Error serializing order data: {str(serialization_error)}")
            return JsonResponse({'error': f'Error serializing order data: {str(serialization_error)}'}, status=500)

        # Add order items
        try:
            items_count = order.items.count()
            logger.info(f"Processing {items_count} items")

            if items_count == 0:
                logger.warning(f"Order {order.order_number} has no items")

            for item in order.items.all():
                try:
                    item_data = {
                        'id': item.id,
                        'product_name': item.warehouse_product.product_name if item.warehouse_product else 'Unknown Product',
                        'quantity_ordered': item.quantity_ordered or 0,
                        'quantity_received': item.quantity_received or 0,
                        'unit_price': float(item.unit_price) if item.unit_price else 0.0,
                        'total_price': float(item.total_price) if item.total_price else 0.0,
                        'is_confirmed_received': getattr(item, 'is_confirmed_received', False),
                        'has_issues': getattr(item, 'has_issues', False),
                        'issue_description': getattr(item, 'issue_description', ''),
                    }
                    order_data['items'].append(item_data)
                    logger.debug(f"Successfully processed item {item.id}")
                except Exception as item_error:
                    logger.error(f"Error processing item {item.id}: {str(item_error)}")
                    # Continue processing other items

        except Exception as items_error:
            logger.error(f"Error processing items for order {order.id}: {str(items_error)}")
            # Continue with empty items list

        logger.info(f"Successfully serialized order data for {order.order_number} with {len(order_data['items'])} items")
        logger.info(f"Final order_data keys: {list(order_data.keys())}")
        logger.info(f"Order ID in response: {order_data.get('id')}")

        return JsonResponse(order_data)

    except Exception as e:
        logger.error(f"Error fetching order details for {order_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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

        if not is_head_manager(request.user):
            return JsonResponse({
                'success': False,
                'message': 'Only head managers can mark orders as in transit'
            }, status=403)
            
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

        logger.info(f"Attempting to confirm delivery for order {order_id} by user {request.user.username}")
        
        # Validate order status
        if order.status not in ['in_transit', 'payment_confirmed']:
            logger.warning(f"Order {order_id} has invalid status for delivery confirmation: {order.status}")
            status_display = order.get_status_display() if hasattr(order, 'get_status_display') else order.status
            return JsonResponse({
                'success': False,
                'message': f'Cannot confirm delivery for order with status "{status_display}". Order must be in transit or payment confirmed.'
            })
        
        # Check if delivery is already confirmed
        if hasattr(order, 'delivery_confirmation') and order.delivery_confirmation:
            logger.warning(f"Order {order_id} already has delivery confirmation")
            confirmed_by = order.delivery_confirmation.confirmed_by.get_full_name() if order.delivery_confirmation.confirmed_by else "Unknown"
            confirmed_at = order.delivery_confirmation.confirmed_at.strftime('%Y-%m-%d %H:%M') if order.delivery_confirmation.confirmed_at else "Unknown time"
            return JsonResponse({
                'success': False,
                'message': f'Delivery was already confirmed by {confirmed_by} on {confirmed_at}.'
            })
        
        # Parse and validate form data
        try:
            delivery_condition = request.POST.get('delivery_condition')
            all_items_received = request.POST.get('all_items_received') == 'true'
            delivery_notes = request.POST.get('delivery_notes', '')
            received_items_str = request.POST.get('received_items', '[]')
            
            # Safely parse JSON
            try:
                received_items = json.loads(received_items_str) if received_items_str else []
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in received_items: {received_items_str}, error: {str(e)}")
                received_items = []
            
        except Exception as e:
            logger.error(f"Error parsing form data for order {order_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid form data provided. Please refresh the page and try again.'
            })
        
        # Validate required fields
        if not delivery_condition:
            logger.warning(f"Missing delivery condition for order {order_id}")
            return JsonResponse({
                'success': False,
                'message': 'Please select a delivery condition to proceed with confirmation.'
            })
        
        # Validate delivery condition choice
        valid_conditions = ['excellent', 'good', 'fair', 'poor', 'damaged']
        if delivery_condition not in valid_conditions:
            logger.warning(f"Invalid delivery condition '{delivery_condition}' for order {order_id}")
            return JsonResponse({
                'success': False,
                'message': f'Please select a valid delivery condition: {", ".join(valid_conditions)}'
            })
        
        with transaction.atomic():
            try:
                # Create delivery confirmation
                logger.info(f"Creating delivery confirmation for order {order_id}")
                delivery_confirmation = DeliveryConfirmation.objects.create(
                    purchase_order=order,
                    confirmed_by=request.user,
                    delivery_condition=delivery_condition,
                    all_items_received=all_items_received,
                    delivery_notes=delivery_notes
                )
                
                # Handle photo uploads
                photos = []
                try:
                    for i, file in enumerate(request.FILES.getlist('delivery_photos')):
                        if file:
                            # Validate file
                            if file.size > 10 * 1024 * 1024:  # 10MB limit
                                logger.warning(f"File {file.name} too large ({file.size} bytes)")
                                continue
                            
                            filename = f"delivery_photos/{order.order_number}_{i}_{file.name}"
                            path = default_storage.save(filename, ContentFile(file.read()))
                            photos.append(path)
                            logger.info(f"Saved delivery photo: {path}")
                    
                    if photos:
                        delivery_confirmation.delivery_photos = photos
                        delivery_confirmation.save()
                        logger.info(f"Saved {len(photos)} delivery photos for order {order_id}")
                        
                except Exception as e:
                    logger.error(f"Error handling photo uploads for order {order_id}: {str(e)}")
                    # Continue without photos rather than failing the entire operation
                
                # Update order items and warehouse stock
                order_items = order.items.all()
                items_count = order_items.count()
                
                if items_count == 0:
                    logger.warning(f"Order {order_id} has no items to confirm")
                    # Instead of failing, we'll allow confirmation but skip item processing
                    # This handles cases where orders exist but items weren't properly created
                    logger.info(f"Confirming order {order_id} without items - marking as delivered")
                    
                    # Update order status directly since there are no items to process
                    previous_status = order.status
                    try:
                        order.confirm_delivery(request.user, delivery_notes)
                        logger.info(f"Order {order_id} status updated from {previous_status} to {order.status}")
                    except Exception as status_error:
                        logger.error(f"Failed to update order status for order {order_id}: {str(status_error)}")
                        raise
                    
                    # Create status history record
                    try:
                        OrderStatusHistory.objects.create(
                            purchase_order=order,
                            previous_status=previous_status,
                            new_status=order.status,
                            changed_by=request.user,
                            reason='Delivery confirmed by Head Manager (no items)',
                            notes=f"Condition: {delivery_condition}, All items received: {all_items_received}",
                            ip_address=request.META.get('REMOTE_ADDR'),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                        logger.info(f"Created status history record for order {order_id}")
                    except Exception as history_error:
                        logger.error(f"Failed to create status history for order {order_id}: {str(history_error)}")
                        # Continue without status history rather than failing
                    
                    # Send notification to supplier (outside transaction to avoid rollback on notification failure)
                    try:
                        supplier_notification_service.send_delivery_confirmation_notification(delivery_confirmation)
                        logger.info(f"Delivery confirmation notification sent for order {order_id}")
                    except Exception as notification_error:
                        logger.error(f"Failed to send delivery confirmation notification for order {order_id}: {str(notification_error)}")
                        # Don't fail the entire operation for notification errors
                    
                    logger.info(f"Successfully confirmed delivery for order {order_id} (no items)")
                    return JsonResponse({
                        'success': True,
                        'message': 'Delivery confirmed successfully (order had no items)',
                        'new_status': order.status
                    })

                logger.info(f"Processing {items_count} items for order {order_id}")
                
                processed_items = 0
                error_items = 0
                
                for item in order_items:
                    try:
                        # Determine if this item was received
                        item_was_received = str(item.id) in received_items if received_items else all_items_received
                        logger.debug(f"Item {item.id}: received={item_was_received}")

                        if item_was_received:
                            # Only update if not already confirmed to avoid double-counting
                            if not item.is_confirmed_received:
                                # Calculate quantity to add to warehouse stock
                                quantity_to_add = item.quantity_ordered - item.quantity_received

                                # Update item status
                                item.is_confirmed_received = True
                                item.quantity_received = item.quantity_ordered
                                item.confirmed_at = timezone.now()
                                item.save()

                                # Update warehouse stock for received items
                                warehouse_product = item.warehouse_product
                                if warehouse_product and quantity_to_add > 0:
                                    try:
                                        warehouse_product.update_stock(
                                            quantity_to_add,
                                            f"Purchase order delivery - {order.order_number}",
                                            movement_type='purchase_delivery',
                                            purchase_order=order
                                        )
                                        logger.info(f"Updated warehouse stock for {warehouse_product.product_name}: +{quantity_to_add} (Total received: {item.quantity_received})")
                                    except Exception as stock_error:
                                        logger.error(f"Failed to update warehouse stock for item {item.id}: {str(stock_error)}")
                                        # Continue processing other items
                                        
                                processed_items += 1
                            else:
                                logger.info(f"Item {item.warehouse_product.product_name} already confirmed, skipping stock update")
                        else:
                            # Item not received - mark as having issues if not already marked
                            if not item.has_issues:
                                item.has_issues = True
                                item.issue_description = "Item not received during delivery confirmation"
                                item.save()
                                logger.info(f"Marked item {item.warehouse_product.product_name} as having delivery issues")

                    except Exception as item_error:
                        logger.error(f"Error processing item {item.id}: {str(item_error)}")
                        error_items += 1
                        continue
                
                # Validate that all items have been processed correctly
                total_items = order.items.count()
                confirmed_items = order.items.filter(is_confirmed_received=True).count()
                items_with_issues = order.items.filter(has_issues=True).count()

                logger.info(f"Delivery confirmation summary for order {order.order_number}: "
                           f"Total items: {total_items}, Confirmed: {confirmed_items}, "
                           f"With issues: {items_with_issues}, Processed: {processed_items}, Errors: {error_items}")

                # Update order status
                previous_status = order.status
                try:
                    order.confirm_delivery(request.user, delivery_notes)
                    logger.info(f"Order {order_id} status updated from {previous_status} to {order.status}")
                except Exception as status_error:
                    logger.error(f"Failed to update order status for order {order_id}: {str(status_error)}")
                    raise
                
                # Create status history record
                try:
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
                    logger.info(f"Created status history record for order {order_id}")
                except Exception as history_error:
                    logger.error(f"Failed to create status history for order {order_id}: {str(history_error)}")
                    # Continue without status history rather than failing
                
            except Exception as transaction_error:
                logger.error(f"Transaction error for order {order_id}: {str(transaction_error)}")
                raise
        
        # Send notification to supplier (outside transaction to avoid rollback on notification failure)
        try:
            supplier_notification_service.send_delivery_confirmation_notification(delivery_confirmation)
            logger.info(f"Delivery confirmation notification sent for order {order_id}")
        except Exception as notification_error:
            logger.error(f"Failed to send delivery confirmation notification for order {order_id}: {str(notification_error)}")
            # Don't fail the entire operation for notification errors
        
        logger.info(f"Successfully confirmed delivery for order {order_id}")
        return JsonResponse({
            'success': True,
            'message': 'Delivery confirmed successfully',
            'new_status': order.status
        })
        
    except PurchaseOrder.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return JsonResponse({
            'success': False,
            'message': 'Order not found'
        }, status=404)
        
    except ValueError as ve:
        logger.error(f"Validation error for order {order_id}: {str(ve)}")
        return JsonResponse({
            'success': False,
            'message': str(ve)
        }, status=400)
        
    except Exception as e:
        logger.error(f"Unexpected error confirming delivery for order {order_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': 'Unable to confirm delivery due to a system error. Please try again or contact support if the problem persists.'
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
