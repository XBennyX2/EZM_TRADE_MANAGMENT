from django.shortcuts import render, redirect
from store.models import StoreCashier, Store
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import CustomLoginForm, EditProfileForm, ChangePasswordForm
from .models import CustomUser
from transactions.models import Transaction, Order
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.contrib import messages
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
    Head Manager view for managing restock requests.
    """
    if request.user.role != 'head_manager':
        messages.error(request, "Access denied. Head Manager role required.")
        return redirect('login')

    from Inventory.models import RestockRequest
    from django.core.paginator import Paginator

    # Filter options
    status_filter = request.GET.get('status', 'all')
    store_filter = request.GET.get('store', 'all')
    priority_filter = request.GET.get('priority', 'all')

    # Build query
    requests = RestockRequest.objects.select_related(
        'store', 'product', 'requested_by', 'reviewed_by'
    ).order_by('-requested_date')

    if status_filter != 'all':
        requests = requests.filter(status=status_filter)
    if store_filter != 'all':
        requests = requests.filter(store_id=store_filter)
    if priority_filter != 'all':
        requests = requests.filter(priority=priority_filter)

    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options
    stores = Store.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'stores': stores,
        'status_filter': status_filter,
        'store_filter': store_filter,
        'priority_filter': priority_filter,
        'status_choices': RestockRequest.STATUS_CHOICES,
        'priority_choices': RestockRequest.PRIORITY_CHOICES,
    }

    return render(request, 'mainpages/head_manager_restock_requests.html', context)


@login_required
def head_manager_transfer_requests(request):
    """
    Head Manager view for managing stock transfer requests.
    """
    if request.user.role != 'head_manager':
        messages.error(request, "Access denied. Head Manager role required.")
        return redirect('login')

    from Inventory.models import StoreStockTransferRequest
    from django.core.paginator import Paginator

    # Filter options
    status_filter = request.GET.get('status', 'all')
    from_store_filter = request.GET.get('from_store', 'all')
    to_store_filter = request.GET.get('to_store', 'all')
    priority_filter = request.GET.get('priority', 'all')

    # Build query
    requests = StoreStockTransferRequest.objects.select_related(
        'from_store', 'to_store', 'product', 'requested_by', 'reviewed_by'
    ).order_by('-requested_date')

    if status_filter != 'all':
        requests = requests.filter(status=status_filter)
    if from_store_filter != 'all':
        requests = requests.filter(from_store_id=from_store_filter)
    if to_store_filter != 'all':
        requests = requests.filter(to_store_id=to_store_filter)
    if priority_filter != 'all':
        requests = requests.filter(priority=priority_filter)

    # Pagination
    paginator = Paginator(requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options
    stores = Store.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'stores': stores,
        'status_filter': status_filter,
        'from_store_filter': from_store_filter,
        'to_store_filter': to_store_filter,
        'priority_filter': priority_filter,
        'status_choices': StoreStockTransferRequest.STATUS_CHOICES,
        'priority_choices': StoreStockTransferRequest.PRIORITY_CHOICES,
    }

    return render(request, 'mainpages/head_manager_transfer_requests.html', context)

@login_required
def approve_restock_request(request, request_id):
    """
    Handle restock request approval by head manager.
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
            review_notes = request.POST.get('review_notes', '')

            if approved_quantity <= 0:
                messages.error(request, "Approved quantity must be greater than 0.")
                return redirect('head_manager_restock_requests')

            # Update request status
            restock_request.status = 'approved'
            restock_request.reviewed_by = request.user
            restock_request.reviewed_date = timezone.now()
            restock_request.review_notes = review_notes
            restock_request.approved_quantity = approved_quantity
            restock_request.save()

            # Update stock levels
            stock, created = Stock.objects.get_or_create(
                store=restock_request.store,
                product=restock_request.product,
                defaults={'quantity': 0, 'selling_price': restock_request.product.price}
            )
            stock.quantity += approved_quantity
            stock.save()

            # Mark as fulfilled
            restock_request.status = 'fulfilled'
            restock_request.fulfilled_quantity = approved_quantity
            restock_request.fulfilled_date = timezone.now()
            restock_request.save()

            # Create notification for store manager
            from .notifications import NotificationTriggers
            NotificationTriggers.notify_request_status_change(restock_request, 'approved', request.user)

            messages.success(request, f"Restock request {restock_request.request_number} approved and fulfilled.")

        except (RestockRequest.DoesNotExist, ValueError) as e:
            messages.error(request, "Invalid request or quantity specified.")
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")

    return redirect('head_manager_restock_requests')


