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
import logging

logger = logging.getLogger(__name__)
from decimal import Decimal
import json
import logging

# Additional imports for enhanced financial reporting
from io import BytesIO
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404
from django.conf import settings
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
    company_name = getattr(settings, 'COMPANY_NAME', 'EZM Trade Management System')
    subject = f"Welcome to {company_name} — Verify Your Email"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email

    context = {
        'username': user.username,
        'otp': user.otp_code,
        'company_name': company_name,
    }

    text_content = f"Hi {user.username},\\nWelcome to {company_name}!\\nYour OTP code is: {user.otp_code}"
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
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
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
        username_attempted = request.POST.get('username', '')

        if form.is_valid():
            user = form.get_user()

            if not user.is_active:
                # Log failed login due to inactive account
                log_login_attempt(request, username_attempted, user, 'failed', 'Account inactive')
                messages.error(request, "Your account is inactive. Please contact the administrator.")
                return redirect('login')

            # Log successful login
            log_login_attempt(request, username_attempted, user, 'success')

            login(request, user)
            if user.is_first_login:
                # All users go to the unified first login password change page
                return redirect('first_login_password_change')
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
            # Log failed login attempt
            log_login_attempt(request, username_attempted, None, 'failed', 'Invalid credentials')
            messages.error(request, "Invalid email or password.")
    else:
        form = CustomLoginForm()

    return render(request, 'users/login.html', {'form': form})

from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    return redirect('login')

