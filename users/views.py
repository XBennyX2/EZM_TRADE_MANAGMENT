from django.shortcuts import render, redirect
from store.models import StoreCashier, Store
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import CustomLoginForm, EditProfileForm, ChangePasswordForm
from .models import CustomUser
from transactions.models import Transaction, Order, FinancialRecord
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.contrib import messages
from django.http import JsonResponse
from Inventory.models import Product, Stock, WarehouseProduct
from django.db import models
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
logger = logging.getLogger(__name__)
try:
    from users.templatetags.users_utils import send_otp_email
except ImportError as e:
    logger.error(f"Could not import users.templatetags.users_utils: {e}")
    raise
from django.shortcuts import redirect
from django.conf import settings
from django.core.mail import EmailMessage
import threading

class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_otp_email(user):
    subject = "Welcome to EZM Trade — Verify Your Email"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email

    context = {
        'username': user.username,
        'otp': user.otp_code,
    }

    text_content = f"Hi {user.username},\\nWelcome to EZM Trade!\\nYour OTP code is: {user.otp_code}"
    html_content = render_to_string('users/email_otp.html', context)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import login
from .forms import CustomLoginForm
from store.models import Store
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

def login_view(request):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser or user.role == 'admin':
            return redirect('admin_dashboard')
        elif user.role == 'head_manager':
            return redirect('head_manager_page')
        elif user.role == 'store_manager':
            return redirect('store_manager_page')
        elif user.role == 'cashier':
            return redirect('cashier_page')
        elif user.role == 'supplier':
            return redirect('supplier_dashboard')
        else:
            messages.warning(request, "No role assigned. Contact admin.")
            return redirect('login')

    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if not user.is_active:
                messages.error(request, "Your account is inactive. Please contact the administrator.")
                return redirect('login')

            login(request, user)
            if user.is_first_login:
                if user.is_superuser or user.role == 'admin':
                    return redirect('admin_change_password')
                elif user.role == 'head_manager':
                    return redirect('head_manager_settings')
                elif user.role == 'store_manager':
                    return redirect('store_manager_settings')
                elif user.role == 'cashier':
                    return redirect('cashier_settings')
                elif user.role == 'supplier':
                    return redirect('supplier_settings')
            else:
                if user.is_superuser or user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'head_manager':
                    return redirect('head_manager_page')
                elif user.role == 'store_manager':
                    try:
                        store = Store.objects.get(store_manager=user)
                        return redirect('store_manager_page')
                    except Store.DoesNotExist:
                        messages.warning(request, "You are not assigned to manage any store.")
                        return redirect('login')
                elif user.role == 'cashier':
                    return redirect('cashier_page')
                elif user.role == 'supplier':
                    return redirect('supplier_dashboard')
                else:
                    messages.warning(request, "No role assigned. Contact admin.")
                    return redirect('login')
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = CustomLoginForm()

    return render(request, 'users/login.html', {'form': form})

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login')

from django.contrib.auth import get_user_model

User = get_user_model()
@login_required
def admin_dashboard(request):
    # Check if user has admin privileges
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.warning(request, "Access denied. Admin privileges required.")
        return redirect('login')

    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()

    # Exclude current user from the displayed list but keep them in counts
    users = User.objects.exclude(pk=request.user.pk).order_by('-date_joined')[:10]

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'users': users,
    }
    return render(request, 'mainpages/admin_dashboard.html', context)

@login_required
def head_manager_page(request):
    """
    Enhanced Head Manager dashboard with request management and analytics.
    """
    if request.user.role != 'head_manager':
        messages.warning(request, "Access denied. You don't have permission to access this page.")
        return redirect('login')

    from django.db.models import Count, Q
    from Inventory.models import RestockRequest, StoreStockTransferRequest

    stores = Store.objects.all().select_related('store_manager')

    # Request statistics
    pending_restock_requests = RestockRequest.objects.filter(status='pending').count()
    pending_transfer_requests = StoreStockTransferRequest.objects.filter(status='pending').count()

    # Recent requests for quick overview
    recent_restock_requests = RestockRequest.objects.filter(
        status='pending'
    ).select_related('store', 'product', 'requested_by').order_by('-requested_date')[:5]

    recent_transfer_requests = StoreStockTransferRequest.objects.filter(
        status='pending'
    ).select_related('from_store', 'to_store', 'product', 'requested_by').order_by('-requested_date')[:5]

    context = {
        'stores': stores,
        'pending_restock_requests': pending_restock_requests,
        'pending_transfer_requests': pending_transfer_requests,
        'recent_restock_requests': recent_restock_requests,
        'recent_transfer_requests': recent_transfer_requests,
    }

    return render(request, 'mainpages/head_manager_page.html', context)