@login_required
def reject_restock_request(request, request_id):
    """
    Handle restock request rejection by head manager.
    """
    if request.user.role != 'head_manager':
        messages.error(request, "Access denied. Head Manager role required.")
        return redirect('login')

    if request.method == 'POST':
        from Inventory.models import RestockRequest
        from django.utils import timezone

        try:
            restock_request = RestockRequest.objects.get(id=request_id, status='pending')
            review_notes = request.POST.get('review_notes', '')

            # Update request status
            restock_request.status = 'rejected'
            restock_request.reviewed_by = request.user
            restock_request.reviewed_date = timezone.now()
            restock_request.review_notes = review_notes
            restock_request.save()

            # Create notification for store manager
            from .notifications import NotificationTriggers
            NotificationTriggers.notify_request_status_change(restock_request, 'rejected', request.user)

            messages.success(request, f"Restock request {restock_request.request_number} rejected.")

        except RestockRequest.DoesNotExist:
            messages.error(request, "Request not found or already processed.")
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")

    return redirect('head_manager_restock_requests')


@login_required
def approve_transfer_request(request, request_id):
    """
    Handle stock transfer request approval by head manager.
    """
    if request.user.role != 'head_manager':
        messages.error(request, "Access denied. Head Manager role required.")
        return redirect('login')

    if request.method == 'POST':
        from Inventory.models import StoreStockTransferRequest, Stock
        from django.utils import timezone

        try:
            transfer_request = StoreStockTransferRequest.objects.get(id=request_id, status='pending')
            approved_quantity = int(request.POST.get('approved_quantity', transfer_request.requested_quantity))
            review_notes = request.POST.get('review_notes', '')

            if approved_quantity <= 0:
                messages.error(request, "Approved quantity must be greater than 0.")
                return redirect('head_manager_transfer_requests')

            # Check if source store has enough stock
            try:
                source_stock = Stock.objects.get(
                    store=transfer_request.from_store,
                    product=transfer_request.product
                )
                if source_stock.quantity < approved_quantity:
                    messages.error(request, f"Insufficient stock in {transfer_request.from_store.name}. Available: {source_stock.quantity}")
                    return redirect('head_manager_transfer_requests')
            except Stock.DoesNotExist:
                messages.error(request, f"Product not found in {transfer_request.from_store.name} inventory.")
                return redirect('head_manager_transfer_requests')

            # Update request status
            transfer_request.status = 'approved'
            transfer_request.reviewed_by = request.user
            transfer_request.reviewed_date = timezone.now()
            transfer_request.review_notes = review_notes
            transfer_request.approved_quantity = approved_quantity
            transfer_request.save()

            # Perform stock transfer
            # Deduct from source store
            source_stock.quantity -= approved_quantity
            source_stock.save()

            # Add to destination store
            dest_stock, created = Stock.objects.get_or_create(
                store=transfer_request.to_store,
                product=transfer_request.product,
                defaults={'quantity': 0, 'selling_price': transfer_request.product.price}
            )
            dest_stock.quantity += approved_quantity
            dest_stock.save()

            # Mark as completed
            transfer_request.status = 'completed'
            transfer_request.shipped_date = timezone.now()
            transfer_request.received_date = timezone.now()
            transfer_request.actual_quantity_transferred = approved_quantity
            transfer_request.save()

            # Create notification for requesting store manager
            from .notifications import NotificationTriggers
            NotificationTriggers.notify_request_status_change(transfer_request, 'approved', request.user)

            messages.success(request, f"Transfer request {transfer_request.request_number} approved and completed.")

        except (StoreStockTransferRequest.DoesNotExist, ValueError) as e:
            messages.error(request, "Invalid request or quantity specified.")
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")

    return redirect('head_manager_transfer_requests')


