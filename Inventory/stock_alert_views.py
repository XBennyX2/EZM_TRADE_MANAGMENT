from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, F
from .models import WarehouseProduct, Stock
from users.notifications import NotificationManager


def is_store_manager_or_head_manager(user):
    """Check if user is a store manager or head manager"""
    return user.is_authenticated and user.role in ['store_manager', 'head_manager']


def is_head_manager(user):
    """Check if user is a head manager"""
    return user.is_authenticated and user.role == 'head_manager'


def is_store_manager(user):
    """Check if user is a store manager"""
    return user.is_authenticated and user.role == 'store_manager'


@login_required
@user_passes_test(is_store_manager_or_head_manager)
def stock_alerts_dashboard(request):
    """Dashboard showing low stock alerts and threshold management"""

    # Check if user is a store manager
    if request.user.role == 'store_manager':
        # For store managers, show store-specific stock alerts
        try:
            from store.models import Store
            store = Store.objects.get(store_manager=request.user)

            # Get low stock products from the store
            from Inventory.models import Stock
            from django.db.models import F

            low_stock_products = Stock.objects.filter(
                store=store,
                quantity__lte=F('low_stock_threshold')
            ).select_related('product').order_by('quantity')

            # Get search and filter parameters
            search_query = request.GET.get('search', '')
            category_filter = request.GET.get('category', '')
            filter_type = request.GET.get('filter', '')

            # Apply filters
            if search_query:
                low_stock_products = low_stock_products.filter(
                    Q(product__name__icontains=search_query) |
                    Q(product__category__icontains=search_query)
                )

            if category_filter:
                low_stock_products = low_stock_products.filter(product__category=category_filter)

            # Apply specific filter types
            if filter_type == 'low_stock':
                # Show only items that are low stock but not out of stock
                low_stock_products = low_stock_products.filter(
                    quantity__gt=0,
                    quantity__lte=F('low_stock_threshold')
                )
            elif filter_type == 'out_of_stock':
                # Show only out of stock items
                low_stock_products = low_stock_products.filter(quantity=0)
            elif filter_type == 'critical':
                # Show only critical stock (≤5 units)
                low_stock_products = low_stock_products.filter(quantity__lte=5)

            # Pagination
            paginator = Paginator(low_stock_products, 20)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            # Get categories for filter dropdown (exclude null/empty categories)
            categories = Stock.objects.filter(
                store=store,
                product__category__isnull=False,
                product__category__gt=''
            ).values_list('product__category', flat=True).distinct().order_by('product__category')

            # Get summary statistics
            total_low_stock = Stock.objects.filter(
                store=store,
                quantity__lte=F('low_stock_threshold')
            ).count()
            out_of_stock = Stock.objects.filter(store=store, quantity=0).count()
            critical_stock = Stock.objects.filter(
                store=store,
                quantity__lte=5
            ).count()

            context = {
                'page_obj': page_obj,
                'search_query': search_query,
                'category_filter': category_filter,
                'filter_type': filter_type,
                'categories': categories,
                'total_low_stock': total_low_stock,
                'out_of_stock': out_of_stock,
                'critical_stock': critical_stock,
                'is_store_manager': True,
                'store': store,
            }

            return render(request, 'inventory/store_stock_alerts_dashboard.html', context)

        except Store.DoesNotExist:
            messages.error(request, "You are not assigned to manage any store.")
            return redirect('store_manager_page')

    else:
        # For head managers, show warehouse stock alerts
        low_stock_products = WarehouseProduct.get_low_stock_products()

        # Get search and filter parameters
        search_query = request.GET.get('search', '')
        category_filter = request.GET.get('category', '')

        # Apply filters
        if search_query:
            low_stock_products = low_stock_products.filter(
                Q(product_name__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(supplier__name__icontains=search_query)
            )

        if category_filter:
            low_stock_products = low_stock_products.filter(category=category_filter)

        # Pagination
        paginator = Paginator(low_stock_products, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Get categories for filter dropdown (exclude null/empty categories)
        categories = WarehouseProduct.objects.filter(
            category__isnull=False,
            category__gt=''
        ).values_list('category', flat=True).distinct().order_by('category')

        # Get summary statistics
        total_low_stock = WarehouseProduct.get_low_stock_products().count()
        out_of_stock = WarehouseProduct.objects.filter(quantity_in_stock=0, is_active=True).count()
        critical_stock = WarehouseProduct.objects.filter(
            quantity_in_stock__lte=5,
            is_active=True
        ).count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
        'total_low_stock': total_low_stock,
        'out_of_stock': out_of_stock,
        'critical_stock': critical_stock,
    }
    
    return render(request, 'inventory/stock_alerts_dashboard.html', context)


@login_required
@user_passes_test(is_store_manager_or_head_manager)
def update_stock_threshold(request, product_id):
    """Update minimum stock threshold for a product"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        product = get_object_or_404(WarehouseProduct, id=product_id)
        new_threshold = int(request.POST.get('threshold', 0))
        
        if new_threshold < 0:
            return JsonResponse({'error': 'Threshold must be non-negative'}, status=400)
        
        if new_threshold > product.maximum_stock_level:
            return JsonResponse({
                'error': f'Threshold cannot exceed maximum stock level ({product.maximum_stock_level})'
            }, status=400)
        
        old_threshold = product.minimum_stock_level
        product.minimum_stock_level = new_threshold
        product.save()
        
        # Log the change
        messages.success(
            request,
            f'Updated minimum stock threshold for {product.product_name} '
            f'from {old_threshold} to {new_threshold}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Threshold updated successfully',
            'old_threshold': old_threshold,
            'new_threshold': new_threshold
        })
        
    except ValueError:
        return JsonResponse({'error': 'Invalid threshold value'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_store_manager_or_head_manager)
def bulk_update_thresholds(request):
    """Bulk update stock thresholds by category"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        category = request.POST.get('category')
        threshold = int(request.POST.get('threshold', 0))
        
        if not category:
            return JsonResponse({'error': 'Category is required'}, status=400)
        
        if threshold < 0:
            return JsonResponse({'error': 'Threshold must be non-negative'}, status=400)
        
        # Update all products in the category
        with transaction.atomic():
            updated_count = WarehouseProduct.objects.filter(
                category=category,
                is_active=True
            ).update(minimum_stock_level=threshold)
        
        messages.success(
            request,
            f'Updated minimum stock threshold to {threshold} for {updated_count} '
            f'{category} products'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Updated {updated_count} products',
            'updated_count': updated_count
        })
        
    except ValueError:
        return JsonResponse({'error': 'Invalid threshold value'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_head_manager)
def warehouse_inventory_overview(request):
    """Head Manager view of complete warehouse inventory with FIFO ordering"""
    
    # Get all active warehouse products ordered by FIFO
    products = WarehouseProduct.get_fifo_ordered_products()
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    stock_status_filter = request.GET.get('stock_status', '')
    
    # Apply filters
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(category=category_filter)
    
    if stock_status_filter:
        if stock_status_filter == 'low_stock':
            products = products.filter(quantity_in_stock__lte=F('minimum_stock_level'))
        elif stock_status_filter == 'out_of_stock':
            products = products.filter(quantity_in_stock=0)
        elif stock_status_filter == 'overstocked':
            products = products.filter(quantity_in_stock__gte=F('maximum_stock_level'))
    
    # Pagination
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown (exclude null/empty categories)
    categories = WarehouseProduct.objects.filter(
        category__isnull=False,
        category__gt=''
    ).values_list('category', flat=True).distinct().order_by('category')
    
    # Get summary statistics
    total_products = WarehouseProduct.objects.filter(is_active=True).count()
    total_value = sum(p.quantity_in_stock * p.unit_price for p in WarehouseProduct.objects.filter(is_active=True))
    low_stock_count = WarehouseProduct.get_low_stock_products().count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'stock_status_filter': stock_status_filter,
        'categories': categories,
        'total_products': total_products,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
    }
    
    return render(request, 'inventory/warehouse_inventory_overview.html', context)