@login_required
def head_manager_restock_requests(request):
    """
    Head Manager comprehensive view for managing restock requests from all stores.
    Central hub for inventory replenishment management.
    """
    if request.user.role != 'head_manager':
        messages.error(request, "Access denied. Head Manager role required.")
        return redirect('login')

    from Inventory.models import RestockRequest, Product
    from store.models import Store
    from django.core.paginator import Paginator
    from django.db.models import Q, Count

    # Filter options
    status_filter = request.GET.get('status', 'all')
    store_filter = request.GET.get('store', 'all')
    priority_filter = request.GET.get('priority', 'all')
    category_filter = request.GET.get('category', 'all')
    search_query = request.GET.get('search', '')

    # Build query with comprehensive filtering
    requests = RestockRequest.objects.select_related(
        'store', 'product', 'requested_by', 'reviewed_by'
    ).order_by('-requested_date', '-priority')

    # Apply filters
    if status_filter != 'all':
        requests = requests.filter(status=status_filter)
    if store_filter != 'all':
        requests = requests.filter(store_id=store_filter)
    if priority_filter != 'all':
        requests = requests.filter(priority=priority_filter)
    if category_filter != 'all':
        requests = requests.filter(product__category=category_filter)

    # Search functionality
    if search_query:
        requests = requests.filter(
            Q(product__name__icontains=search_query) |
            Q(product__description__icontains=search_query) |
            Q(reason__icontains=search_query) |
            Q(store__name__icontains=search_query) |
            Q(requested_by__username__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(requests, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get comprehensive statistics
    all_requests = RestockRequest.objects.all()
    stats = {
        'total_requests': all_requests.count(),
        'pending_requests': all_requests.filter(status='pending').count(),
        'approved_requests': all_requests.filter(status='approved').count(),
        'rejected_requests': all_requests.filter(status='rejected').count(),
        'urgent_requests': all_requests.filter(priority='urgent', status='pending').count(),
        'high_priority_requests': all_requests.filter(priority='high', status='pending').count(),
    }

    # Get filter options
    stores = Store.objects.filter(store_manager__isnull=False).order_by('name')
    categories = Product.objects.values_list('category', flat=True).distinct().order_by('category')

    # Prepare choices with selection flags for template
    status_choices_with_selection = []
    for value, label in RestockRequest.STATUS_CHOICES:
        status_choices_with_selection.append({
            'value': value,
            'label': label,
            'selected': status_filter == value
        })

    priority_choices_with_selection = []
    for value, label in RestockRequest.PRIORITY_CHOICES:
        priority_choices_with_selection.append({
            'value': value,
            'label': label,
            'selected': priority_filter == value
        })

    store_choices_with_selection = []
    for store in stores:
        store_choices_with_selection.append({
            'id': store.id,
            'name': store.name,
            'selected': str(store_filter) == str(store.id)
        })

    category_choices_with_selection = []
    for category in categories:
        category_choices_with_selection.append({
            'value': category,
            'label': category.replace('_', ' ').title(),
            'selected': category_filter == category
        })

    context = {
        'page_obj': page_obj,
        'stores': stores,
        'categories': categories,
        'status_filter': status_filter,
        'store_filter': store_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'status_choices': status_choices_with_selection,
        'priority_choices': priority_choices_with_selection,
        'store_choices': store_choices_with_selection,
        'category_choices': category_choices_with_selection,
        'status_all_selected': status_filter == 'all',
        'store_all_selected': store_filter == 'all',
        'priority_all_selected': priority_filter == 'all',
        'category_all_selected': category_filter == 'all',
        'stats': stats,
    }

    return render(request, 'mainpages/head_manager_restock_requests.html', context)




@login_required
def approve_restock_request(request, request_id):
    """
    Handle restock request approval by head manager with comprehensive feedback.
    """
    if request.user.role != 'head_manager':
        messages.error(request, "Access denied. Head Manager role required.")
        return redirect('login')

    if request.method == 'POST':
        from Inventory.models import RestockRequest, Stock
        from django.utils import timezone

        try:
            restock_request = RestockRequest.objects.get(id=request_id, status='pending')
            approved_quantity = int(request.POST.get('approved_quantity', restock_request.requested_quantity))
            review_notes = request.POST.get('review_notes', '').strip()

            # Validation
            if approved_quantity <= 0:
                messages.error(request, "Approved quantity must be greater than 0.")
                return redirect('head_manager_restock_requests')

            if approved_quantity > restock_request.requested_quantity * 2:
                messages.warning(request, f"Approved quantity ({approved_quantity}) is significantly higher than requested ({restock_request.requested_quantity}). Please confirm this is intentional.")

            # Use the new approve method which handles notifications and immediate inventory transfer
            restock_request.approve(
                approved_by=request.user,
                approved_quantity=approved_quantity,
                notes=review_notes or f"Approved by {request.user.get_full_name() or request.user.username}"
            )

            # Success message with details
            success_msg = f"✅ Restock request #{restock_request.request_number} approved and inventory transferred! {approved_quantity} units of {restock_request.product.name} have been moved from warehouse to {restock_request.store.name}."
            if approved_quantity != restock_request.requested_quantity:
                success_msg += f" (Originally requested: {restock_request.requested_quantity} units)"
            messages.success(request, success_msg)

        except RestockRequest.DoesNotExist:
            messages.error(request, "Restock request not found or already processed.")
        except ValueError as e:
            # Handle specific inventory-related errors
            messages.error(request, f"Inventory Error: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")

    return redirect('head_manager_restock_requests')


@login_required
def reject_restock_request(request, request_id):
    """
    Handle restock request rejection by head manager with detailed feedback.
    """
    if request.user.role != 'head_manager':
        messages.error(request, "Access denied. Head Manager role required.")
        return redirect('login')

    if request.method == 'POST':
        from Inventory.models import RestockRequest
        from django.utils import timezone

        try:
            restock_request = RestockRequest.objects.get(id=request_id, status='pending')
            review_notes = request.POST.get('review_notes', '').strip()
            rejection_reason = request.POST.get('rejection_reason', '').strip()

            # Require feedback for rejection
            if not review_notes and not rejection_reason:
                messages.error(request, "Please provide a reason for rejecting this request to help the Store Manager understand the decision.")
                return redirect('head_manager_restock_requests')

            # Combine rejection reason and review notes
            feedback_parts = []
            if rejection_reason:
                feedback_parts.append(f"Reason: {rejection_reason}")
            if review_notes:
                feedback_parts.append(f"Notes: {review_notes}")

            combined_notes = " | ".join(feedback_parts) if feedback_parts else f"Rejected by {request.user.get_full_name() or request.user.username}"

            # Use the new reject method which handles notifications
            restock_request.reject(
                rejected_by=request.user,
                notes=combined_notes
            )

            # Success message with details
            messages.success(request, f"Restock request #{restock_request.request_number} for {restock_request.product.name} from {restock_request.store.name} has been rejected. Feedback has been sent to the Store Manager.")

        except RestockRequest.DoesNotExist:
            messages.error(request, "Request not found or already processed.")
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")

    return redirect('head_manager_restock_requests')





@login_required
def store_manager_page(request):
    """
    Enhanced Store Manager dashboard with analytics, stock management, and request functionality.
    """
    if request.user.role != 'store_manager':
        messages.warning(request, "Access denied. Store Manager role required.")
        return redirect('login')

    store = None
    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store. Please contact the administrator.")
        # Render a simple error page instead of redirecting to avoid loops
        return render(request, 'mainpages/store_manager_no_store.html', {
            'user': request.user
        })

    # Get current date for filtering
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Q, F
    from Inventory.models import Stock, Product, RestockRequest, StoreStockTransferRequest

    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)

    # Recent sales and transactions (last 30 days)
    recent_transactions = Transaction.objects.filter(
        store=store,
        transaction_type='sale',
        timestamp__date__gte=last_30_days
    ).order_by('-timestamp')[:10]

    # Sales analytics
    total_sales_30_days = Transaction.objects.filter(
        store=store,
        transaction_type='sale',
        timestamp__date__gte=last_30_days
    ).aggregate(
        total_amount=Sum('total_amount'),
        total_transactions=Count('id')
    )

    total_sales_7_days = Transaction.objects.filter(
        store=store,
        transaction_type='sale',
        timestamp__date__gte=last_7_days
    ).aggregate(
        total_amount=Sum('total_amount'),
        total_transactions=Count('id')
    )

    # Most sold product analytics (based on order quantities)
    most_sold_products = Order.objects.filter(
        transaction__store=store,
        transaction__transaction_type='sale',
        transaction__timestamp__date__gte=last_30_days
    ).values(
        'product__name',
        'product__id'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price_at_time_of_sale'))
    ).order_by('-total_quantity')[:5]

    # Low stock alerts
    low_stock_items = Stock.objects.filter(
        store=store,
        quantity__lte=F('low_stock_threshold')
    ).select_related('product').order_by('quantity')

    # Current stock levels
    current_stock = Stock.objects.filter(store=store).select_related('product').order_by('product__name')

    # Recent requests status
    recent_restock_requests = RestockRequest.objects.filter(
        store=store
    ).order_by('-requested_date')[:5]

    recent_transfer_requests = StoreStockTransferRequest.objects.filter(
        Q(from_store=store) | Q(to_store=store)
    ).order_by('-requested_date')[:5]

    # Pending requests count
    pending_restock_count = RestockRequest.objects.filter(
        store=store,
        status='pending'
    ).count()

    pending_transfer_count = StoreStockTransferRequest.objects.filter(
        Q(from_store=store) | Q(to_store=store),
        status='pending'
    ).count()

    # Cashier assignment
    cashier_assignment = StoreCashier.objects.filter(store=store, is_active=True).first()

    # Get all stores except current store for transfer requests
    other_stores = Store.objects.exclude(id=store.id).order_by('name')

    # Get products available for restock (from warehouse and other stores)
    from Inventory.models import WarehouseProduct, Product
    from django.db import models

    # Get products available in warehouse
    warehouse_product_names = WarehouseProduct.objects.filter(
        quantity_in_stock__gt=0,
        is_active=True
    ).values_list('product_name', flat=True)

    # Get products available in other stores
    other_stores_products = Stock.objects.filter(
        quantity__gt=0
    ).exclude(store=store).values_list('product', flat=True)

    # For restock requests, include ALL products in the system
    # This allows store managers to request any product, whether it's currently
    # in warehouse, other stores, or needs to be ordered from suppliers
    restock_available_products = Product.objects.all().order_by('name')

    context = {
        'store': store,
        'cashier_assignment': cashier_assignment,
        'recent_transactions': recent_transactions,
        'total_sales_30_days': total_sales_30_days,
        'total_sales_7_days': total_sales_7_days,
        'most_sold_products': most_sold_products,
        'low_stock_items': low_stock_items,
        'current_stock': current_stock,
        'restock_available_products': restock_available_products,  # Products for restock dropdown
        'recent_restock_requests': recent_restock_requests,
        'recent_transfer_requests': recent_transfer_requests,
        'pending_restock_count': pending_restock_count,
        'pending_transfer_count': pending_transfer_count,
        'other_stores': other_stores,
    }

    return render(request, 'mainpages/store_manager_page.html', context)


@login_required
def get_restock_products(request):
    """
    API endpoint to get products available for restock requests.
    Returns products from warehouse and other stores.
    """
    if request.user.role != 'store_manager':
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        return JsonResponse({'error': 'Store not found'}, status=404)

    from Inventory.models import Product, Stock, WarehouseProduct
    from django.db import models

    # Get products available in warehouse
    warehouse_product_names = WarehouseProduct.objects.filter(
        quantity_in_stock__gt=0,
        is_active=True
    ).values_list('product_name', flat=True)

    # Get products available in other stores
    other_stores_products = Stock.objects.filter(
        quantity__gt=0
    ).exclude(store=store).values_list('product', flat=True)

    # For restock requests, include ALL products in the system
    # This allows store managers to request any product
    available_products = Product.objects.all().order_by('name').values('id', 'name', 'category', 'price')

    return JsonResponse({
        'products': list(available_products)
    })


@login_required
def get_transfer_products(request):
    """
    API endpoint to get products available for transfer requests.
    Returns products from OTHER stores (excluding warehouse and current store).
    """
    if request.user.role != 'store_manager':
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        return JsonResponse({'error': 'Store not found'}, status=404)

    from Inventory.models import Stock, Product

    # Get products available in OTHER stores (excluding current store)
    # This shows products that can be transferred FROM other stores TO current store
    other_stores_products = Stock.objects.filter(
        quantity__gt=0
    ).exclude(store=store).values_list('product', flat=True).distinct()

    # Get the actual products that are available in other stores
    available_products = Product.objects.filter(
        id__in=other_stores_products
    ).order_by('name').values('id', 'name', 'category', 'price')

    return JsonResponse({
        'products': list(available_products)
    })


@login_required
def get_stores_with_product(request):
    """
    API endpoint to get stores that have a specific product in stock.
    Used for transfer requests - shows which stores can provide the selected product.
    """
    if request.user.role != 'store_manager':
        return JsonResponse({'error': 'Access denied'}, status=403)

    try:
        requesting_store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        return JsonResponse({'error': 'Store not found'}, status=404)

    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse({'error': 'Product ID required'}, status=400)

    from Inventory.models import Stock, Product

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

    # Get stores that have this product in stock (excluding the requesting store)
    stores_with_product = Stock.objects.filter(
        product=product,
        quantity__gt=0
    ).exclude(store=requesting_store).select_related('store')

    # Format the response with store info and available quantity
    available_stores = []
    for stock in stores_with_product:
        available_stores.append({
            'id': stock.store.id,
            'name': stock.store.name,
            'address': stock.store.address,
            'available_quantity': stock.quantity,
            'product_name': product.name
        })

    return JsonResponse({
        'stores': available_stores,
        'product_name': product.name
    })


@login_required
def submit_restock_request(request):
    """
    Handle restock request submission by store managers.
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        from Inventory.models import Product, Stock, RestockRequest

        product_id = request.POST.get('product_id')
        requested_quantity = request.POST.get('requested_quantity')
        priority = request.POST.get('priority', 'medium')
        reason = request.POST.get('reason', '')

        try:
            product = Product.objects.get(id=product_id)
            requested_quantity = int(requested_quantity)

            if requested_quantity <= 0:
                messages.error(request, "Requested quantity must be greater than 0.")
                return redirect('store_manager_page')

            # Check for existing pending requests
            existing_request = RestockRequest.objects.filter(
                store=store,
                product=product,
                status='pending'
            ).first()

            if existing_request:
                messages.warning(request, f"You already have a pending restock request for {product.name}.")
                return redirect('store_manager_page')

            # Get current stock level
            try:
                stock = Stock.objects.get(store=store, product=product)
                current_stock = stock.quantity
            except Stock.DoesNotExist:
                current_stock = 0

            # Create restock request
            restock_request = RestockRequest.objects.create(
                store=store,
                product=product,
                requested_quantity=requested_quantity,
                current_stock=current_stock,
                priority=priority,
                reason=reason,
                requested_by=request.user
            )

            # Trigger notification for head managers
            from .notifications import NotificationTriggers
            NotificationTriggers.notify_pending_restock_request(restock_request)

            messages.success(request, f"Restock request {restock_request.request_number} submitted successfully.")

        except (Product.DoesNotExist, ValueError) as e:
            messages.error(request, "Invalid product or quantity specified.")
        except Exception as e:
            messages.error(request, f"Error submitting restock request: {str(e)}")

    return redirect('store_manager_page')


@login_required
def submit_transfer_request(request):
    """
    Handle stock transfer request submission by store managers.
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        requesting_store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        from Inventory.models import Product, Stock, StoreStockTransferRequest

        product_id = request.POST.get('product_id')
        from_store_id = request.POST.get('to_store_id')  # This is actually the source store
        requested_quantity = request.POST.get('requested_quantity')
        priority = request.POST.get('priority', 'medium')
        reason = request.POST.get('reason', '')

        try:
            product = Product.objects.get(id=product_id)
            from_store = Store.objects.get(id=from_store_id)  # Store that has the product
            requested_quantity = int(requested_quantity)

            if requested_quantity <= 0:
                messages.error(request, "Requested quantity must be greater than 0.")
                return redirect('store_manager_page')

            if requesting_store == from_store:
                messages.error(request, "Cannot transfer from the same store.")
                return redirect('store_manager_page')

            # Check if the source store has the product in stock
            try:
                source_stock = Stock.objects.get(product=product, store=from_store)
                if source_stock.quantity < requested_quantity:
                    messages.error(request, f"Insufficient stock. {from_store.name} only has {source_stock.quantity} units of {product.name}.")
                    return redirect('store_manager_page')
            except Stock.DoesNotExist:
                messages.error(request, f"{product.name} is not available in {from_store.name}.")
                return redirect('store_manager_page')

            # Check for existing pending requests
            existing_request = StoreStockTransferRequest.objects.filter(
                from_store=from_store,
                to_store=requesting_store,
                product=product,
                status='pending'
            ).first()

            if existing_request:
                messages.warning(request, f"You already have a pending transfer request for {product.name} from {from_store.name}.")
                return redirect('store_manager_page')

            # Create transfer request (FROM other store TO current store)
            transfer_request = StoreStockTransferRequest.objects.create(
                product=product,
                from_store=from_store,  # Store that has the product
                to_store=requesting_store,  # Current store (requesting)
                requested_quantity=requested_quantity,
                priority=priority,
                reason=reason,
                requested_by=request.user
            )

            # Trigger notification for head managers
            from .notifications import NotificationTriggers
            NotificationTriggers.notify_pending_transfer_request(transfer_request)

            messages.success(request, f"Transfer request {transfer_request.request_number} submitted successfully.")

        except (Product.DoesNotExist, Store.DoesNotExist, ValueError) as e:
            messages.error(request, "Invalid product, store, or quantity specified.")
        except Exception as e:
            messages.error(request, f"Error submitting transfer request: {str(e)}")

    return redirect('store_manager_page')


@login_required
def update_product_price(request):
    """
    Handle product price updates by store managers.
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        from Inventory.models import Stock

        stock_id = request.POST.get('stock_id')
        new_price = request.POST.get('new_price')

        try:
            stock = Stock.objects.get(id=stock_id, store=store)
            new_price = float(new_price)

            if new_price <= 0:
                messages.error(request, "Price must be greater than 0.")
                return redirect('store_manager_page')

            old_price = stock.selling_price
            stock.selling_price = new_price
            stock.save()

            messages.success(request, f"Price for {stock.product.name} updated from ${old_price} to ${new_price}.")

        except (Stock.DoesNotExist, ValueError) as e:
            messages.error(request, "Invalid stock item or price specified.")
        except Exception as e:
            messages.error(request, f"Error updating price: {str(e)}")

    return redirect('store_manager_page')


@login_required
def store_manager_restock_requests(request):
    """
    Store Manager view for managing their restock requests.
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    from Inventory.models import RestockRequest, Stock
    from django.core.paginator import Paginator

    # Filter options
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    product_filter = request.GET.get('product', '')

    # Build query
    requests = RestockRequest.objects.filter(store=store).select_related(
        'product', 'requested_by', 'reviewed_by'
    ).order_by('-requested_date')

    if status_filter != 'all':
        requests = requests.filter(status=status_filter)
    if priority_filter != 'all':
        requests = requests.filter(priority=priority_filter)
    if product_filter:
        requests = requests.filter(product__name__icontains=product_filter)

    # Pagination
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    all_requests = RestockRequest.objects.filter(store=store)
    stats = {
        'pending_count': all_requests.filter(status='pending').count(),
        'approved_count': all_requests.filter(status='approved').count(),
        'fulfilled_count': all_requests.filter(status='fulfilled').count(),
        'rejected_count': all_requests.filter(status='rejected').count(),
    }

    # Get current stock for the modal
    current_stock = Stock.objects.filter(store=store).select_related('product')

    # Get products available for restock (from warehouse and other stores)
    from Inventory.models import WarehouseProduct, Product
    from django.db import models

    # Get products available in warehouse
    warehouse_product_names = WarehouseProduct.objects.filter(
        quantity_in_stock__gt=0,
        is_active=True
    ).values_list('product_name', flat=True)

    # Get products available in other stores
    other_stores_products = Stock.objects.filter(
        quantity__gt=0
    ).exclude(store=store).values_list('product', flat=True)

    # For restock requests, include ALL products in the system
    # This allows store managers to request any product, whether it's currently
    # in warehouse, other stores, or needs to be ordered from suppliers
    restock_available_products = Product.objects.all().order_by('name')

    # Prepare status choices with selection flags
    status_choices_with_selection = []
    for value, label in RestockRequest.STATUS_CHOICES:
        status_choices_with_selection.append({
            'value': value,
            'label': label,
            'selected': status_filter == value
        })

    # Prepare priority choices with selection flags
    priority_choices_with_selection = []
    for value, label in RestockRequest.PRIORITY_CHOICES:
        priority_choices_with_selection.append({
            'value': value,
            'label': label,
            'selected': priority_filter == value
        })

    # Prepare pagination data with current page info
    pagination_data = []
    if page_obj.has_other_pages:
        for num in page_obj.paginator.page_range:
            pagination_data.append({
                'number': num,
                'is_current': page_obj.number == num,
                'in_range': num > page_obj.number - 3 and num < page_obj.number + 3
            })

    context = {
        'page_obj': page_obj,
        'pagination_data': pagination_data,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'product_filter': product_filter,
        'status_choices': status_choices_with_selection,
        'priority_choices': priority_choices_with_selection,
        'current_stock': current_stock,
        'restock_available_products': restock_available_products,  # Products for restock dropdown
        'status_all_selected': status_filter == 'all' or not status_filter,
        'priority_all_selected': priority_filter == 'all' or not priority_filter,
        **stats
    }

    return render(request, 'mainpages/store_manager_restock_requests.html', context)


@login_required
def store_manager_transfer_requests(request):
    """
    Store Manager view for managing their stock transfer requests.
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    from Inventory.models import StoreStockTransferRequest, Stock
    from django.core.paginator import Paginator

    # Filter options
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    to_store_filter = request.GET.get('to_store', 'all')

    # Build query - show both outgoing (to_store=store) and incoming (from_store=store) requests
    from django.db.models import Q
    requests = StoreStockTransferRequest.objects.filter(
        Q(from_store=store) | Q(to_store=store)
    ).select_related(
        'product', 'from_store', 'to_store', 'requested_by', 'reviewed_by'
    ).order_by('-requested_date')

    if status_filter != 'all':
        requests = requests.filter(status=status_filter)
    if priority_filter != 'all':
        requests = requests.filter(priority=priority_filter)
    if to_store_filter != 'all':
        requests = requests.filter(to_store_id=to_store_filter)

    # Pagination
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics - include both outgoing and incoming requests
    all_requests = StoreStockTransferRequest.objects.filter(
        Q(from_store=store) | Q(to_store=store)
    )
    stats = {
        'pending_count': all_requests.filter(status='pending').count(),
        'approved_count': all_requests.filter(status='approved').count(),
        'completed_count': all_requests.filter(status='completed').count(),
        'rejected_count': all_requests.filter(status='rejected').count(),
    }

    # Get products available in other stores for transfer requests
    # (excluding warehouse and current store)
    other_stores_products = Stock.objects.filter(
        quantity__gt=0
    ).exclude(store=store).values_list('product', flat=True).distinct()

    transfer_available_products = Product.objects.filter(
        id__in=other_stores_products
    ).order_by('name')

    other_stores = Store.objects.exclude(id=store.id)

    # Prepare choices with selected flags
    status_choices_with_selected = []
    for value, label in StoreStockTransferRequest.STATUS_CHOICES:
        status_choices_with_selected.append({
            'value': value,
            'label': label,
            'selected': status_filter == value
        })

    priority_choices_with_selected = []
    for value, label in StoreStockTransferRequest.PRIORITY_CHOICES:
        priority_choices_with_selected.append({
            'value': value,
            'label': label,
            'selected': priority_filter == value
        })

    other_stores_with_selected = []
    for store in other_stores:
        other_stores_with_selected.append({
            'id': store.id,
            'name': store.name,
            'selected': str(to_store_filter) == str(store.id)
        })

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'to_store_filter': to_store_filter,
        'status_choices': status_choices_with_selected,
        'priority_choices': priority_choices_with_selected,
        'transfer_available_products': transfer_available_products,  # Products from other stores
        'other_stores': other_stores_with_selected,
        'status_all_selected': status_filter == 'all',
        'priority_all_selected': priority_filter == 'all',
        'to_store_all_selected': to_store_filter == 'all',
        **stats
    }

    return render(request, 'mainpages/store_manager_transfer_requests.html', context)


@login_required
def store_manager_stock_management(request):
    """
    Store Manager comprehensive stock management view.
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    from store.models import Store
    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    from Inventory.models import Stock, Product, WarehouseProduct
    from django.core.paginator import Paginator
    from django.db.models import Q, F, Case, When, Value, CharField

    # Filter options
    category_filter = request.GET.get('category', 'all')
    stock_level_filter = request.GET.get('stock_level', 'all')
    search_query = request.GET.get('search', '')

    # Build query
    stock_items = Stock.objects.filter(store=store).select_related(
        'product'
    ).annotate(
        stock_status=Case(
            When(quantity=0, then=Value('out_of_stock')),
            When(quantity__lte=F('low_stock_threshold'), then=Value('low_stock')),
            When(quantity__lte=F('low_stock_threshold') * 2, then=Value('medium_stock')),
            default=Value('good_stock'),
            output_field=CharField()
        )
    )

    # Apply filters
    if category_filter and category_filter != 'all':
        stock_items = stock_items.filter(product__category=category_filter)

    if stock_level_filter and stock_level_filter != 'all':
        if stock_level_filter == 'low_stock':
            stock_items = stock_items.filter(quantity__lte=F('low_stock_threshold'), quantity__gt=0)
        elif stock_level_filter == 'out_of_stock':
            stock_items = stock_items.filter(quantity=0)
        elif stock_level_filter == 'good_stock':
            stock_items = stock_items.filter(quantity__gt=F('low_stock_threshold') * 2)

    if search_query:
        stock_items = stock_items.filter(
            Q(product__name__icontains=search_query) |
            Q(product__description__icontains=search_query) |
            Q(product__batch_number__icontains=search_query)
        )

    # Order by stock status (critical first) then by name
    stock_items = stock_items.order_by('quantity', 'product__name')

    # Pagination
    paginator = Paginator(stock_items, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get statistics
    total_products = stock_items.count()
    low_stock_count = Stock.objects.filter(
        store=store,
        quantity__lte=F('low_stock_threshold'),
        quantity__gt=0
    ).count()
    out_of_stock_count = Stock.objects.filter(store=store, quantity=0).count()
    good_stock_count = Stock.objects.filter(
        store=store,
        quantity__gt=F('low_stock_threshold') * 2
    ).count()

    # Get categories for filter
    categories = Product.objects.values_list('category', flat=True).distinct().order_by('category')

    # Prepare category choices with selection flags
    category_choices_with_selection = []
    for category in categories:
        category_choices_with_selection.append({
            'value': category,
            'label': category.replace('_', ' ').title(),
            'selected': category_filter == category
        })

    # Stock level choices
    stock_level_choices = [
        {'value': 'low_stock', 'label': 'Low Stock', 'selected': stock_level_filter == 'low_stock'},
        {'value': 'out_of_stock', 'label': 'Out of Stock', 'selected': stock_level_filter == 'out_of_stock'},
        {'value': 'good_stock', 'label': 'Good Stock', 'selected': stock_level_filter == 'good_stock'},
    ]

    # Get warehouse products for additional info
    warehouse_products = WarehouseProduct.objects.filter(
        product_name__in=[item.product.name for item in page_obj]
    ).select_related('supplier')

    # Create a mapping for quick lookup
    warehouse_product_map = {wp.product_name: wp for wp in warehouse_products}

    # Get other stores for transfer modal
    other_stores = Store.objects.exclude(id=store.id).filter(store_manager__isnull=False)

    # Get products available for restock (from warehouse and other stores)
    from Inventory.models import Product
    from django.db import models

    # Get products available in warehouse
    warehouse_product_names = WarehouseProduct.objects.filter(
        quantity_in_stock__gt=0,
        is_active=True
    ).values_list('product_name', flat=True)

    # Get products available in other stores
    other_stores_products = Stock.objects.filter(
        quantity__gt=0
    ).exclude(store=store).values_list('product', flat=True)

    # For restock requests, include ALL products in the system
    # This allows store managers to request any product, whether it's currently
    # in warehouse, other stores, or needs to be ordered from suppliers
    restock_available_products = Product.objects.all().order_by('name')

    # For transfer requests, show products available in OTHER stores only
    # (excluding warehouse and current store)
    transfer_available_products = Product.objects.filter(
        id__in=other_stores_products
    ).order_by('name')

    context = {
        'page_obj': page_obj,
        'store': store,
        'category_filter': category_filter,
        'stock_level_filter': stock_level_filter,
        'search_query': search_query,
        'category_choices': category_choices_with_selection,
        'stock_level_choices': stock_level_choices,
        'warehouse_product_map': warehouse_product_map,
        'other_stores': other_stores,
        'restock_available_products': restock_available_products,  # Products for restock dropdown
        'transfer_available_products': transfer_available_products,  # Products for transfer dropdown
        'category_all_selected': category_filter == 'all' or not category_filter,
        'stock_level_all_selected': stock_level_filter == 'all' or not stock_level_filter,
        'stats': {
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'good_stock_count': good_stock_count,
        }
    }

    return render(request, 'mainpages/store_manager_stock_management.html', context)


def create_request_notification(notification_type, recipient, title, message, restock_request=None, transfer_request=None):
    """
    Create a notification for request status changes.
    """
    from Inventory.models import RequestNotification

    RequestNotification.objects.create(
        notification_type=notification_type,
        recipient=recipient,
        title=title,
        message=message,
        restock_request=restock_request,
        transfer_request=transfer_request
    )

@login_required
def cashier_page(request):
    """
    Cashier dashboard that checks for store assignment and shows appropriate content
    """
    if request.user.role != 'cashier':
        messages.error(request, "Access denied. Cashier role required.")
        return redirect('login')

    # Check if cashier is assigned to a store
    if not request.user.store:
        # Show waiting message until store manager assigns them
        return render(request, 'mainpages/cashier_waiting.html', {
            'message': 'Please wait for your store manager to assign you to a store.'
        })

    # Cashier is assigned to a store, redirect to the proper dashboard
    return redirect('cashier_dashboard')

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from .forms import ChangeUserRoleForm, CustomUserCreationFormAdmin
from django.core.paginator import Paginator

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

@user_passes_test(is_admin)
def manage_users(request):
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    page_number = request.GET.get('page')

    # Get all users for accurate counts, but exclude current user from display
    all_users = User.objects.all()
    users = User.objects.exclude(pk=request.user.pk)

    if search_query:
        all_users = all_users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    if role_filter:
        all_users = all_users.filter(role=role_filter)
        users = users.filter(role=role_filter)

    paginator = Paginator(users.order_by('username'), 5)
    page_obj = paginator.get_page(page_number)

    context = {
        'users': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'role_filter': role_filter,
        'total_users': all_users.count(),  # Use all_users for accurate count including current user
        'is_admin': role_filter == 'admin',
        'is_head_manager': role_filter == 'head_manager',
        'is_store_manager': role_filter == 'store_manager',
        'is_cashier': role_filter == 'cashier',
        'is_supplier': role_filter == 'supplier',
    }
    logger.debug(f"page_obj: {page_obj}")
    logger.debug(f"page_obj.paginator.page_range: {page_obj.paginator.page_range}")
    return render(request, 'admin/manage_users.html', context)

@user_passes_test(is_admin)
def create_user(request):
    # Get role choices from the CustomUser model
    role_choices = CustomUser.ROLE_CHOICES

    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        phone_number = request.POST.get('phone_number')

        context = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone_number': phone_number,
            'role': role,
            'role_choices': role_choices
        }

        if not all([username, first_name, last_name, email, password, role]):
            messages.error(request, "All required fields must be filled.")
            return render(request, 'admin/create_user.html', context)

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose a different username.")
            return render(request, 'admin/create_user.html', context)

        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email address already exists.")
            return render(request, 'admin/create_user.html', context)

        try:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                role=role,
                phone_number=phone_number,
            )

            # Send welcome email with credentials
            try:
                subject = "Welcome to EZM Trade Management - Account Created"
                message = f"""Dear {user.first_name} {user.last_name},

Your account has been created for EZM Trade Management System.

Login Details:
- Username: {user.username}
- Temporary Password: {password}
- Role: {user.get_role_display()}

Please login at: http://127.0.0.1:8000/users/login/

IMPORTANT: You will be required to change your password on first login for security purposes.

If you have any questions, please contact your administrator.

Best regards,
EZM Trade Management Team"""

                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = [user.email]

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=to_email,
                    fail_silently=False
                )

                messages.success(request, f"User {user.username} created successfully. Welcome email sent to {user.email}.")
            except Exception as email_error:
                messages.warning(request, f"User {user.username} created successfully, but email could not be sent: {email_error}")

            return redirect('manage_users')
        except Exception as e:
            messages.error(request, f"Error creating user: {e}")
            return render(request, 'admin/create_user.html', context)
    else:
        return render(request, 'admin/create_user.html', {'role_choices': role_choices})