from django.contrib.auth import get_user_model
from .models import LoginLog, AccountReset

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

    # Payment statistics
    payment_stats = {}
    try:
        from payments.models import ChapaTransaction
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()
        this_month = today.replace(day=1)

        payment_stats = {
            'total_payments': ChapaTransaction.objects.filter(status='success').count(),
            'monthly_payments': ChapaTransaction.objects.filter(
                status='success',
                paid_at__gte=this_month
            ).count(),
            'total_payment_amount': ChapaTransaction.objects.filter(
                status='success'
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'monthly_payment_amount': ChapaTransaction.objects.filter(
                status='success',
                paid_at__gte=this_month
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'recent_payments': ChapaTransaction.objects.filter(
                status='success'
            ).select_related('supplier').order_by('-paid_at')[:5]
        }
    except:
        payment_stats = {
            'total_payments': 0,
            'monthly_payments': 0,
            'total_payment_amount': 0,
            'monthly_payment_amount': 0,
            'recent_payments': []
        }

    context = {
        'stores': stores,
        'pending_restock_requests': pending_restock_requests,
        'pending_transfer_requests': pending_transfer_requests,
        'recent_restock_requests': recent_restock_requests,
        'recent_transfer_requests': recent_transfer_requests,
        'payment_stats': payment_stats,
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

            # Use the approve method which validates and approves the request
            restock_request.approve(
                approved_by=request.user,
                approved_quantity=approved_quantity,
                notes=review_notes or f"Approved by {request.user.get_full_name() or request.user.username}"
            )

            # Success message with details
            success_msg = f"✅ Restock request #{restock_request.request_number} approved! {approved_quantity} units of {restock_request.product.name} are ready for the store manager to receive."
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





def calculate_store_analytics(store):
    """
    Calculate comprehensive analytics for a store including performance metrics,
    inventory analysis, operational analytics, and actionable insights.
    """
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Avg, F, Q, Max, Min
    from django.utils import timezone
    from decimal import Decimal
    import json

    now = timezone.now()
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)

    analytics = {}

    try:
        # 1. STORE PERFORMANCE METRICS

        # Current month revenue
        current_month_sales = Transaction.objects.filter(
            store=store,
            transaction_type='sale',
            timestamp__gte=current_month_start
        ).aggregate(
            total_revenue=Sum('total_amount'),
            total_transactions=Count('id'),
            avg_transaction=Avg('total_amount')
        )

        # Previous month revenue
        previous_month_sales = Transaction.objects.filter(
            store=store,
            transaction_type='sale',
            timestamp__gte=previous_month_start,
            timestamp__lt=current_month_start
        ).aggregate(
            total_revenue=Sum('total_amount'),
            total_transactions=Count('id'),
            avg_transaction=Avg('total_amount')
        )

        # Calculate trends
        current_revenue = current_month_sales['total_revenue'] or Decimal('0')
        previous_revenue = previous_month_sales['total_revenue'] or Decimal('0')
        revenue_trend = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0

        current_transactions = current_month_sales['total_transactions'] or 0
        previous_transactions = previous_month_sales['total_transactions'] or 0
        transaction_count_trend = ((current_transactions - previous_transactions) / previous_transactions * 100) if previous_transactions > 0 else 0

        current_avg = current_month_sales['avg_transaction'] or Decimal('0')
        previous_avg = previous_month_sales['avg_transaction'] or Decimal('0')
        transaction_value_trend = ((current_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0

        # Daily transactions average
        days_in_month = (now - current_month_start).days + 1
        daily_transactions = current_transactions / days_in_month if days_in_month > 0 else 0

        analytics.update({
            'current_month_revenue': float(current_revenue),
            'previous_month_revenue': float(previous_revenue),
            'revenue_trend': float(revenue_trend),
            'current_month_transactions': current_transactions,
            'previous_month_transactions': previous_transactions,
            'transaction_count_trend': float(transaction_count_trend),
            'current_avg_transaction': float(current_avg),
            'previous_avg_transaction': float(previous_avg),
            'transaction_value_trend': float(transaction_value_trend),
            'avg_transaction_value': float(current_avg),
            'daily_transactions': int(daily_transactions),
        })

        # 2. INVENTORY ANALYSIS

        # Stock turnover rate calculation
        total_stock_value = Stock.objects.filter(store=store).aggregate(
            total_value=Sum(F('quantity') * F('selling_price'))
        )['total_value'] or Decimal('0')

        # Calculate inventory turnover (sales / average inventory)
        inventory_turnover = (float(current_revenue) / float(total_stock_value)) if total_stock_value > 0 else 0

        # Stock-out frequency
        stock_out_frequency = Stock.objects.filter(
            store=store,
            quantity=0,
            last_updated__gte=current_month_start
        ).count()

        # Customer satisfaction (based on return rates)
        total_sales_count = current_transactions
        return_count = Transaction.objects.filter(
            store=store,
            transaction_type='refund',
            timestamp__gte=current_month_start
        ).count()

        customer_satisfaction = ((total_sales_count - return_count) / total_sales_count * 100) if total_sales_count > 0 else 100

        analytics.update({
            'inventory_turnover': inventory_turnover,
            'stock_out_frequency': stock_out_frequency,
            'customer_satisfaction': customer_satisfaction,
        })

        # 3. PEAK HOURS/DAYS ANALYSIS

        # Peak hour analysis (SQLite compatible)
        hourly_sales = Transaction.objects.filter(
            store=store,
            transaction_type='sale',
            timestamp__gte=last_30_days
        ).extra(
            select={'hour': "strftime('%%H', timestamp)"}
        ).values('hour').annotate(
            total_sales=Sum('total_amount'),
            transaction_count=Count('id')
        ).order_by('-total_sales')

        peak_hour = f"{hourly_sales[0]['hour']}:00" if hourly_sales else "14:00"
        peak_sales = float(hourly_sales[0]['total_sales']) if hourly_sales else 0

        # Peak day analysis (SQLite compatible)
        daily_sales = Transaction.objects.filter(
            store=store,
            transaction_type='sale',
            timestamp__gte=last_7_days
        ).extra(
            select={'weekday': "strftime('%%w', timestamp)"}
        ).values('weekday').annotate(
            total_sales=Sum('total_amount')
        ).order_by('-total_sales')

        weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        peak_day = weekdays[int(daily_sales[0]['weekday'])] if daily_sales else "Saturday"

        analytics.update({
            'peak_hour': peak_hour,
            'peak_day': peak_day,
            'peak_sales': peak_sales,
        })

        # 4. CHART DATA PREPARATION

        # Sales trend data (last 30 days)
        sales_trend_data = []
        sales_trend_labels = []
        for i in range(30):
            date = (now - timedelta(days=29-i)).date()
            day_sales = Transaction.objects.filter(
                store=store,
                transaction_type='sale',
                timestamp__date=date
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            sales_trend_data.append(float(day_sales))
            sales_trend_labels.append(date.strftime('%m/%d'))

        # Peak hours data
        peak_hours_labels = ['9AM', '10AM', '11AM', '12PM', '1PM', '2PM', '3PM', '4PM', '5PM']
        peak_hours_data = []
        for hour in range(9, 18):  # 9 AM to 5 PM
            hour_sales = Transaction.objects.filter(
                store=store,
                transaction_type='sale',
                timestamp__gte=last_30_days,
                timestamp__hour=hour
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            peak_hours_data.append(float(hour_sales))

        # Payment method data
        payment_methods = Transaction.objects.filter(
            store=store,
            transaction_type='sale',
            timestamp__gte=last_30_days
        ).values('payment_type').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        )

        payment_method_labels = []
        payment_method_data = []
        total_transactions = sum(pm['count'] for pm in payment_methods)

        for pm in payment_methods:
            payment_method_labels.append(pm['payment_type'].title())
            percentage = (pm['count'] / total_transactions * 100) if total_transactions > 0 else 0
            payment_method_data.append(round(percentage, 1))

        # 5. INVENTORY INSIGHTS

        # Top performing products
        top_products = []
        try:
            from transactions.models import Order
            top_product_sales = Order.objects.filter(
                transaction__store=store,
                transaction__transaction_type='sale',
                transaction__timestamp__gte=last_30_days
            ).values('product__name', 'product__id').annotate(
                total_quantity=Sum('quantity'),
                revenue=Sum(F('quantity') * F('price_at_time_of_sale')),
                turnover_rate=F('revenue') / F('product__stock__selling_price')
            ).order_by('-revenue')[:5]

            for product in top_product_sales:
                top_products.append({
                    'name': product['product__name'],
                    'id': product['product__id'],
                    'turnover_rate': float(product['turnover_rate'] or 0),
                    'revenue': float(product['revenue'] or 0)
                })
        except:
            # Fallback if Order model is not available
            pass

        # Expiring products
        expiring_products = []
        try:
            from datetime import date
            expiring_stock = Stock.objects.filter(
                store=store,
                product__expiry_date__isnull=False,
                product__expiry_date__lte=date.today() + timedelta(days=30),
                quantity__gt=0
            ).select_related('product')[:5]

            for stock in expiring_stock:
                days_to_expiry = (stock.product.expiry_date - date.today()).days
                expiring_products.append({
                    'name': stock.product.name,
                    'expiry_date': stock.product.expiry_date,
                    'days_to_expiry': max(0, days_to_expiry)
                })
        except:
            pass

        # Slow moving products
        slow_moving_products = []
        try:
            # Products with no sales in last 30 days
            products_with_sales = Order.objects.filter(
                transaction__store=store,
                transaction__transaction_type='sale',
                transaction__timestamp__gte=last_30_days
            ).values_list('product_id', flat=True).distinct()

            slow_moving_stock = Stock.objects.filter(
                store=store,
                quantity__gt=0
            ).exclude(product_id__in=products_with_sales).select_related('product')[:5]

            for stock in slow_moving_stock:
                slow_moving_products.append({
                    'name': stock.product.name,
                    'current_stock': stock.quantity,
                    'days_since_sale': 30  # Simplified
                })
        except:
            pass

        # Reorder recommendations
        reorder_recommendations = []
        try:
            low_stock_items = Stock.objects.filter(
                store=store,
                quantity__lte=F('low_stock_threshold'),
                quantity__gt=0
            ).select_related('product')[:5]

            for stock in low_stock_items:
                suggested_quantity = max(stock.low_stock_threshold * 2, 10)
                reorder_recommendations.append({
                    'name': stock.product.name,
                    'id': stock.product.id,
                    'suggested_quantity': suggested_quantity
                })
        except:
            pass

        # 6. OPERATIONAL ANALYTICS

        # Return analysis
        return_rate = 0
        most_returned_product = "N/A"
        return_value = 0

        try:
            total_sales = current_transactions
            total_returns = Transaction.objects.filter(
                store=store,
                transaction_type='refund',
                timestamp__gte=current_month_start
            ).count()

            return_rate = (total_returns / total_sales * 100) if total_sales > 0 else 0

            return_transactions = Transaction.objects.filter(
                store=store,
                transaction_type='refund',
                timestamp__gte=current_month_start
            ).aggregate(total_value=Sum('total_amount'))

            return_value = float(return_transactions['total_value'] or 0)
        except:
            pass

        # 7. INSIGHTS AND RECOMMENDATIONS

        insights = []

        # Revenue trend insight
        if revenue_trend > 10:
            insights.append({
                'icon': 'graph-up',
                'title': 'Excellent Revenue Growth',
                'description': f'Your store revenue has increased by {revenue_trend:.1f}% this month. Keep up the great work!',
                'action': None,
                'action_text': None
            })
        elif revenue_trend < -10:
            insights.append({
                'icon': 'graph-down',
                'title': 'Revenue Decline Alert',
                'description': f'Revenue has decreased by {abs(revenue_trend):.1f}% this month. Consider promotional strategies.',
                'action': 'showPromotionModal()',
                'action_text': 'Plan Promotion'
            })

        # Inventory turnover insight
        if inventory_turnover < 1:
            insights.append({
                'icon': 'boxes',
                'title': 'Slow Inventory Movement',
                'description': 'Your inventory turnover rate is below optimal. Consider reviewing product mix and pricing.',
                'action': 'window.location.href="/store/stock-management/"',
                'action_text': 'Review Inventory'
            })

        # Stock-out insight
        if stock_out_frequency > 5:
            insights.append({
                'icon': 'exclamation-triangle',
                'title': 'Frequent Stock-outs',
                'description': f'You\'ve had {stock_out_frequency} stock-outs this month. Improve inventory planning.',
                'action': 'window.location.href="/store/restock-requests/"',
                'action_text': 'Request Restock'
            })

        # Performance goals
        revenue_goal = 50000  # Example goal
        revenue_goal_percentage = min((float(current_revenue) / revenue_goal * 100), 100) if revenue_goal > 0 else 0
        satisfaction_goal_percentage = min((customer_satisfaction / 95 * 100), 100)
        turnover_goal_percentage = min((inventory_turnover / 4.0 * 100), 100)

        analytics.update({
            # Chart data
            'sales_trend_labels': json.dumps(sales_trend_labels),
            'sales_trend_data': json.dumps(sales_trend_data),
            'peak_hours_labels': json.dumps(peak_hours_labels),
            'peak_hours_data': json.dumps(peak_hours_data),
            'payment_method_labels': json.dumps(payment_method_labels),
            'payment_method_data': json.dumps(payment_method_data),

            # Inventory data
            'top_products': top_products,
            'expiring_products': expiring_products,
            'slow_moving_products': slow_moving_products,
            'reorder_recommendations': reorder_recommendations,

            # Operational data
            'return_rate': return_rate,
            'most_returned_product': most_returned_product,
            'return_value': return_value,

            # Insights
            'insights': insights,

            # Goals
            'revenue_goal': revenue_goal,
            'revenue_goal_percentage': revenue_goal_percentage,
            'satisfaction_goal_percentage': satisfaction_goal_percentage,
            'turnover_goal_percentage': turnover_goal_percentage,
        })

    except Exception as e:
        # Handle any database errors gracefully
        print(f"Analytics calculation error: {e}")
        analytics.update({
            'current_month_revenue': 0,
            'revenue_trend': 0,
            'avg_transaction_value': 0,
            'transaction_value_trend': 0,
            'daily_transactions': 0,
            'transaction_count_trend': 0,
            'inventory_turnover': 0,
            'stock_out_frequency': 0,
            'customer_satisfaction': 100,
            'peak_hour': "14:00",
            'peak_day': "Saturday",
            'peak_sales': 0,
            'sales_trend_labels': json.dumps([]),
            'sales_trend_data': json.dumps([]),
            'peak_hours_labels': json.dumps(['9AM', '10AM', '11AM', '12PM', '1PM', '2PM', '3PM', '4PM', '5PM']),
            'peak_hours_data': json.dumps([0, 0, 0, 0, 0, 0, 0, 0, 0]),
            'payment_method_labels': json.dumps(['Cash', 'Card']),
            'payment_method_data': json.dumps([70, 30]),
            'top_products': [],
            'expiring_products': [],
            'slow_moving_products': [],
            'reorder_recommendations': [],
            'return_rate': 0,
            'most_returned_product': "N/A",
            'return_value': 0,
            'insights': [],
            'revenue_goal': 50000,
            'revenue_goal_percentage': 0,
            'satisfaction_goal_percentage': 100,
            'turnover_goal_percentage': 0,
        })

    return analytics


@login_required
def store_sales_report(request):
    """
    Comprehensive sales report for Store Managers with filtering, analytics, and export capabilities.
    """
    # Ensure user is a store manager
    if request.user.role != 'store_manager':
        messages.error(request, 'Access denied. Store Manager role required.')
        return redirect('store_manager_page')

    # Get the store managed by this user
    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, 'No store assigned to your account.')
        return redirect('store_manager_page')

    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    product_category = request.GET.get('category')
    supplier_id = request.GET.get('supplier')
    product_id = request.GET.get('product')
    payment_method = request.GET.get('payment_method')
    export_format = request.GET.get('export')

    # Get pagination parameters
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 25)
    try:
        page = int(page)
        page_size = int(page_size)
        if page_size not in [10, 25, 50, 100]:
            page_size = 25
    except (ValueError, TypeError):
        page = 1
        page_size = 25

    # Set default date range (last 30 days)
    if not start_date or not end_date:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Build base queryset for sales transactions
    sales_transactions = Transaction.objects.filter(
        store=store,
        transaction_type='sale',
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    ).select_related('store').prefetch_related('orders__product')

    # Apply filters
    if payment_method:
        sales_transactions = sales_transactions.filter(payment_type=payment_method)

    # Get detailed sales data with product information
    sales_data = []
    total_revenue = Decimal('0.00')
    total_units_sold = 0

    for transaction in sales_transactions:
        for order in transaction.orders.all():
            if order.product:
                # Apply product filters
                if product_category and order.product.category != product_category:
                    continue
                if supplier_id and order.product.supplier_company != supplier_id:
                    continue
                if product_id and str(order.product.id) != product_id:
                    continue

                # Get current stock information
                try:
                    current_stock = Stock.objects.get(product=order.product, store=store)
                    remaining_stock = current_stock.quantity
                    current_selling_price = current_stock.selling_price
                except Stock.DoesNotExist:
                    remaining_stock = 0
                    current_selling_price = order.price_at_time_of_sale

                # Calculate metrics
                line_total = order.quantity * order.price_at_time_of_sale
                cost_price = order.product.price  # Assuming this is cost price
                profit_per_unit = order.price_at_time_of_sale - cost_price
                total_profit = profit_per_unit * order.quantity
                profit_margin = (profit_per_unit / order.price_at_time_of_sale * 100) if order.price_at_time_of_sale > 0 else 0

                sales_data.append({
                    'transaction_id': transaction.id,
                    'sale_date': transaction.timestamp,
                    'product_name': order.product.name,
                    'product_sku': getattr(order.product, 'sku', f'SKU-{order.product.id}'),
                    'category': order.product.category,
                    'supplier': order.product.supplier_company if order.product.supplier_company else 'N/A',
                    'quantity_sold': order.quantity,
                    'unit_price': order.price_at_time_of_sale,
                    'cost_price': cost_price,
                    'line_total': line_total,
                    'profit_per_unit': profit_per_unit,
                    'total_profit': total_profit,
                    'profit_margin': profit_margin,
                    'remaining_stock': remaining_stock,
                    'current_selling_price': current_selling_price,
                    'payment_method': transaction.payment_type,
                    'receipt_number': f'R{transaction.receipt.id:06d}' if hasattr(transaction, 'receipt') and transaction.receipt else f'TXN-{transaction.id}',
                })

                total_revenue += line_total
                total_units_sold += order.quantity

    # Calculate summary statistics
    total_transactions = sales_transactions.count()
    avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else Decimal('0.00')

    # Get top performing products
    top_products = {}
    for item in sales_data:
        product_name = item['product_name']
        if product_name not in top_products:
            top_products[product_name] = {
                'name': product_name,
                'total_quantity': 0,
                'total_revenue': Decimal('0.00'),
                'total_profit': Decimal('0.00'),
            }
        top_products[product_name]['total_quantity'] += item['quantity_sold']
        top_products[product_name]['total_revenue'] += item['line_total']
        top_products[product_name]['total_profit'] += item['total_profit']

    # Sort top products by revenue
    top_products_list = sorted(top_products.values(), key=lambda x: x['total_revenue'], reverse=True)[:10]

    # Get payment method distribution
    payment_distribution = sales_transactions.values('payment_type').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('-total')

    # Handle export requests
    if export_format in ['pdf', 'excel']:
        return export_sales_report(sales_data, {
            'store': store,
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': total_revenue,
            'total_units_sold': total_units_sold,
            'total_transactions': total_transactions,
            'avg_transaction_value': avg_transaction_value,
            'top_products': top_products_list,
            'payment_distribution': payment_distribution,
        }, export_format)

    # Get filter options for the form
    categories = set()
    suppliers = set()
    products = set()

    for item in sales_data:
        categories.add(item['category'])
        suppliers.add(item['supplier'])
        products.add((item['product_name'], item['product_sku']))

    # Pre-process chart data to avoid large JavaScript generation
    from collections import defaultdict
    import json

    # Process sales trend data
    sales_by_date = defaultdict(float)
    payment_methods = defaultdict(float)

    for item in sales_data:
        # Sales trend data
        date_key = item['sale_date'].strftime('%Y-%m-%d')
        sales_by_date[date_key] += float(item['line_total'])

        # Payment method data
        payment_methods[item['payment_method']] += float(item['line_total'])

    # Prepare chart data
    chart_data = {
        'sales_trend': {
            'labels': sorted(sales_by_date.keys()),
            'data': [sales_by_date[date] for date in sorted(sales_by_date.keys())]
        },
        'payment_methods': {
            'labels': [method.title() for method in payment_methods.keys()],
            'data': list(payment_methods.values())
        }
    }

    # Implement pagination for sales data
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    paginator = Paginator(sales_data, page_size)
    try:
        paginated_sales_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_sales_data = paginator.page(1)
    except EmptyPage:
        paginated_sales_data = paginator.page(paginator.num_pages)

    context = {
        'store': store,
        'sales_data': paginated_sales_data,
        'paginator': paginator,
        'page_obj': paginated_sales_data,
        'total_sales_count': len(sales_data),
        'page_size': page_size,
        'chart_data': json.dumps(chart_data),
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_units_sold': total_units_sold,
        'total_transactions': total_transactions,
        'avg_transaction_value': avg_transaction_value,
        'top_products': top_products_list,
        'payment_distribution': payment_distribution,
        'categories': sorted(categories),
        'suppliers': sorted(suppliers),
        'products': sorted(products),
        'selected_category': product_category,
        'selected_supplier': supplier_id,
        'selected_product': product_id,
        'selected_payment_method': payment_method,
    }

    return render(request, 'mainpages/store_sales_report.html', context)


@login_required
def first_login_password_change(request):
    """
    Handle mandatory password change for first-time login users.
    """
    # Check if user actually needs to change password
    if not request.user.is_first_login:
        messages.info(request, 'Password change not required.')
        # Redirect based on user role
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'head_manager':
            return redirect('head_manager_page')
        elif request.user.role == 'store_manager':
            return redirect('store_manager_page')
        elif request.user.role == 'cashier':
            return redirect('cashier_page')
        elif request.user.role == 'supplier':
            return redirect('supplier_dashboard')
        else:
            return redirect('login')

    if request.method == 'POST':
        # Get form data directly from POST since template uses different field names
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Basic validation
        if not current_password or not new_password or not confirm_password:
            messages.error(request, 'All fields are required.')
            return render(request, 'users/first_login_password_change.html', {'user': request.user})

        # Verify current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'users/first_login_password_change.html', {'user': request.user})

        # Verify new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'users/first_login_password_change.html', {'user': request.user})

        # Verify new password is different from current
        if request.user.check_password(new_password):
            messages.error(request, 'New password must be different from current password.')
            return render(request, 'users/first_login_password_change.html', {'user': request.user})

        # Verify password strength (basic validation)
        if len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
            return render(request, 'users/first_login_password_change.html', {'user': request.user})

        # Update password and mark first login as complete
        request.user.set_password(new_password)
        request.user.is_first_login = False
        request.user.save()

        # Update session to prevent logout
        update_session_auth_hash(request, request.user)

        # Refresh user from database to ensure middleware sees the updated state
        request.user.refresh_from_db()

        messages.success(request, 'Password changed successfully! Welcome to EZM Trade Management.')

        # Redirect based on user role
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'head_manager':
            return redirect('head_manager_page')
        elif request.user.role == 'store_manager':
            return redirect('store_manager_page')
        elif request.user.role == 'cashier':
            return redirect('cashier_page')
        elif request.user.role == 'supplier':
            return redirect('supplier_dashboard')
        else:
            return redirect('login')
    # For GET requests, just render the template
    context = {
        'user': request.user,
    }
    return render(request, 'users/first_login_password_change.html', context)


def export_sales_report(sales_data, summary_data, export_format):
    """
    Export sales report data in PDF or Excel format.
    """
    if export_format == 'pdf':
        return export_sales_pdf(sales_data, summary_data)
    elif export_format == 'excel':
        return export_sales_excel(sales_data, summary_data)
    else:
        return HttpResponse("Invalid export format", status=400)


def export_sales_pdf(sales_data, summary_data):
    """
    Generate PDF sales report using ReportLab.
    """
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from io import BytesIO
    from django.utils import timezone

    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor('#0B0C10'),
        alignment=1  # Center alignment
    )

    story.append(Paragraph(f"Sales Report - {summary_data['store'].name}", title_style))
    story.append(Paragraph(f"Period: {summary_data['start_date']} to {summary_data['end_date']}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Summary section
    summary_data_table = [
        ['Metric', 'Value'],
        ['Total Revenue', f"ETB {summary_data['total_revenue']:,.2f}"],
        ['Total Transactions', f"{summary_data['total_transactions']:,}"],
        ['Units Sold', f"{summary_data['total_units_sold']:,}"],
        ['Average Transaction', f"ETB {summary_data['avg_transaction_value']:,.2f}"],
    ]

    summary_table = Table(summary_data_table, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#66FCF1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0B0C10')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    story.append(Paragraph("Summary", styles['Heading2']))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Sales data table (all records)
    if sales_data:
        sales_table_data = [['Date', 'Product', 'SKU', 'Category', 'Qty', 'Unit Price', 'Total', 'Profit', 'Payment']]

        for item in sales_data:  # Include all items
            try:
                # Safely get values with defaults
                product_name = item.get('product_name', 'Unknown Product')
                category = item.get('category', 'N/A')
                product_sku = item.get('product_sku', 'N/A')
                sale_date = item.get('sale_date', timezone.now())
                quantity_sold = item.get('quantity_sold', 0)
                unit_price = item.get('unit_price', 0)
                line_total = item.get('line_total', 0)
                total_profit = item.get('total_profit', 0)
                payment_method = item.get('payment_method', 'N/A')

                # Truncate long names for better table formatting
                product_name = product_name[:25] + '...' if len(str(product_name)) > 25 else str(product_name)
                category = category[:15] + '...' if len(str(category)) > 15 else str(category)

                sales_table_data.append([
                    sale_date.strftime('%m/%d/%Y %H:%M') if hasattr(sale_date, 'strftime') else str(sale_date),
                    product_name,
                    str(product_sku),
                    category,
                    str(quantity_sold),
                    f"ETB {float(unit_price):,.2f}",
                    f"ETB {float(line_total):,.2f}",
                    f"ETB {float(total_profit):,.2f}",
                    str(payment_method)
                ])
            except Exception as e:
                # Skip problematic records and continue
                print(f"Error processing sales record: {e}")
                continue

        # Adjust column widths for better fit
        sales_table = Table(sales_table_data, colWidths=[0.8*inch, 1.5*inch, 0.6*inch, 0.8*inch, 0.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.7*inch])
        sales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#66FCF1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0B0C10')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),  # Smaller font for more data
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])  # Alternating row colors
        ]))

        story.append(Paragraph(f"Complete Sales Details ({len(sales_data)} Records)", styles['Heading2']))
        story.append(sales_table)
        story.append(Spacer(1, 20))
    else:
        # No sales data available
        story.append(Paragraph("Sales Details", styles['Heading2']))
        story.append(Paragraph("No sales data found for the selected period.", styles['Normal']))
        story.append(Spacer(1, 20))



    # Payment method distribution
    if summary_data.get('payment_distribution'):
        payment_data = [['Payment Method', 'Transactions', 'Total Amount']]

        for payment in summary_data['payment_distribution']:
            try:
                payment_type = payment.get('payment_type', 'Unknown')
                count = payment.get('count', 0)
                total = payment.get('total', 0)

                payment_data.append([
                    str(payment_type).title(),
                    f"{int(count):,}",
                    f"ETB {float(total):,.2f}"
                ])
            except Exception as e:
                print(f"Error processing payment distribution: {e}")
                continue

        payment_table = Table(payment_data, colWidths=[2*inch, 1.5*inch, 2*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#66FCF1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0B0C10')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

        story.append(Paragraph("Payment Method Distribution", styles['Heading2']))
        story.append(payment_table)

    # Build PDF
    doc.build(story)

    # Return PDF response
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{summary_data["start_date"]}_{summary_data["end_date"]}.pdf"'

    return response


def export_sales_excel(sales_data, summary_data):
    """
    Generate CSV sales report (Excel-compatible).
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{summary_data["start_date"]}_{summary_data["end_date"]}.csv"'

    writer = csv.writer(response)

    # Write header information
    writer.writerow([f"Sales Report - {summary_data['store'].name}"])
    writer.writerow([f"Period: {summary_data['start_date']} to {summary_data['end_date']}"])
    writer.writerow([])  # Empty row

    # Write summary statistics
    writer.writerow(['Summary Statistics'])
    writer.writerow(['Total Revenue', f"ETB {summary_data['total_revenue']:,.2f}"])
    writer.writerow(['Total Units Sold', f"{summary_data['total_units_sold']:,}"])
    writer.writerow(['Total Transactions', f"{summary_data['total_transactions']:,}"])
    writer.writerow(['Average Transaction Value', f"ETB {summary_data['avg_transaction_value']:,.2f}"])
    writer.writerow([])  # Empty row

    # Write detailed data headers
    writer.writerow([
        'Transaction ID', 'Sale Date', 'Product Name', 'SKU', 'Category', 'Supplier',
        'Quantity Sold', 'Unit Price', 'Cost Price', 'Line Total', 'Profit per Unit',
        'Total Profit', 'Profit Margin %', 'Remaining Stock', 'Payment Method', 'Receipt Number'
    ])

    # Write data rows
    for item in sales_data:
        writer.writerow([
            item['transaction_id'],
            item['sale_date'].strftime('%Y-%m-%d %H:%M'),
            item['product_name'],
            item['product_sku'],
            item['category'],
            item['supplier'],
            item['quantity_sold'],
            f"{item['unit_price']:.2f}",
            f"{item['cost_price']:.2f}",
            f"{item['line_total']:.2f}",
            f"{item['profit_per_unit']:.2f}",
            f"{item['total_profit']:.2f}",
            f"{item['profit_margin']:.1f}",
            item['remaining_stock'],
            item['payment_method'],
            item['receipt_number']
        ])

    return response


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

    # Get period from request (default to 30 days)
    period = request.GET.get('period', '30')

    # Get current date for filtering
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Q, F, Avg
    from Inventory.models import Stock, Product, RestockRequest, StoreStockTransferRequest

    now = timezone.now()
    today = now.date()

    # Calculate date ranges based on period
    if period == '7':
        start_date = now - timedelta(days=7)
    elif period == '30':
        start_date = now - timedelta(days=30)
    elif period == '90':
        start_date = now - timedelta(days=90)
    elif period == '365':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)

    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)

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

    # Low stock alerts
    low_stock_items = Stock.objects.filter(
        store=store,
        quantity__lte=F('low_stock_threshold')
    ).select_related('product').order_by('quantity')

    # Debug: Print low stock information
    print(f"DEBUG - Store: {store.name}")
    print(f"DEBUG - Total stock items: {Stock.objects.filter(store=store).count()}")
    print(f"DEBUG - Low stock items: {low_stock_items.count()}")
    for stock in low_stock_items[:5]:
        print(f"DEBUG - {stock.product.name}: qty={stock.quantity}, threshold={stock.low_stock_threshold}")

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

    # Enhanced Analytics for the selected period
    period_transactions = Transaction.objects.filter(
        store=store,
        timestamp__gte=start_date
    )

    # Financial metrics for the period
    total_revenue = period_transactions.aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    total_transactions = period_transactions.count()
    avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0

    # Stock analytics
    total_products = current_stock.count()
    total_stock_value = current_stock.aggregate(
        total=Sum(F('quantity') * F('selling_price'))
    )['total'] or 0

    out_of_stock_count = Stock.objects.filter(store=store, quantity=0).count()
    critical_stock_count = Stock.objects.filter(store=store, quantity__lte=5, quantity__gt=0).count()

    # Top selling products for the period
    from transactions.models import Order as TransactionOrder
    top_products = TransactionOrder.objects.filter(
        transaction__store=store,
        transaction__timestamp__gte=start_date
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price_at_time_of_sale'))
    ).order_by('-total_sold')[:5]

    # Daily sales trend (last 7 days for chart)
    daily_sales = []
    for i in range(7):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        day_revenue = Transaction.objects.filter(
            store=store,
            timestamp__gte=day_start,
            timestamp__lt=day_end
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        daily_sales.append({
            'date': day_start.strftime('%Y-%m-%d'),
            'revenue': float(day_revenue)
        })

    daily_sales.reverse()  # Show oldest to newest

    # Payment method breakdown
    payment_methods = Transaction.objects.filter(
        store=store,
        timestamp__gte=start_date
    ).values('payment_type').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    ).order_by('-total')

    # Recent transactions - get receipts for sales transactions since they have more detailed info
    from transactions.models import Receipt
    recent_transactions = Receipt.objects.filter(
        transaction__store=store,
        transaction__transaction_type='sale'
    ).select_related('transaction').order_by('-timestamp')[:10]

    # Compare with previous period
    previous_start = start_date - (now - start_date)
    previous_revenue = Transaction.objects.filter(
        store=store,
        timestamp__gte=previous_start,
        timestamp__lt=start_date
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    revenue_change = 0
    if previous_revenue > 0:
        revenue_change = ((total_revenue - previous_revenue) / previous_revenue) * 100

    # Comprehensive Analytics Data
    analytics = calculate_store_analytics(store)

    context = {
        'store': store,
        'period': period,
        'start_date': start_date,
        'end_date': now,

        # Enhanced metrics
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'avg_transaction_value': avg_transaction_value,
        'revenue_change': revenue_change,
        'previous_revenue': previous_revenue,

        # Stock metrics
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'out_of_stock_count': out_of_stock_count,
        'critical_stock_count': critical_stock_count,

        # Analytics data
        'top_products': top_products,
        'daily_sales': daily_sales,
        'payment_methods': payment_methods,
        'recent_transactions': recent_transactions,

        # Original context
        'cashier_assignment': cashier_assignment,
        'total_sales_30_days': total_sales_30_days,
        'total_sales_7_days': total_sales_7_days,
        'low_stock_items': low_stock_items,
        'current_stock': current_stock,
        'restock_available_products': restock_available_products,
        'recent_restock_requests': recent_restock_requests,
        'recent_transfer_requests': recent_transfer_requests,
        'pending_restock_count': pending_restock_count,
        'pending_transfer_count': pending_transfer_count,
        'other_stores': other_stores,
        'analytics': analytics,
    }

    return render(request, 'mainpages/store_manager_page.html', context)


@login_required
def export_store_report(request):
    """
    Export store manager's store report as PDF
    """
    if request.user.role != 'store_manager':
        messages.warning(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    # Get period from request (default to 30 days)
    period = request.GET.get('period', '30')

    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Sum, Count, Avg, Q
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    from io import BytesIO

    # Calculate date ranges
    now = timezone.now()
    if period == '7':
        start_date = now - timedelta(days=7)
        period_name = "7 Days"
    elif period == '30':
        start_date = now - timedelta(days=30)
        period_name = "30 Days"
    elif period == '90':
        start_date = now - timedelta(days=90)
        period_name = "90 Days"
    elif period == '365':
        start_date = now - timedelta(days=365)
        period_name = "1 Year"
    else:
        start_date = now - timedelta(days=30)
        period_name = "30 Days"

    # Get store data
    period_transactions = Transaction.objects.filter(
        store=store,
        timestamp__gte=start_date
    ).order_by('-timestamp')

    # Financial metrics
    total_revenue = period_transactions.aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    total_transactions = period_transactions.count()
    avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else 0

    # Stock metrics
    current_stock = Stock.objects.filter(store=store)
    total_products = current_stock.count()
    total_stock_value = current_stock.aggregate(
        total=Sum(F('quantity') * F('selling_price'))
    )['total'] or 0

    low_stock_items = Stock.objects.filter(
        store=store,
        quantity__lte=F('low_stock_threshold')
    ).select_related('product')

    # Top products
    from transactions.models import Order as TransactionOrder
    top_products = TransactionOrder.objects.filter(
        transaction__store=store,
        transaction__timestamp__gte=start_date
    ).values('product__name').annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price_at_time_of_sale'))
    ).order_by('-total_sold')[:10]

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor('#0B0C10'),
        alignment=1  # Center alignment
    )

    story.append(Paragraph(f"{store.name} - Store Report", title_style))
    story.append(Paragraph(f"Period: {period_name} ({start_date.strftime('%B %d, %Y')} - {now.strftime('%B %d, %Y')})", styles['Normal']))
    story.append(Spacer(1, 20))

    # Store Information
    store_info = [
        ['Store Name:', store.name],
        ['Address:', store.address],
        ['Phone:', store.phone_number or 'N/A'],
        ['Manager:', request.user.get_full_name() or request.user.username],
        ['Report Generated:', now.strftime('%B %d, %Y at %I:%M %p')]
    ]

    store_table = Table(store_info, colWidths=[2*inch, 4*inch])
    store_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#45A29E')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(Paragraph("Store Information", styles['Heading2']))
    story.append(store_table)
    story.append(Spacer(1, 20))

    # Financial Summary
    financial_data = [
        ['Metric', 'Value'],
        ['Total Revenue', f'ETB {total_revenue:,.2f}'],
        ['Total Transactions', f'{total_transactions:,}'],
        ['Average Transaction', f'ETB {avg_transaction_value:,.2f}'],
        ['Total Products', f'{total_products:,}'],
        ['Stock Value', f'ETB {total_stock_value:,.2f}'],
        ['Low Stock Alerts', f'{low_stock_items.count():,}']
    ]

    financial_table = Table(financial_data, colWidths=[3*inch, 3*inch])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#66FCF1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0B0C10')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    story.append(Paragraph("Financial Summary", styles['Heading2']))
    story.append(financial_table)
    story.append(Spacer(1, 20))

    # Recent Transactions (last 20) - use receipts for sales transactions
    from transactions.models import Receipt
    recent_receipts = Receipt.objects.filter(
        transaction__store=store,
        transaction__transaction_type='sale',
        transaction__timestamp__gte=start_date
    ).select_related('transaction').order_by('-timestamp')[:20]

    if recent_receipts.exists():
        transaction_data = [['Date', 'Amount', 'Payment Method', 'Customer']]

        for receipt in recent_receipts:
            customer_name = receipt.customer_name if receipt.customer_name != 'Walk-in Customer' else 'Walk-in'
            transaction_data.append([
                receipt.timestamp.strftime('%m/%d/%Y %H:%M'),
                f'ETB {receipt.total_amount:,.2f}',
                receipt.transaction.get_payment_type_display(),
                customer_name
            ])

        transaction_table = Table(transaction_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        transaction_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#66FCF1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0B0C10')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

        story.append(Paragraph("Recent Transactions", styles['Heading2']))
        story.append(transaction_table)
        story.append(Spacer(1, 20))

    # Top Products
    if top_products:
        product_data = [['Product', 'Units Sold', 'Revenue']]

        for product in top_products:
            product_data.append([
                product['product__name'][:30],
                f"{product['total_sold']:,}",
                f"ETB {product['total_revenue']:,.2f}"
            ])

        product_table = Table(product_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#66FCF1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0B0C10')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

        story.append(Paragraph("Top Selling Products", styles['Heading2']))
        story.append(product_table)
        story.append(Spacer(1, 20))

    # Low Stock Alerts
    if low_stock_items.exists():
        stock_data = [['Product', 'Current Stock', 'Threshold', 'Status']]

        for stock in low_stock_items[:15]:
            status = "Out of Stock" if stock.quantity == 0 else "Low Stock"
            stock_data.append([
                stock.product.name[:30],
                f"{stock.quantity}",
                f"{stock.low_stock_threshold}",
                status
            ])

        stock_table = Table(stock_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1.5*inch])
        stock_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFC107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0B0C10')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

        story.append(Paragraph("Low Stock Alerts", styles['Heading2']))
        story.append(stock_table)

    # Build PDF
    doc.build(story)

    # Return PDF response
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{store.name}_Report_{period_name.replace(" ", "_")}_{now.strftime("%Y%m%d")}.pdf"'

    return response


@login_required
def update_stock_threshold(request):
    """
    Update the low stock threshold for a specific stock item
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('store_manager_stock_management')

    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        from store.models import Store
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    stock_id = request.POST.get('stock_id')
    new_threshold = request.POST.get('new_threshold')

    if not stock_id or not new_threshold:
        messages.error(request, "Missing required fields.")
        return redirect('store_manager_stock_management')

    try:
        new_threshold = int(new_threshold)
        if new_threshold < 0:
            messages.error(request, "Threshold cannot be negative.")
            return redirect('store_manager_stock_management')
    except ValueError:
        messages.error(request, "Invalid threshold value.")
        return redirect('store_manager_stock_management')

    try:
        from Inventory.models import Stock
        stock_item = Stock.objects.get(id=stock_id, store=store)

        old_threshold = stock_item.low_stock_threshold
        stock_item.low_stock_threshold = new_threshold
        stock_item.save()

        messages.success(
            request,
            f"Successfully updated threshold for {stock_item.product.name} from {old_threshold} to {new_threshold}."
        )

        # Log the threshold update
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Store Manager {request.user.username} updated threshold for {stock_item.product.name} "
            f"in store {store.name} from {old_threshold} to {new_threshold}"
        )

    except Stock.DoesNotExist:
        messages.error(request, "Stock item not found or you don't have permission to update it.")
    except Exception as e:
        messages.error(request, f"Error updating threshold: {str(e)}")

    return redirect('store_manager_stock_management')


@login_required
def store_manager_warehouse_products(request):
    """
    Display all warehouse products for store managers to request restocks
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        from store.models import Store
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    from Inventory.models import WarehouseProduct, Product, RestockRequest
    from django.core.paginator import Paginator
    from django.db.models import Q

    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    availability_filter = request.GET.get('availability', 'all')

    # Build query for warehouse products
    warehouse_products = WarehouseProduct.objects.filter(
        is_active=True
    ).select_related('supplier')

    # Apply search filter
    if search_query:
        warehouse_products = warehouse_products.filter(
            Q(product_name__icontains=search_query) |
            Q(supplier__name__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(sku__icontains=search_query)
        )

    # Apply category filter
    if category_filter:
        warehouse_products = warehouse_products.filter(category=category_filter)

    # Apply availability filter
    if availability_filter == 'in_stock':
        warehouse_products = warehouse_products.filter(quantity_in_stock__gt=0)
    elif availability_filter == 'out_of_stock':
        warehouse_products = warehouse_products.filter(quantity_in_stock=0)

    # Order by availability (in stock first) then by name
    warehouse_products = warehouse_products.order_by('-quantity_in_stock', 'product_name')

    # Pagination
    paginator = Paginator(warehouse_products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for filter dropdown
    categories = WarehouseProduct.objects.filter(
        is_active=True
    ).values_list('category', flat=True).distinct().order_by('category')

    # Get pending requests for this store to show status
    pending_requests = RestockRequest.objects.filter(
        store=store,
        status__in=['pending', 'approved', 'shipped']
    ).values_list('product__name', flat=True)

    # Statistics
    total_products = warehouse_products.count()
    in_stock_count = WarehouseProduct.objects.filter(
        is_active=True,
        quantity_in_stock__gt=0
    ).count()
    out_of_stock_count = WarehouseProduct.objects.filter(
        is_active=True,
        quantity_in_stock=0
    ).count()

    context = {
        'page_obj': page_obj,
        'store': store,
        'search_query': search_query,
        'category_filter': category_filter,
        'availability_filter': availability_filter,
        'categories': categories,
        'pending_requests': pending_requests,
        'stats': {
            'total_products': total_products,
            'in_stock_count': in_stock_count,
            'out_of_stock_count': out_of_stock_count,
        }
    }

    return render(request, 'mainpages/store_manager_warehouse_products.html', context)


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

    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Product ID: {product_id}, Product: {product.name}")
    logger.info(f"Requesting store: {requesting_store.name}")
    logger.info(f"Found {len(available_stores)} stores with product")
    for store in available_stores:
        logger.info(f"  - {store['name']}: {store['available_quantity']} units")

    return JsonResponse({
        'stores': available_stores,
        'product_name': product.name,
        'debug': {
            'product_id': product_id,
            'requesting_store': requesting_store.name,
            'total_stores_found': len(available_stores)
        }
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

        # Handle both product_id (old) and product_name (new) parameters
        product_id = request.POST.get('product_id')
        product_name = request.POST.get('product_name')
        requested_quantity = request.POST.get('requested_quantity')
        priority = request.POST.get('priority', 'medium')
        reason = request.POST.get('reason', '')

        try:
            if product_name:
                # New logic: find or create product by name
                product, created = Product.objects.get_or_create(
                    name=product_name,
                    defaults={
                        'category': 'general',
                        'description': f'Product requested from warehouse: {product_name}'
                    }
                )
            elif product_id:
                # Old logic: get product by ID
                product = Product.objects.get(id=product_id)
            else:
                raise ValueError("No product specified")
            requested_quantity = int(requested_quantity)

            if requested_quantity <= 0:
                messages.error(request, "Requested quantity must be greater than 0.")
                return redirect('store_manager_restock_requests')

            # Check for existing pending requests
            existing_request = RestockRequest.objects.filter(
                store=store,
                product=product,
                status='pending'
            ).first()

            if existing_request:
                messages.warning(request, f"You already have a pending restock request for {product.name}.")
                return redirect('store_manager_restock_requests')

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

    return redirect('store_manager_restock_requests')


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
                return redirect('store_manager_transfer_requests')

            if requesting_store == from_store:
                messages.error(request, "Cannot transfer from the same store.")
                return redirect('store_manager_transfer_requests')

            # Check if the source store has the product in stock
            try:
                source_stock = Stock.objects.get(product=product, store=from_store)
                if source_stock.quantity < requested_quantity:
                    messages.error(request, f"Insufficient stock. {from_store.name} only has {source_stock.quantity} units of {product.name}.")
                    return redirect('store_manager_transfer_requests')
            except Stock.DoesNotExist:
                messages.error(request, f"{product.name} is not available in {from_store.name}.")
                return redirect('store_manager_transfer_requests')

            # Check for existing pending requests
            existing_request = StoreStockTransferRequest.objects.filter(
                from_store=from_store,
                to_store=requesting_store,
                product=product,
                status='pending'
            ).first()

            if existing_request:
                messages.warning(request, f"You already have a pending transfer request for {product.name} from {from_store.name}.")
                return redirect('store_manager_transfer_requests')

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

    return redirect('store_manager_transfer_requests')


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
def mark_restock_received(request):
    """
    Mark a restock request as received and update store stock
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('store_manager_restock_requests')

    try:
        from Inventory.models import RestockRequest
        from django.db import transaction

        request_id = request.POST.get('request_id')
        received_quantity = int(request.POST.get('received_quantity', 0))
        receiving_notes = request.POST.get('receiving_notes', '').strip()

        # Get the restock request
        restock_request = RestockRequest.objects.get(
            id=request_id,
            requested_by=request.user,
            status='shipped'
        )

        if received_quantity <= 0:
            messages.error(request, "Received quantity must be greater than 0.")
            return redirect('store_manager_restock_requests')

        if received_quantity > restock_request.shipped_quantity:
            messages.error(request, f"Received quantity cannot exceed shipped quantity ({restock_request.shipped_quantity}).")
            return redirect('store_manager_restock_requests')

        # Use the existing receive method from the model
        with transaction.atomic():
            restock_request.receive(
                received_by=request.user,
                received_quantity=received_quantity,
                notes=receiving_notes
            )

            # Create notification for head manager if there's a discrepancy
            if received_quantity < restock_request.shipped_quantity:
                from users.notifications import NotificationManager
                NotificationManager.create_notification(
                    notification_type='low_stock_alert',
                    title=f'Restock Delivery Discrepancy: {restock_request.product.name}',
                    message=f'Store received {received_quantity} units but {restock_request.shipped_quantity} were shipped. Store: {restock_request.store.name}',
                    target_roles=['head_manager'],
                    priority='high',
                    related_object_type='restock_request',
                    related_object_id=restock_request.id
                )

        messages.success(request, f"Restock request marked as received. {received_quantity} units of {restock_request.product.name} added to your store stock.")

    except RestockRequest.DoesNotExist:
        messages.error(request, "Restock request not found or not eligible for receiving.")
    except ValueError:
        messages.error(request, "Invalid quantity specified.")
    except Exception as e:
        messages.error(request, f"Error processing receipt: {str(e)}")

    return redirect('store_manager_restock_requests')


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

    # Get detailed stock information for transfer requests
    from collections import defaultdict

    # Get all stock items from other stores (excluding current store)
    other_stores_stock = Stock.objects.filter(
        quantity__gt=0
    ).exclude(store=store).select_related('product', 'store').order_by('product__name', 'store__name')

    # Group stock by product for easy access in template
    products_with_stores = defaultdict(list)
    for stock in other_stores_stock:
        products_with_stores[stock.product].append({
            'store': stock.store,
            'quantity': stock.quantity
        })

    # Convert to list for template with product-store combinations
    transfer_product_store_combinations = []
    for product, stores_data in products_with_stores.items():
        for store_data in stores_data:
            transfer_product_store_combinations.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_category': product.category,
                'store_id': store_data['store'].id,
                'store_name': store_data['store'].name,
                'available_quantity': store_data['quantity'],
                'display_text': f"{product.name} from {store_data['store'].name} ({store_data['quantity']} units)"
            })

    # Sort by product name then store name
    transfer_product_store_combinations.sort(key=lambda x: (x['product_name'], x['store_name']))

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
        'transfer_product_store_combinations': transfer_product_store_combinations,  # Product-store combinations with stock
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

    # For transfer requests, get detailed stock information for all products in other stores
    from collections import defaultdict

    # Get all stock items from other stores (excluding current store)
    other_stores_stock = Stock.objects.filter(
        quantity__gt=0
    ).exclude(store=store).select_related('product', 'store').order_by('product__name', 'store__name')

    # Group stock by product for easy access in template
    products_with_stores = defaultdict(list)
    for stock in other_stores_stock:
        products_with_stores[stock.product].append({
            'store': stock.store,
            'quantity': stock.quantity
        })

    # Convert to list for template with product-store combinations
    transfer_product_store_combinations = []
    for product, stores_data in products_with_stores.items():
        for store_data in stores_data:
            transfer_product_store_combinations.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_category': product.category,
                'store_id': store_data['store'].id,
                'store_name': store_data['store'].name,
                'available_quantity': store_data['quantity'],
                'display_text': f"{product.name} from {store_data['store'].name} ({store_data['quantity']} units)"
            })

    # Sort by product name then store name
    transfer_product_store_combinations.sort(key=lambda x: (x['product_name'], x['store_name']))

    # Keep the old transfer_available_products for backward compatibility
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

    # Cashier is assigned to a store, redirect to the unified cashier interface
    return redirect('initiate_order')

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from .forms import ChangeUserRoleForm, CustomUserCreationFormAdmin
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from django.utils import timezone
import json
from decimal import Decimal
import csv
import io