@login_required
@user_passes_test(is_store_manager)
def store_inventory_view(request):
    """Store Manager view of their store's inventory with restock request integration"""
    
    # Get the store manager's store
    try:
        store = request.user.managed_store
    except:
        messages.error(request, 'You are not assigned to manage any store.')
        return redirect('dashboard')
    
    # Get store stock with related product information
    store_stock = Stock.objects.filter(store=store).select_related('product')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    # Apply filters
    if search_query:
        store_stock = store_stock.filter(
            Q(product__name__icontains=search_query) |
            Q(product__category__icontains=search_query)
        )
    
    if category_filter:
        store_stock = store_stock.filter(product__category=category_filter)
    
    # Pagination
    paginator = Paginator(store_stock, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown (exclude null/empty categories)
    categories = Stock.objects.filter(
        store=store,
        product__category__isnull=False,
        product__category__gt=''
    ).values_list('product__category', flat=True).distinct().order_by('product__category')
    
    # Get summary statistics
    total_items = store_stock.count()
    low_stock_items = store_stock.filter(quantity__lte=F('low_stock_threshold')).count()
    out_of_stock_items = store_stock.filter(quantity=0).count()
    
    context = {
        'store': store,
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
    }
    
    return render(request, 'inventory/store_inventory_view.html', context)