@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    target_user.is_active = not target_user.is_active
    target_user.save()
    return redirect('manage_users')

@user_passes_test(is_admin)
def view_user_detail(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    return render(request, 'admin/user_detail.html', {'target_user': target_user})

@user_passes_test(is_admin)
def change_user_role(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = ChangeUserRoleForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = ChangeUserRoleForm(instance=target_user)
    return render(request, 'admin/change_user_role.html', {'form': form, 'target_user': target_user})

@user_passes_test(is_admin)
def delete_user(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    # Prevent admin from deleting themselves
    if target_user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('manage_users')

    # Prevent deletion of superusers by non-superusers
    if target_user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You cannot delete a superuser account.")
        return redirect('manage_users')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User '{username}' has been successfully deleted.")
        return redirect('manage_users')

    return render(request, 'admin/delete_user_confirm.html', {'target_user': target_user})

@login_required
def admin_settings(request):
    if request.user.is_superuser or request.user.role == 'admin':
        return render(request, 'admin/admin_settings.html')
    elif request.user.role == 'head_manager':
        return redirect('head_manager_settings')
    elif request.user.role == 'store_manager':
        return redirect('store_manager_settings')
    elif request.user.role == 'cashier':
        return redirect('cashier_settings')
    else:
        messages.warning(request, "No role assigned. Contact admin.")
        return redirect('login')

@login_required
def admin_edit_profile(request):
    # Check if user has admin privileges
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.warning(request, "Access denied. Admin privileges required.")
        return redirect('login')

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('admin_settings')
        else:
            messages.error(request, 'Error updating profile.')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def admin_change_password(request):
    # Check if user has admin privileges
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.warning(request, "Access denied. Admin privileges required.")
        return redirect('login')

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password1 = form.cleaned_data['new_password1']
            if request.user.check_password(old_password):
                request.user.set_password(new_password1)
                # Mark user as no longer first login after password change
                if request.user.is_first_login:
                    request.user.is_first_login = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')
                return redirect('admin_dashboard')  # Redirect to dashboard after first password change
            else:
                messages.error(request, 'Incorrect old password.')
    else:
        form = ChangePasswordForm()
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def head_manager_settings(request):
    # Check if user has head manager privileges
    if request.user.role != 'head_manager':
        messages.warning(request, "Access denied. Head manager role required.")
        return redirect('login')

    # Show welcome message for first login users, but don't reset the flag yet
    if request.user.is_first_login:
        messages.info(request, "Welcome! Please update your password and profile information.")

    return render(request, 'mainpages/head_manager_settings.html')


@login_required
def head_manager_change_password(request):
    if request.user.role != 'head_manager':
        messages.warning(request, "Access denied. You don't have permission to access this page.")
        return redirect('login')

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password1 = form.cleaned_data['new_password1']
            if request.user.check_password(old_password):
                # Check if this is first login before changing password
                was_first_login = request.user.is_first_login
                request.user.set_password(new_password1)
                # Mark user as no longer first login after password change
                if request.user.is_first_login:
                    request.user.is_first_login = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')
                # Redirect to dashboard if it was first login, otherwise back to settings
                if was_first_login:
                    return redirect('head_manager_page')
                else:
                    return redirect('head_manager_settings')
            else:
                messages.error(request, 'Incorrect old password.')
    else:
        form = ChangePasswordForm()
    return render(request, 'users/change_password.html', {'form': form})


@login_required
def head_manager_edit_profile(request):
    if request.user.role != 'head_manager':
        messages.warning(request, "Access denied. You don't have permission to access this page.")
        return redirect('login')

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('head_manager_settings')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def store_manager_settings(request):
    # Check if user has store manager privileges
    if request.user.role != 'store_manager':
        messages.warning(request, "Access denied. Store manager role required.")
        return redirect('login')

    # Show welcome message for first login users, but don't reset the flag yet
    if request.user.is_first_login:
        messages.info(request, "Welcome! Please update your password and profile information.")

    return render(request, 'mainpages/store_manager_settings.html')

@login_required
def store_manager_change_password(request):
    if request.user.role != 'store_manager':
        messages.warning(request, "Access denied. You don't have permission to access this page.")
        return redirect('login')

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password1 = form.cleaned_data['new_password1']
            if request.user.check_password(old_password):
                # Check if this is first login before changing password
                was_first_login = request.user.is_first_login
                request.user.set_password(new_password1)
                # Mark user as no longer first login after password change
                if request.user.is_first_login:
                    request.user.is_first_login = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')
                # Redirect to dashboard if it was first login, otherwise back to settings
                if was_first_login:
                    return redirect('store_manager_page')
                else:
                    return redirect('store_manager_settings')
            else:
                messages.error(request, 'Incorrect old password.')
    else:
        form = ChangePasswordForm()
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def cashier_settings(request):
    # Check if user has cashier privileges
    if request.user.role != 'cashier':
        messages.warning(request, "Access denied. Cashier role required.")
        return redirect('login')

    # Show welcome message for first login users, but don't reset the flag yet
    if request.user.is_first_login:
        messages.info(request, "Welcome! Please update your password and profile information.")

    return render(request, 'mainpages/cashier_settings.html')


@login_required
def cashier_edit_profile(request):
    if request.user.role != 'cashier':
        messages.warning(request, "Access denied. You don't have permission to access this page.")
        return redirect('login')

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('cashier_settings')
        else:
            messages.error(request, 'Error updating profile.')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})


@login_required
def cashier_change_password(request):
    if request.user.role != 'cashier':
        messages.warning(request, "Access denied. You don't have permission to access this page.")
        return redirect('login')

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password1 = form.cleaned_data['new_password1']
            if request.user.check_password(old_password):
                # Check if this is first login before changing password
                was_first_login = request.user.is_first_login
                request.user.set_password(new_password1)
                # Mark user as no longer first login after password change
                if request.user.is_first_login:
                    request.user.is_first_login = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')
                # Redirect to dashboard if it was first login, otherwise back to settings
                if was_first_login:
                    return redirect('cashier_page')
                else:
                    return redirect('cashier_settings')
            else:
                messages.error(request, 'Incorrect old password.')
    else:
        form = ChangePasswordForm()
    return render(request, 'users/change_password.html', {'form': form})


class CustomPasswordChangeView(PasswordChangeView):
    """
    Custom Password Change View that redirects users to their appropriate dashboard
    based on their role after successful password change.
    """
    template_name = 'users/password_change.html'

    def get_success_url(self):
        """
        Redirect to the appropriate dashboard based on user role
        """
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return reverse_lazy('admin_dashboard')
        elif user.role == 'head_manager':
            return reverse_lazy('head_manager_page')
        elif user.role == 'store_manager':
            return reverse_lazy('store_manager_page')
        elif user.role == 'cashier':
            return reverse_lazy('cashier_page')
        elif user.role == 'supplier':
            return reverse_lazy('supplier_dashboard')
        else:
            # Default fallback
            return reverse_lazy('login')


# Analytics and Reports Views for Head Manager

@login_required
def analytics_dashboard(request):
    """
    Analytics dashboard showing store performance, top products, and best sellers.
    """
    if request.user.role != 'head_manager':
        messages.error(request, 'Access denied. Head manager role required.')
        return redirect('login')

    # Get time period filter
    period = request.GET.get('period', '30')
    end_date = timezone.now()

    if period == '7':
        start_date = end_date - timedelta(days=7)
    elif period == '90':
        start_date = end_date - timedelta(days=90)
    elif period == '365':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)

    # Store Performance Analysis
    stores = Store.objects.all()
    store_performance = []

    for store in stores:
        # Get sales data for the store
        sales_data = Transaction.objects.filter(
            store=store,
            transaction_type='sale',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(
            total_sales=Sum('total_amount'),
            total_transactions=Count('id'),
            avg_transaction=Avg('total_amount')
        )

        # Handle None values from aggregation
        total_sales = sales_data['total_sales'] or Decimal('0')
        total_transactions = sales_data['total_transactions'] or 0
        avg_transaction = sales_data['avg_transaction'] or Decimal('0')

        # Get product count in store
        product_count = Stock.objects.filter(store=store, quantity__gt=0).count()

        # Calculate performance score (weighted combination of metrics)
        performance_score = float(total_sales)

        store_performance.append({
            'store': store,
            'total_sales': total_sales,
            'total_transactions': total_transactions,
            'avg_transaction': avg_transaction,
            'product_count': product_count,
            'performance_score': performance_score
        })

    # Sort stores by performance score
    store_performance.sort(key=lambda x: x['performance_score'], reverse=True)

    # Top Products Per Store
    top_products_per_store = {}
    for store in stores:
        # Get top products based on stock levels and recent transactions
        top_products = Stock.objects.filter(
            store=store,
            quantity__gt=0
        ).select_related('product').order_by('-quantity')[:5]

        products_data = []
        for stock in top_products:
            # Calculate sales for this product in this store
            product_sales = Transaction.objects.filter(
                store=store,
                transaction_type='sale',
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).aggregate(
                total_sold=Sum('quantity'),
                revenue=Sum('total_amount')
            )

            # Handle None values from aggregation
            total_sold = product_sales['total_sold'] or 0
            revenue = product_sales['revenue'] or Decimal('0')

            products_data.append({
                'name': stock.product.name,
                'category': stock.product.category,
                'quantity_in_stock': stock.quantity,
                'total_sold': total_sold,
                'revenue': revenue
            })

        top_products_per_store[store.id] = products_data

    # Overall Best Sellers (across all stores)
    best_sellers = []
    all_products = Product.objects.all()

    for product in all_products:
        total_sales = Transaction.objects.filter(
            transaction_type='sale',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(
            total_sold=Sum('quantity'),
            revenue=Sum('total_amount')
        )

        # Handle None values from aggregation
        total_sold = total_sales['total_sold'] or 0
        total_revenue = total_sales['revenue'] or Decimal('0')

        if total_sold > 0:
            best_sellers.append({
                'name': product.name,
                'category': product.category,
                'total_sold': total_sold,
                'revenue': total_revenue
            })

    # Sort best sellers by quantity sold and add performance metrics
    best_sellers.sort(key=lambda x: x['total_sold'], reverse=True)
    best_sellers = best_sellers[:10]  # Top 10

    # Calculate performance percentages for best sellers
    max_sold = max([p['total_sold'] for p in best_sellers]) if best_sellers else 1
    for product in best_sellers:
        product['performance_percentage'] = (product['total_sold'] / max_sold * 100) if max_sold > 0 else 0

    # Enhanced KPIs and Overall Statistics
    total_revenue = sum(sp['total_sales'] for sp in store_performance)
    total_transactions = sum(sp['total_transactions'] for sp in store_performance)
    active_stores = len([sp for sp in store_performance if sp['total_sales'] > 0])

    # Calculate additional KPIs
    avg_revenue_per_store = total_revenue / stores.count() if stores.count() > 0 else 0
    avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0

    # Store performance ranking with detailed metrics
    for i, store_data in enumerate(store_performance):
        store_data['rank'] = i + 1
        store_data['revenue_percentage'] = (float(store_data['total_sales']) / float(total_revenue) * 100) if total_revenue > 0 else 0

    overall_stats = {
        'total_stores': stores.count(),
        'active_stores': active_stores,
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'avg_revenue_per_store': avg_revenue_per_store,
        'avg_transaction_value': avg_transaction_value,
        'period_days': (end_date - start_date).days,
        'best_performing_store': store_performance[0] if store_performance else None,
        'growth_rate': 0  # Placeholder for growth calculation
    }

    # Sales trend data for charts
    daily_sales = []
    current_date = start_date.date()
    while current_date <= end_date.date():
        day_sales = Transaction.objects.filter(
            transaction_type='sale',
            timestamp__date=current_date
        ).aggregate(total=Sum('total_amount'))

        # Handle None values from aggregation
        total_sales = day_sales['total'] or Decimal('0')

        daily_sales.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'sales': float(total_sales)
        })
        current_date += timedelta(days=1)

    # Calculate additional analytics metrics
    peak_sales_day = max(daily_sales, key=lambda x: x['sales'])['date'] if daily_sales else None
    avg_daily_sales = sum(d['sales'] for d in daily_sales) / len(daily_sales) if daily_sales else 0
    top_store_percentage = (float(store_performance[0]['total_sales']) / float(total_revenue) * 100) if store_performance and total_revenue > 0 else 0
    total_best_seller_revenue = sum(p['revenue'] for p in best_sellers) if best_sellers else 0

    context = {
        'store_performance': store_performance,
        'top_products_per_store': top_products_per_store,
        'best_sellers': best_sellers,
        'overall_stats': overall_stats,
        'daily_sales': daily_sales,
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'peak_sales_day': peak_sales_day,
        'avg_daily_sales': avg_daily_sales,
        'top_store_percentage': top_store_percentage,
        'total_best_seller_revenue': total_best_seller_revenue,
        'period_days': (end_date - start_date).days,
    }

    return render(request, 'analytics/dashboard.html', context)