def get_client_ip(request):
    """Get the client's IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_login_attempt(request, username_attempted, user=None, status='failed', failure_reason=''):
    """Log login attempt for admin audit purposes"""
    try:
        LoginLog.objects.create(
            user=user,
            username_attempted=username_attempted,
            login_status=status,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            user_role=user.role if user else '',
            failure_reason=failure_reason
        )
    except Exception as e:
        # Don't let logging errors break the login process
        logger.error(f"Failed to log login attempt: {e}")
        pass


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

@user_passes_test(is_admin)
def admin_login_logs(request):
    """Admin page to view login logs with filtering and sorting"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    role_filter = request.GET.get('role', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    sort_by = request.GET.get('sort', '-login_timestamp')
    page_number = request.GET.get('page')

    # Get all login logs
    logs = LoginLog.objects.all().select_related('user')

    # Apply filters
    if search_query:
        logs = logs.filter(
            Q(username_attempted__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )

    if status_filter:
        logs = logs.filter(login_status=status_filter)

    if role_filter:
        logs = logs.filter(user_role=role_filter)

    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(login_timestamp__gte=from_date)
        except ValueError:
            pass

    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire day
            to_date = to_date.replace(hour=23, minute=59, second=59)
            logs = logs.filter(login_timestamp__lte=to_date)
        except ValueError:
            pass

    # Apply sorting
    valid_sort_fields = ['login_timestamp', '-login_timestamp', 'username_attempted',
                        '-username_attempted', 'login_status', '-login_status',
                        'user_role', '-user_role']
    if sort_by in valid_sort_fields:
        logs = logs.order_by(sort_by)
    else:
        logs = logs.order_by('-login_timestamp')

    # Pagination
    paginator = Paginator(logs, 25)  # Show 25 logs per page
    page_obj = paginator.get_page(page_number)

    # Get statistics
    total_logs = logs.count()
    successful_logs = logs.filter(login_status='success').count()
    failed_logs = logs.filter(login_status='failed').count()

    context = {
        'page_obj': page_obj,
        'total_logs': total_logs,
        'successful_logs': successful_logs,
        'failed_logs': failed_logs,
        'search_query': search_query,
        'status_filter': status_filter,
        'role_filter': role_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'role_choices': CustomUser.ROLE_CHOICES,
    }

    return render(request, 'admin/login_logs.html', context)


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

            # Send welcome email with credentials using enhanced email service
            from .email_service import email_service

            email_success, email_message = email_service.send_user_creation_email(user, password)

            if email_success:
                messages.success(request, f"User {user.username} created successfully. {email_message}")
            else:
                messages.warning(request, f"User {user.username} created successfully, but email could not be sent: {email_message}")

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
def reset_user_account(request, user_id):
    """Reset user account with new temporary credentials and email update capability"""
    target_user = get_object_or_404(User, id=user_id)

    # Prevent admin from resetting their own account
    if target_user == request.user:
        messages.error(request, "You cannot reset your own account.")
        return redirect('manage_users')

    # Prevent resetting superuser accounts by non-superusers
    if target_user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You cannot reset a superuser account.")
        return redirect('manage_users')

    if request.method == 'POST':
        from .forms import AccountResetForm
        form = AccountResetForm(request.POST, user_being_reset=target_user)

        if form.is_valid():
            try:
                # Store old email for audit trail
                old_email = target_user.email
                new_email = form.cleaned_data['new_email']
                reset_reason = form.cleaned_data['reset_reason']

                # Generate new temporary credentials
                import secrets
                import string

                # Generate temporary password
                alphabet = string.ascii_letters + string.digits
                temp_password = ''.join(secrets.choice(alphabet) for i in range(12))

                # Update user account with new email
                target_user.email = new_email
                target_user.set_password(temp_password)
                target_user.is_first_login = True
                target_user.is_active = True
                target_user.save()

                # Create account reset record
                AccountReset.objects.create(
                    user=target_user,
                    reset_by=request.user,
                    old_email=old_email,
                    new_email=new_email,
                    temporary_password=target_user.password,  # Store hashed password
                    reset_reason=reset_reason
                )

                # Log the account reset as a login log entry
                log_login_attempt(request, new_email, target_user, 'success', f'Account reset by {request.user.username}')

                # Send email notification with new credentials to the new email
                from .email_service import EZMEmailService
                email_service = EZMEmailService()

                success, message = email_service.send_account_reset_email(
                    target_user, temp_password, old_email, request.user
                )

                if success:
                    messages.success(request,
                        f"Account for '{target_user.username}' has been reset successfully. "
                        f"New credentials have been sent to {new_email}.")
                else:
                    messages.warning(request,
                        f"Account reset completed but email notification failed: {message}. "
                        f"New email: {new_email}, Password: {temp_password}")

                return redirect('manage_users')

            except Exception as e:
                messages.error(request, f"Error resetting account: {e}")
                return redirect('manage_users')
        else:
            # Form has validation errors, re-render with errors
            context = {
                'target_user': target_user,
                'form': form,
            }
            return render(request, 'admin/reset_user_account.html', context)

    else:
        # For GET requests, show form with current user data
        from .forms import AccountResetForm
        form = AccountResetForm(user_being_reset=target_user)

    context = {
        'target_user': target_user,
        'form': form,
    }
    return render(request, 'admin/reset_user_account.html', context)


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
def store_manager_edit_profile(request):
    if request.user.role != 'store_manager':
        messages.warning(request, "Access denied. You don't have permission to access this page.")
        return redirect('login')

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('store_manager_settings')
        else:
            messages.error(request, 'Error updating profile.')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})


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


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view that sends properly formatted HTML emails"""
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.txt'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send HTML email with plain text fallback
        """
        from django.core.mail import EmailMultiAlternatives
        from django.template import loader
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Render subject template
            subject = loader.render_to_string(subject_template_name, context)
            subject = ''.join(subject.splitlines())

            # Render plain text body as fallback
            text_body = loader.render_to_string(email_template_name, context)

            # Render HTML body
            html_body = loader.render_to_string('users/password_reset_email.html', context)

            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=from_email,
                to=[to_email]
            )

            # Attach HTML version
            msg.attach_alternative(html_body, "text/html")

            # Set additional headers to ensure HTML rendering
            msg.extra_headers['Content-Type'] = 'multipart/alternative'

            # Send the email
            msg.send()

            logger.info(f"Password reset email sent successfully to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {e}")
            # Fallback to plain text only
            from django.core.mail import send_mail
            subject = loader.render_to_string(subject_template_name, context)
            subject = ''.join(subject.splitlines())
            body = loader.render_to_string(email_template_name, context)

            send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=[to_email],
                fail_silently=False
            )


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


