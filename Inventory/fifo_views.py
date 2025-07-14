from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, F, Sum
from django.utils import timezone
from .models import WarehouseProduct, Stock, Product, InventoryMovement
from store.models import Store
import logging

logger = logging.getLogger(__name__)


def is_cashier_or_manager(user):
    """Check if user is a cashier, store manager, or head manager"""
    return user.is_authenticated and user.role in ['cashier', 'store_manager', 'head_manager']


def is_head_manager(user):
    """Check if user is a head manager"""
    return user.is_authenticated and user.role == 'head_manager'


@login_required
@user_passes_test(is_cashier_or_manager)
def fifo_inventory_view(request):
    """
    Display inventory ordered by FIFO (First-In-First-Out) for cashiers and managers
    """
    # Get user's store if they're a cashier or store manager
    user_store = None
    if request.user.role in ['cashier', 'store_manager']:
        try:
            if hasattr(request.user, 'managed_store'):
                user_store = request.user.managed_store
            elif hasattr(request.user, 'store'):
                user_store = request.user.store
        except:
            messages.error(request, 'You are not assigned to any store.')
            return redirect('dashboard')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    stock_status_filter = request.GET.get('stock_status', '')
    
    if user_store:
        # For cashiers and store managers, show store inventory with FIFO info
        store_stock = Stock.objects.filter(store=user_store).select_related('product')
        
        # Apply filters
        if search_query:
            store_stock = store_stock.filter(
                Q(product__name__icontains=search_query) |
                Q(product__category__icontains=search_query)
            )
        
        if category_filter:
            store_stock = store_stock.filter(product__category=category_filter)
        
        if stock_status_filter:
            if stock_status_filter == 'low_stock':
                store_stock = store_stock.filter(quantity__lte=F('low_stock_threshold'))
            elif stock_status_filter == 'out_of_stock':
                store_stock = store_stock.filter(quantity=0)
        
        # Get FIFO information for each product
        inventory_data = []
        for stock in store_stock:
            # Get warehouse product info for FIFO data
            try:
                warehouse_product = WarehouseProduct.objects.get(
                    product_name=stock.product.name,
                    is_active=True
                )
                fifo_info = {
                    'arrival_date': warehouse_product.arrival_date,
                    'batch_number': warehouse_product.batch_number,
                    'warehouse_stock': warehouse_product.quantity_in_stock,
                    'warehouse_location': warehouse_product.warehouse_location,
                }
            except WarehouseProduct.DoesNotExist:
                fifo_info = {
                    'arrival_date': None,
                    'batch_number': 'N/A',
                    'warehouse_stock': 0,
                    'warehouse_location': 'N/A',
                }
            
            inventory_data.append({
                'stock': stock,
                'fifo_info': fifo_info,
                'is_low_stock': stock.quantity <= stock.low_stock_threshold,
                'is_out_of_stock': stock.quantity == 0,
            })
        
        # Sort by arrival date (FIFO)
        inventory_data.sort(key=lambda x: x['fifo_info']['arrival_date'] or timezone.now())
        
        # Pagination
        paginator = Paginator(inventory_data, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get categories for filter dropdown
        categories = Stock.objects.filter(store=user_store).values_list('product__category', flat=True).distinct()
        
        context = {
            'page_obj': page_obj,
            'user_store': user_store,
            'search_query': search_query,
            'category_filter': category_filter,
            'stock_status_filter': stock_status_filter,
            'categories': categories,
            'is_store_view': True,
        }
        
        return render(request, 'inventory/fifo_inventory_view.html', context)
    
    else:
        # For head managers, show warehouse inventory with FIFO ordering
        warehouse_products = WarehouseProduct.get_fifo_ordered_products()
        
        # Apply filters
        if search_query:
            warehouse_products = warehouse_products.filter(
                Q(product_name__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(supplier__name__icontains=search_query)
            )
        
        if category_filter:
            warehouse_products = warehouse_products.filter(category=category_filter)
        
        if stock_status_filter:
            if stock_status_filter == 'low_stock':
                warehouse_products = warehouse_products.filter(quantity_in_stock__lte=F('minimum_stock_level'))
            elif stock_status_filter == 'out_of_stock':
                warehouse_products = warehouse_products.filter(quantity_in_stock=0)
            elif stock_status_filter == 'overstocked':
                warehouse_products = warehouse_products.filter(quantity_in_stock__gte=F('maximum_stock_level'))
        
        # Pagination
        paginator = Paginator(warehouse_products, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get categories for filter dropdown
        categories = WarehouseProduct.objects.values_list('category', flat=True).distinct()
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'category_filter': category_filter,
            'stock_status_filter': stock_status_filter,
            'categories': categories,
            'is_store_view': False,
        }
        
        return render(request, 'inventory/fifo_inventory_view.html', context)


@login_required
@user_passes_test(is_head_manager)
def inventory_movement_history(request, product_id):
    """
    Display movement history for a specific warehouse product
    """
    warehouse_product = get_object_or_404(WarehouseProduct, id=product_id)
    
    # Get all inventory movements for this product
    movements = InventoryMovement.objects.filter(
        warehouse_product=warehouse_product
    ).select_related('created_by', 'purchase_order', 'restock_request').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(movements, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate summary statistics
    total_received = movements.filter(quantity_change__gt=0).aggregate(
        total=Sum('quantity_change')
    )['total'] or 0
    
    total_issued = movements.filter(quantity_change__lt=0).aggregate(
        total=Sum('quantity_change')
    )['total'] or 0
    
    context = {
        'warehouse_product': warehouse_product,
        'page_obj': page_obj,
        'total_received': total_received,
        'total_issued': abs(total_issued),
        'current_stock': warehouse_product.quantity_in_stock,
    }
    
    return render(request, 'inventory/inventory_movement_history.html', context)


@login_required
def get_fifo_product_info(request, product_name):
    """
    API endpoint to get FIFO information for a product
    """
    try:
        # Get warehouse product for FIFO info
        warehouse_product = WarehouseProduct.objects.get(
            product_name=product_name,
            is_active=True
        )
        
        # Get recent movements
        recent_movements = InventoryMovement.objects.filter(
            warehouse_product=warehouse_product
        ).order_by('-created_at')[:5]
        
        movements_data = []
        for movement in recent_movements:
            movements_data.append({
                'date': movement.created_at.strftime('%Y-%m-%d %H:%M'),
                'type': movement.get_movement_type_display(),
                'quantity_change': movement.quantity_change,
                'reason': movement.reason,
                'created_by': movement.created_by.get_full_name() if movement.created_by else 'System'
            })
        
        return JsonResponse({
            'success': True,
            'product_name': warehouse_product.product_name,
            'arrival_date': warehouse_product.arrival_date.strftime('%Y-%m-%d %H:%M') if warehouse_product.arrival_date else None,
            'batch_number': warehouse_product.batch_number,
            'current_stock': warehouse_product.quantity_in_stock,
            'minimum_stock': warehouse_product.minimum_stock_level,
            'supplier': warehouse_product.supplier.name,
            'location': warehouse_product.warehouse_location,
            'stock_status': warehouse_product.stock_status,
            'recent_movements': movements_data
        })
        
    except WarehouseProduct.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found in warehouse'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting FIFO product info for {product_name}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to retrieve product information'
        }, status=500)


@login_required
@user_passes_test(is_head_manager)
def batch_management_view(request):
    """
    View for managing product batches and FIFO ordering
    """
    # Get products grouped by name with multiple batches
    products_with_batches = {}
    warehouse_products = WarehouseProduct.objects.filter(is_active=True).order_by('product_name', 'arrival_date')
    
    for product in warehouse_products:
        if product.product_name not in products_with_batches:
            products_with_batches[product.product_name] = []
        products_with_batches[product.product_name].append(product)
    
    # Filter to show only products with multiple batches or specific search
    search_query = request.GET.get('search', '')
    if search_query:
        filtered_products = {}
        for product_name, batches in products_with_batches.items():
            if search_query.lower() in product_name.lower():
                filtered_products[product_name] = batches
        products_with_batches = filtered_products
    
    context = {
        'products_with_batches': products_with_batches,
        'search_query': search_query,
        'total_products': len(products_with_batches),
    }
    
    return render(request, 'inventory/batch_management_view.html', context)
