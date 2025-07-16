from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import RestockRequest, WarehouseProduct, Stock
from users.notifications import NotificationManager
import logging

logger = logging.getLogger(__name__)


def is_head_manager(user):
    """Check if user is a head manager"""
    return user.is_authenticated and user.role == 'head_manager'


def is_store_manager(user):
    """Check if user is a store manager"""
    return user.is_authenticated and user.role == 'store_manager'


@login_required
@user_passes_test(is_head_manager)
@require_POST
def ship_restock_request(request, request_id):
    """
    Mark a restock request as shipped and update warehouse stock
    """
    try:
        restock_request = get_object_or_404(RestockRequest, id=request_id, status='approved')
        
        shipped_quantity = int(request.POST.get('shipped_quantity', restock_request.approved_quantity))
        tracking_number = request.POST.get('tracking_number', '').strip()
        
        if shipped_quantity <= 0:
            return JsonResponse({'error': 'Shipped quantity must be greater than 0'}, status=400)
        
        if shipped_quantity > restock_request.approved_quantity:
            return JsonResponse({
                'error': f'Shipped quantity cannot exceed approved quantity ({restock_request.approved_quantity})'
            }, status=400)
        
        with transaction.atomic():
            # Use the ship method which handles warehouse stock updates
            restock_request.ship(
                shipped_by=request.user,
                shipped_quantity=shipped_quantity,
                tracking_number=tracking_number
            )
            
            # Create notification for store manager
            NotificationManager.create_notification(
                notification_type='request_approved',
                title=f'Restock Request Shipped: {restock_request.product.name}',
                message=f'Your restock request has been shipped. Quantity: {shipped_quantity} units. Tracking: {tracking_number or "N/A"}',
                target_users=[restock_request.requested_by],
                priority='medium',
                related_object_type='restock_request',
                related_object_id=restock_request.id
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Restock request shipped successfully. Warehouse stock updated.',
            'new_status': restock_request.status,
            'shipped_quantity': shipped_quantity,
            'tracking_number': tracking_number
        })
        
    except ValueError:
        return JsonResponse({'error': 'Invalid shipped quantity'}, status=400)
    except Exception as e:
        logger.error(f"Error shipping restock request {request_id}: {str(e)}")
        return JsonResponse({'error': 'Unable to ship restock request'}, status=500)


@login_required
@user_passes_test(is_store_manager)
@require_POST
def receive_restock_request(request, request_id):
    """
    Mark a restock request as received and update store stock
    """
    try:
        restock_request = get_object_or_404(
            RestockRequest, 
            id=request_id, 
            status='shipped',
            requested_by=request.user
        )
        
        received_quantity = int(request.POST.get('received_quantity', restock_request.shipped_quantity))
        receiving_notes = request.POST.get('receiving_notes', '').strip()
        
        if received_quantity <= 0:
            return JsonResponse({'error': 'Received quantity must be greater than 0'}, status=400)
        
        if received_quantity > restock_request.shipped_quantity:
            return JsonResponse({
                'error': f'Received quantity cannot exceed shipped quantity ({restock_request.shipped_quantity})'
            }, status=400)
        
        with transaction.atomic():
            # Use the receive method which handles store stock updates
            restock_request.receive(
                received_by=request.user,
                received_quantity=received_quantity,
                notes=receiving_notes
            )
            
            # Create notification for head manager if there's a discrepancy
            if received_quantity < restock_request.shipped_quantity:
                NotificationManager.create_notification(
                    notification_type='low_stock_alert',
                    title=f'Restock Delivery Discrepancy: {restock_request.product.name}',
                    message=f'Store received {received_quantity} units but {restock_request.shipped_quantity} were shipped. Store: {restock_request.store.name}',
                    target_roles=['head_manager'],
                    priority='high',
                    related_object_type='restock_request',
                    related_object_id=restock_request.id
                )
        
        return JsonResponse({
            'success': True,
            'message': f'Restock request received successfully. Store stock updated.',
            'new_status': restock_request.status,
            'received_quantity': received_quantity
        })
        
    except ValueError:
        return JsonResponse({'error': 'Invalid received quantity'}, status=400)
    except Exception as e:
        logger.error(f"Error receiving restock request {request_id}: {str(e)}")
        return JsonResponse({'error': 'Unable to receive restock request'}, status=500)


@login_required
@user_passes_test(is_head_manager)
def restock_workflow_dashboard(request):
    """
    Dashboard for Head Managers to manage restock request workflow
    """
    # Get restock requests by status
    pending_requests = RestockRequest.objects.filter(status='pending').select_related(
        'store', 'product', 'requested_by'
    ).order_by('-requested_date')
    
    approved_requests = RestockRequest.objects.filter(status='approved').select_related(
        'store', 'product', 'requested_by', 'reviewed_by'
    ).order_by('-reviewed_date')
    
    shipped_requests = RestockRequest.objects.filter(status='shipped').select_related(
        'store', 'product', 'requested_by', 'shipped_by'
    ).order_by('-shipped_date')
    
    received_requests = RestockRequest.objects.filter(status='received').select_related(
        'store', 'product', 'requested_by', 'received_by'
    ).order_by('-received_date')
    
    # Get summary statistics
    total_pending = pending_requests.count()
    total_approved = approved_requests.count()
    total_shipped = shipped_requests.count()
    total_received = received_requests.count()
    
    context = {
        'pending_requests': pending_requests[:10],  # Show latest 10
        'approved_requests': approved_requests[:10],
        'shipped_requests': shipped_requests[:10],
        'received_requests': received_requests[:10],
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_shipped': total_shipped,
        'total_received': total_received,
    }
    
    return render(request, 'inventory/restock_workflow_dashboard.html', context)


@login_required
@user_passes_test(is_store_manager)
def store_restock_tracking(request):
    """
    Store Manager view for tracking their restock requests
    """
    try:
        store = request.user.managed_store
    except:
        messages.error(request, 'You are not assigned to manage any store.')
        return redirect('dashboard')
    
    # Get restock requests for this store
    restock_requests = RestockRequest.objects.filter(store=store).select_related(
        'product', 'requested_by', 'reviewed_by', 'shipped_by', 'received_by'
    ).order_by('-requested_date')
    
    # Filter by status if requested
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        restock_requests = restock_requests.filter(status=status_filter)
    
    # Get summary statistics
    pending_count = RestockRequest.objects.filter(store=store, status='pending').count()
    approved_count = RestockRequest.objects.filter(store=store, status='approved').count()
    shipped_count = RestockRequest.objects.filter(store=store, status='shipped').count()
    received_count = RestockRequest.objects.filter(store=store, status='received').count()
    
    context = {
        'store': store,
        'restock_requests': restock_requests,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'shipped_count': shipped_count,
        'received_count': received_count,
    }
    
    return render(request, 'inventory/store_restock_tracking.html', context)


@login_required
def get_warehouse_stock_info(request, product_name):
    """
    API endpoint to get warehouse stock information for a product
    """
    try:
        warehouse_product = WarehouseProduct.objects.get(
            product_name=product_name,
            is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'product_name': warehouse_product.product_name,
            'current_stock': warehouse_product.quantity_in_stock,
            'minimum_stock': warehouse_product.minimum_stock_level,
            'maximum_stock': warehouse_product.maximum_stock_level,
            'supplier': warehouse_product.supplier.name,
            'location': warehouse_product.warehouse_location,
            'is_low_stock': warehouse_product.is_low_stock,
            'stock_status': warehouse_product.stock_status
        })
        
    except WarehouseProduct.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found in warehouse'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting warehouse stock info for {product_name}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to retrieve stock information'
        }, status=500)