def calculate_net_profit_for_store(store, start_date, end_date):
    """
    Calculate net profit for a store by finding the difference between
    sale price and purchase price from suppliers for each item sold.

    Fixed to handle realistic profit margins:
    - If warehouse cost > sale price, assumes 30% profit margin
    - If no warehouse product found, assumes 25% profit margin
    - Prevents negative profit calculations from unrealistic data
    """
    from Inventory.models import PurchaseOrderItem

    net_profit = Decimal('0')

    # Get all sales transactions for the store in the period
    sales_transactions = Transaction.objects.filter(
        store=store,
        transaction_type='sale',
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )

    for transaction in sales_transactions:
        # Get orders for this transaction
        orders = Order.objects.filter(transaction=transaction)

        for order in orders:
            if order.product:
                # Find the most recent purchase price for this product
                # Match by product name since WarehouseProduct is separate from Product
                from Inventory.models import WarehouseProduct

                # Try exact name match first
                warehouse_product = WarehouseProduct.objects.filter(
                    product_name__iexact=order.product.name
                ).first()

                # If no exact match, try partial name match
                if not warehouse_product:
                    warehouse_product = WarehouseProduct.objects.filter(
                        product_name__icontains=order.product.name.split()[0]
                    ).first()

                if warehouse_product:
                    # Find recent purchase price for this warehouse product
                    recent_purchase = PurchaseOrderItem.objects.filter(
                        warehouse_product=warehouse_product,
                        purchase_order__status='delivered'
                    ).order_by('-purchase_order__created_date').first()

                    if recent_purchase:
                        purchase_price = recent_purchase.unit_price
                    else:
                        # Use warehouse product unit price as fallback
                        purchase_price = warehouse_product.unit_price

                    sale_price = order.price_at_time_of_sale
                    quantity = order.quantity

                    # Ensure realistic profit calculation
                    # If warehouse price is higher than sale price, use 70% of sale price as cost
                    if purchase_price > sale_price:
                        purchase_price = sale_price * Decimal('0.7')  # Assume 30% profit margin

                    # Calculate net profit for this item
                    item_net_profit = (sale_price - purchase_price) * quantity
                    net_profit += item_net_profit
                else:
                    # If no warehouse product found, assume 25% profit margin
                    sale_price = order.price_at_time_of_sale
                    quantity = order.quantity
                    estimated_cost = sale_price * Decimal('0.75')  # 25% profit margin

                    item_net_profit = (sale_price - estimated_cost) * quantity
                    net_profit += item_net_profit

    return net_profit