@login_required
def financial_reports(request):
    """
    Financial reports page with P&L statements and financial metrics.
    """
    if request.user.role != 'head_manager':
        messages.error(request, 'Access denied. Head manager role required.')
        return redirect('login')

    # Get time period filter
    period = request.GET.get('period', '30')
    end_date = timezone.now()

    if period == '7':
        start_date = end_date - timedelta(days=7)
    elif period == '90':
        start_date = end_date - timedelta(days=90)
    elif period == '365':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)

    # Financial data per store
    stores = Store.objects.all()
    financial_data = []

    for store in stores:
        # Revenue from sales
        revenue = Transaction.objects.filter(
            store=store,
            transaction_type='sale',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        # Expenses from financial records
        expenses = FinancialRecord.objects.filter(
            store=store,
            record_type='expense',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Calculate profit/loss and margin
        profit_loss = revenue - expenses
        profit_margin = (profit_loss / revenue * 100) if revenue > 0 else 0

        financial_data.append({
            'store': store,
            'revenue': revenue,
            'expenses': expenses,
            'profit_loss': profit_loss,
            'profit_margin': profit_margin
        })

    # Sort by profit/loss
    financial_data.sort(key=lambda x: x['profit_loss'], reverse=True)

    # Overall financial summary
    total_revenue = sum(fd['revenue'] for fd in financial_data)
    total_expenses = sum(fd['expenses'] for fd in financial_data)
    total_profit = total_revenue - total_expenses
    overall_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    # Monthly financial trend
    monthly_trend = []
    current_month = start_date.replace(day=1)

    while current_month <= end_date:
        next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)

        month_revenue = Transaction.objects.filter(
            transaction_type='sale',
            timestamp__gte=current_month,
            timestamp__lt=next_month
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        month_expenses = FinancialRecord.objects.filter(
            record_type='expense',
            timestamp__gte=current_month,
            timestamp__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        monthly_trend.append({
            'month': current_month.strftime('%Y-%m'),
            'revenue': float(month_revenue),
            'expenses': float(month_expenses),
            'profit': float(month_revenue - month_expenses)
        })

        current_month = next_month

    # Key financial metrics
    financial_metrics = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'overall_margin': overall_margin,
        'best_performing_store': financial_data[0] if financial_data else None,
        'stores_count': stores.count(),
        'profitable_stores': len([fd for fd in financial_data if fd['profit_loss'] > 0])
    }

    context = {
        'financial_data': financial_data,
        'financial_metrics': financial_metrics,
        'monthly_trend': monthly_trend,
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'analytics/financial_reports.html', context)


@login_required
def analytics_api(request):
    """
    API endpoint for chart data.
    """
    if request.user.role != 'head_manager':
        return JsonResponse({'error': 'Access denied'}, status=403)

    chart_type = request.GET.get('type', 'sales_trend')
    period = request.GET.get('period', '30')

    end_date = timezone.now()
    if period == '7':
        start_date = end_date - timedelta(days=7)
    elif period == '90':
        start_date = end_date - timedelta(days=90)
    elif period == '365':
        start_date = end_date - timedelta(days=365)
    else:
        start_date = end_date - timedelta(days=30)

    if chart_type == 'sales_trend':
        # Daily sales trend
        daily_sales = []
        current_date = start_date.date()

        while current_date <= end_date.date():
            day_sales = Transaction.objects.filter(
                transaction_type='sale',
                timestamp__date=current_date
            ).aggregate(total=Sum('total_amount') or Decimal('0'))

            daily_sales.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'sales': float(day_sales['total'])
            })
            current_date += timedelta(days=1)

        return JsonResponse({
            'labels': [item['date'] for item in daily_sales],
            'data': [item['sales'] for item in daily_sales]
        })

    elif chart_type == 'store_comparison':
        # Store performance comparison
        stores = Store.objects.all()
        store_data = []

        for store in stores:
            total_sales = Transaction.objects.filter(
                store=store,
                transaction_type='sale',
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

            store_data.append({
                'store': store.name,
                'sales': float(total_sales)
            })

        return JsonResponse({
            'labels': [item['store'] for item in store_data],
            'data': [item['sales'] for item in store_data]
        })

    return JsonResponse({'error': 'Invalid chart type'}, status=400)