@login_required
def reject_transfer_request(request, request_id):
    """
    Handle stock transfer request rejection by head manager.
    """
    if request.user.role != 'head_manager':
        messages.error(request, "Access denied. Head Manager role required.")
        return redirect('login')

    if request.method == 'POST':
        from Inventory.models import StoreStockTransferRequest
        from django.utils import timezone

        try:
            transfer_request = StoreStockTransferRequest.objects.get(id=request_id, status='pending')
            review_notes = request.POST.get('review_notes', '')

            # Update request status
            transfer_request.status = 'rejected'
            transfer_request.reviewed_by = request.user
            transfer_request.reviewed_date = timezone.now()
            transfer_request.review_notes = review_notes
            transfer_request.save()

            # Create notification for requesting store manager
            from .notifications import NotificationTriggers
            NotificationTriggers.notify_request_status_change(transfer_request, 'rejected', request.user)

            messages.success(request, f"Transfer request {transfer_request.request_number} rejected.")

        except StoreStockTransferRequest.DoesNotExist:
            messages.error(request, "Request not found or already processed.")
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")

    return redirect('head_manager_transfer_requests')


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

    context = {
        'store': store,
        'cashier_assignment': cashier_assignment,
        'recent_transactions': recent_transactions,
        'total_sales_30_days': total_sales_30_days,
        'total_sales_7_days': total_sales_7_days,
        'most_sold_products': most_sold_products,
        'low_stock_items': low_stock_items,
        'current_stock': current_stock,
        'recent_restock_requests': recent_restock_requests,
        'recent_transfer_requests': recent_transfer_requests,
        'pending_restock_count': pending_restock_count,
        'pending_transfer_count': pending_transfer_count,
        'other_stores': other_stores,
    }

    return render(request, 'mainpages/store_manager_page.html', context)


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
        from_store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('admin_dashboard')

    if request.method == 'POST':
        from Inventory.models import Product, Stock, StoreStockTransferRequest

        product_id = request.POST.get('product_id')
        to_store_id = request.POST.get('to_store_id')
        requested_quantity = request.POST.get('requested_quantity')
        priority = request.POST.get('priority', 'medium')
        reason = request.POST.get('reason', '')

        try:
            product = Product.objects.get(id=product_id)
            to_store = Store.objects.get(id=to_store_id)
            requested_quantity = int(requested_quantity)

            if requested_quantity <= 0:
                messages.error(request, "Requested quantity must be greater than 0.")
                return redirect('store_manager_page')

            if from_store == to_store:
                messages.error(request, "Cannot transfer to the same store.")
                return redirect('store_manager_page')

            # Check for existing pending requests
            existing_request = StoreStockTransferRequest.objects.filter(
                from_store=from_store,
                to_store=to_store,
                product=product,
                status='pending'
            ).first()

            if existing_request:
                messages.warning(request, f"You already have a pending transfer request for {product.name} to {to_store.name}.")
                return redirect('store_manager_page')

            # Create transfer request
            transfer_request = StoreStockTransferRequest.objects.create(
                product=product,
                from_store=from_store,
                to_store=to_store,
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
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    return redirect('manage_users')

@user_passes_test(is_admin)
def view_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'admin/user_detail.html', {'user': user})

@user_passes_test(is_admin)
def change_user_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = ChangeUserRoleForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('manage_users')
    else:
        form = ChangeUserRoleForm(instance=user)
    return render(request, 'admin/change_user_role.html', {'form': form, 'user': user})

@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Prevent admin from deleting themselves
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('manage_users')

    # Prevent deletion of superusers by non-superusers
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You cannot delete a superuser account.")
        return redirect('manage_users')

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' has been successfully deleted.")
        return redirect('manage_users')

    return render(request, 'admin/delete_user_confirm.html', {'user': user})

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