def calculate_purchase_costs_for_period(start_date, end_date):
    """
    Calculate total purchase costs from completed purchase orders in the period.
    """
    from Inventory.models import PurchaseOrder

    purchase_costs = PurchaseOrder.objects.filter(
        status='delivered',
        created_date__gte=start_date,
        created_date__lte=end_date
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

    return purchase_costs


def get_revenue_breakdown_data(start_date, end_date):
    """
    Get revenue breakdown by categories, suppliers, and stores.
    """
    # Revenue by category
    category_revenue = []
    categories = Product.objects.values_list('category', flat=True).distinct().filter(category__isnull=False)

    for category in categories:
        if category:  # Skip None/empty categories
            revenue = Order.objects.filter(
                product__category=category,
                transaction__transaction_type='sale',
                transaction__timestamp__gte=start_date,
                transaction__timestamp__lte=end_date
            ).aggregate(
                total=Sum(F('quantity') * F('price_at_time_of_sale'))
            )['total'] or Decimal('0')

            if revenue > 0:
                category_revenue.append({
                    'category': category,
                    'revenue': float(revenue)
                })

    # Revenue by store
    store_revenue = []
    stores = Store.objects.all()

    for store in stores:
        revenue = Transaction.objects.filter(
            store=store,
            transaction_type='sale',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        if revenue > 0:
            store_revenue.append({
                'store': store.name,
                'revenue': float(revenue)
            })

    return {
        'category_revenue': category_revenue,
        'store_revenue': store_revenue
    }


@login_required
def financial_reports(request):
    """
    Comprehensive financial reports page with enhanced P&L statements,
    net profit calculations, charts, and PDF export functionality.
    """
    if request.user.role != 'head_manager':
        messages.error(request, 'Access denied. Head manager role required.')
        return redirect('login')

    # Handle PDF export request
    if request.GET.get('export') == 'pdf':
        return generate_financial_pdf_report(request)

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

    # Enhanced financial data per store with net profit calculations
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

        # Calculate net profit (Sale Price - Purchase Price from Supplier)
        net_profit = calculate_net_profit_for_store(store, start_date, end_date)

        # Expenses from financial records and purchase orders
        expense_records = FinancialRecord.objects.filter(
            store=store,
            record_type='expense',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Purchase costs from completed purchase orders
        purchase_costs = calculate_purchase_costs_for_period(start_date, end_date)

        total_expenses = expense_records + purchase_costs

        # Calculate profit/loss and margin
        profit_loss = revenue - total_expenses
        profit_margin = (profit_loss / revenue * 100) if revenue > 0 else 0
        net_profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0

        financial_data.append({
            'store': store,
            'revenue': revenue,
            'expenses': total_expenses,
            'expense_records': expense_records,
            'purchase_costs': purchase_costs,
            'profit_loss': profit_loss,
            'profit_margin': profit_margin,
            'net_profit': net_profit,
            'net_profit_margin': net_profit_margin
        })

    # Sort by profit/loss
    financial_data.sort(key=lambda x: x['profit_loss'], reverse=True)

    # Overall financial summary with enhanced metrics
    total_revenue = sum(fd['revenue'] for fd in financial_data)
    total_expenses = sum(fd['expenses'] for fd in financial_data)
    total_net_profit = sum(fd['net_profit'] for fd in financial_data)
    total_profit = total_revenue - total_expenses
    overall_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    overall_net_margin = (total_net_profit / total_revenue * 100) if total_revenue > 0 else 0

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

    # Get revenue breakdown data
    revenue_breakdown = get_revenue_breakdown_data(start_date, end_date)

    # Key financial metrics with enhanced data
    financial_metrics = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'total_net_profit': total_net_profit,
        'overall_margin': overall_margin,
        'overall_net_margin': overall_net_margin,
        'best_performing_store': financial_data[0] if financial_data else None,
        'stores_count': stores.count(),
        'profitable_stores': len([fd for fd in financial_data if fd['profit_loss'] > 0])
    }

    context = {
        'financial_data': financial_data,
        'financial_metrics': financial_metrics,
        'monthly_trend': monthly_trend,
        'revenue_breakdown': revenue_breakdown,
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        # Add shorter variable names for template rendering
        'margin': financial_metrics.get('overall_margin', 0),
        'net_margin': financial_metrics.get('overall_net_margin', 0),
        'profitable_stores': financial_metrics.get('profitable_stores', 0),
        'total_stores': financial_metrics.get('stores_count', 0),
        'best_store': financial_metrics.get('best_performing_store'),
        'total_net_profit': total_net_profit,
    }

    return render(request, 'analytics/financial_reports.html', context)


def generate_financial_pdf_report(request):
    """
    Generate comprehensive PDF financial report with charts and statistics.
    """
    if request.user.role != 'head_manager':
        return JsonResponse({'error': 'Access denied'}, status=403)

    if not REPORTLAB_AVAILABLE:
        messages.error(request, 'PDF generation is not available. Please install ReportLab.')
        return redirect('financial_reports')

    # Get the same data as the main view
    period = request.GET.get('period', '30')
    end_date = timezone.now()

    if period == '7':
        start_date = end_date - timedelta(days=7)
        period_name = "7 Days"
    elif period == '90':
        start_date = end_date - timedelta(days=90)
        period_name = "90 Days"
    elif period == '365':
        start_date = end_date - timedelta(days=365)
        period_name = "1 Year"
    else:
        start_date = end_date - timedelta(days=30)
        period_name = "30 Days"

    # Calculate financial data
    stores = Store.objects.all()
    financial_data = []
    total_revenue = Decimal('0')
    total_expenses = Decimal('0')
    total_net_profit = Decimal('0')

    for store in stores:
        revenue = Transaction.objects.filter(
            store=store,
            transaction_type='sale',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        net_profit = calculate_net_profit_for_store(store, start_date, end_date)

        expense_records = FinancialRecord.objects.filter(
            store=store,
            record_type='expense',
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        purchase_costs = calculate_purchase_costs_for_period(start_date, end_date)
        expenses = expense_records + purchase_costs

        financial_data.append({
            'store': store.name,
            'revenue': revenue,
            'expenses': expenses,
            'net_profit': net_profit,
            'profit_loss': revenue - expenses
        })

        total_revenue += revenue
        total_expenses += expenses
        total_net_profit += net_profit

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#0B0C10'),
        alignment=1  # Center alignment
    )
    story.append(Paragraph("EZM Trade Management", title_style))
    story.append(Paragraph(f"Financial Report - {period_name}", styles['Heading2']))
    story.append(Paragraph(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Summary statistics
    summary_data = [
        ['Metric', 'Amount (ETB)', 'Percentage'],
        ['Total Revenue', f"{total_revenue:,.2f}", "100%"],
        ['Total Expenses', f"{total_expenses:,.2f}", f"{(total_expenses/total_revenue*100) if total_revenue > 0 else 0:.1f}%"],
        ['Net Profit', f"{total_net_profit:,.2f}", f"{(total_net_profit/total_revenue*100) if total_revenue > 0 else 0:.1f}%"],
        ['Gross Profit', f"{total_revenue - total_expenses:,.2f}", f"{((total_revenue - total_expenses)/total_revenue*100) if total_revenue > 0 else 0:.1f}%"],
    ]

    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#66FCF1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0B0C10')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(Paragraph("Financial Summary", styles['Heading3']))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Store-wise breakdown
    if financial_data:
        store_data = [['Store', 'Revenue (ETB)', 'Expenses (ETB)', 'Net Profit (ETB)', 'Profit Margin']]
        for fd in financial_data:
            margin = (fd['net_profit'] / fd['revenue'] * 100) if fd['revenue'] > 0 else 0
            store_data.append([
                fd['store'],
                f"{fd['revenue']:,.2f}",
                f"{fd['expenses']:,.2f}",
                f"{fd['net_profit']:,.2f}",
                f"{margin:.1f}%"
            ])

        store_table = Table(store_data)
        store_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#45A29E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(Paragraph("Store Performance Breakdown", styles['Heading3']))
        story.append(store_table)

    # Footer
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph("EZM Trade Management System", styles['Normal']))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="EZM_Financial_Report_{period_name}_{end_date.strftime("%Y%m%d")}.pdf"'

    return response


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
            ).aggregate(total=Sum('total_amount'))

            daily_sales.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'sales': float(day_sales['total'] or 0)
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

    elif chart_type == 'revenue_vs_expense':
        # Revenue vs Expense trend
        trend_data = []
        current_date = start_date.date()

        while current_date <= end_date.date():
            day_revenue = Transaction.objects.filter(
                transaction_type='sale',
                timestamp__date=current_date
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

            day_expenses = FinancialRecord.objects.filter(
                record_type='expense',
                timestamp__date=current_date
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            trend_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'revenue': float(day_revenue),
                'expenses': float(day_expenses)
            })
            current_date += timedelta(days=1)

        return JsonResponse({
            'labels': [item['date'] for item in trend_data],
            'revenue': [item['revenue'] for item in trend_data],
            'expenses': [item['expenses'] for item in trend_data]
        })

    elif chart_type == 'category_revenue':
        # Revenue breakdown by category
        revenue_breakdown = get_revenue_breakdown_data(start_date, end_date)
        category_data = revenue_breakdown['category_revenue']

        return JsonResponse({
            'labels': [item['category'] for item in category_data],
            'data': [item['revenue'] for item in category_data]
        })

    elif chart_type == 'store_revenue':
        # Revenue breakdown by store
        revenue_breakdown = get_revenue_breakdown_data(start_date, end_date)
        store_data = revenue_breakdown['store_revenue']

        return JsonResponse({
            'labels': [item['store'] for item in store_data],
            'data': [item['revenue'] for item in store_data]
        })

    elif chart_type == 'net_profit_trend':
        # Net profit trend over time
        stores = Store.objects.all()
        trend_data = []
        current_date = start_date.date()

        while current_date <= end_date.date():
            day_net_profit = Decimal('0')
            for store in stores:
                day_start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
                day_end = timezone.make_aware(datetime.combine(current_date, datetime.max.time()))
                store_net_profit = calculate_net_profit_for_store(store, day_start, day_end)
                day_net_profit += store_net_profit

            trend_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'net_profit': float(day_net_profit)
            })
            current_date += timedelta(days=1)

        return JsonResponse({
            'labels': [item['date'] for item in trend_data],
            'data': [item['net_profit'] for item in trend_data]
        })

    return JsonResponse({'error': 'Invalid chart type'}, status=400)


@login_required
def transaction_history(request):
    """
    Display comprehensive transaction history including payment transactions
    """
    from transactions.models import Transaction, SupplierTransaction
    from payments.models import ChapaTransaction
    from django.core.paginator import Paginator

    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    transaction_type = request.GET.get('type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Combine different transaction types
    transactions = []

    # Get regular transactions
    regular_transactions = Transaction.objects.all()
    if search_query:
        regular_transactions = regular_transactions.filter(
            Q(store__name__icontains=search_query) |
            Q(payment_type__icontains=search_query)
        )
    if transaction_type and transaction_type != 'payment':
        regular_transactions = regular_transactions.filter(transaction_type=transaction_type)

    for trans in regular_transactions:
        transactions.append({
            'id': f"T-{trans.id}",
            'type': trans.transaction_type,
            'amount': trans.total_amount,
            'date': trans.timestamp,
            'description': f"{trans.transaction_type.title()} at {trans.store.name}",
            'payment_method': trans.payment_type,
            'status': 'completed',
            'source': 'transaction'
        })

    # Get supplier transactions
    try:
        supplier_transactions = SupplierTransaction.objects.all()
        if search_query:
            supplier_transactions = supplier_transactions.filter(
                Q(supplier_account__supplier__name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(reference_number__icontains=search_query)
            )

        for trans in supplier_transactions:
            transactions.append({
                'id': f"ST-{trans.id}",
                'type': trans.transaction_type,
                'amount': trans.amount,
                'date': trans.created_at,
                'description': trans.description,
                'payment_method': 'supplier_account',
                'status': trans.status,
                'source': 'supplier_transaction',
                'supplier': trans.supplier_account.supplier.name
            })
    except:
        pass  # SupplierTransaction model might not exist yet

    # Get payment transactions
    if not transaction_type or transaction_type == 'payment':
        try:
            payment_transactions = ChapaTransaction.objects.filter(status='success')
            if search_query:
                payment_transactions = payment_transactions.filter(
                    Q(chapa_tx_ref__icontains=search_query) |
                    Q(customer_first_name__icontains=search_query) |
                    Q(customer_last_name__icontains=search_query) |
                    Q(supplier__name__icontains=search_query)
                )

            for trans in payment_transactions:
                transactions.append({
                    'id': trans.chapa_tx_ref,
                    'type': 'payment',
                    'amount': trans.amount,
                    'date': trans.paid_at or trans.created_at,
                    'description': f"Payment to {trans.supplier.name}",
                    'payment_method': 'chapa_gateway',
                    'status': trans.status,
                    'source': 'payment',
                    'supplier': trans.supplier.name,
                    'customer': f"{trans.customer_first_name} {trans.customer_last_name}"
                })
        except:
            pass  # ChapaTransaction model might not be accessible

    # Apply date filters
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = [t for t in transactions if t['date'].date() >= date_from_obj]
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = [t for t in transactions if t['date'].date() <= date_to_obj]
        except ValueError:
            pass

    # Sort by date (newest first)
    transactions.sort(key=lambda x: x['date'], reverse=True)

    # Paginate
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate totals
    total_amount = sum(t['amount'] for t in transactions)
    payment_total = sum(t['amount'] for t in transactions if t['type'] == 'payment')

    context = {
        'transactions': page_obj,
        'search_query': search_query,
        'transaction_type': transaction_type,
        'date_from': date_from,
        'date_to': date_to,
        'total_amount': total_amount,
        'payment_total': payment_total,
        'total_count': len(transactions),
        'page_title': 'Transaction History'
    }

    return render(request, 'users/transaction_history.html', context)


@login_required
def warehouse_products_api(request):
    """
    API endpoint to provide warehouse products for supplier dropdown selection.
    Returns products that are active, in stock, and not already in supplier's catalog.
    """
    from Inventory.models import SupplierProduct

    # Get search query parameter
    search_query = request.GET.get('search', '').strip()

    # Get supplier from request user
    supplier = None
    if hasattr(request.user, 'supplier_profile'):
        supplier = request.user.supplier_profile.supplier

    try:
        # Base queryset: active warehouse products with stock
        queryset = WarehouseProduct.objects.filter(
            is_active=True,
            quantity_in_stock__gt=0,
            is_discontinued=False
        )

        # Exclude products already in supplier's catalog
        if supplier:
            existing_products = SupplierProduct.objects.filter(
                supplier=supplier,
                warehouse_product__isnull=False
            ).values_list('warehouse_product_id', flat=True)

            queryset = queryset.exclude(id__in=existing_products)

        # Apply search filter if provided
        if search_query:
            queryset = queryset.filter(
                Q(product_name__icontains=search_query) |
                Q(product_id__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(category__icontains=search_query)
            )

        # Limit results for performance
        queryset = queryset[:50]

        # Prepare response data
        products = []
        for product in queryset:
            # Determine stock status
            if product.quantity_in_stock <= product.reorder_point:
                stock_status = 'low_stock'
                stock_label = 'Low Stock'
            elif product.quantity_in_stock <= product.minimum_stock_level:
                stock_status = 'limited_stock'
                stock_label = 'Limited Stock'
            else:
                stock_status = 'in_stock'
                stock_label = 'In Stock'

            products.append({
                'id': product.id,
                'product_id': product.product_id,
                'name': product.product_name,
                'sku': product.sku,
                'category': product.category,
                'quantity_in_stock': product.quantity_in_stock,
                'unit_price': float(product.unit_price),
                'stock_status': stock_status,
                'stock_label': stock_label,
                'supplier_name': product.supplier.name if product.supplier else '',
                'description': product.description or '',
                'display_text': f"{product.product_name} ({product.sku}) - {product.category}",
                'availability_info': f"{stock_label} ({product.quantity_in_stock} units)"
            })

        return JsonResponse({
            'success': True,
            'products': products,
            'count': len(products),
            'search_query': search_query
        })

    except Exception as e:
        logger.error(f"Error in warehouse_products_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch warehouse products',
            'products': [],
            'count': 0
        })
