# users/supplier_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from transactions.models import (
    SupplierAccount, SupplierTransaction, SupplierPayment, 
    SupplierCredit, SupplierInvoice
)
from Inventory.models import PurchaseOrder, Supplier
from .forms import EditProfileForm, ChangePasswordForm
from django.contrib.auth import update_session_auth_hash


def supplier_required(view_func):
    """Decorator to ensure only supplier users can access supplier views"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        if request.user.role != 'supplier':
            messages.error(request, "Access denied. Supplier privileges required.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@supplier_required
def supplier_dashboard(request):
    """Supplier dashboard with overview of account status and recent activity"""
    try:
        # Get supplier account
        supplier = Supplier.objects.get(email=request.user.email)
        supplier_account = SupplierAccount.objects.get(supplier=supplier)
        
        # Get recent transactions
        recent_transactions = SupplierTransaction.objects.filter(
            supplier_account=supplier_account
        ).order_by('-transaction_date')[:10]
        
        # Get pending purchase orders
        pending_orders = PurchaseOrder.objects.filter(
            supplier=supplier,
            status__in=['pending', 'approved']
        ).count()
        
        # Get payment statistics
        total_payments = SupplierPayment.objects.filter(
            supplier_transaction__supplier_account=supplier_account,
            status='completed'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Get pending invoices
        pending_invoices = SupplierInvoice.objects.filter(
            supplier_transaction__supplier_account=supplier_account,
            status__in=['received', 'verified']
        ).count()
        
        context = {
            'supplier': supplier,
            'supplier_account': supplier_account,
            'recent_transactions': recent_transactions,
            'pending_orders': pending_orders,
            'total_payments': total_payments,
            'pending_invoices': pending_invoices,
        }
        
    except (Supplier.DoesNotExist, SupplierAccount.DoesNotExist):
        messages.warning(request, "Supplier account not found. Please contact administrator.")
        context = {
            'supplier': None,
            'supplier_account': None,
            'recent_transactions': [],
            'pending_orders': 0,
            'total_payments': 0,
            'pending_invoices': 0,
        }
    
    return render(request, 'supplier/dashboard.html', context)


@supplier_required
def supplier_account(request):
    """Supplier account overview and details"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
        supplier_account = SupplierAccount.objects.get(supplier=supplier)
        
        context = {
            'supplier': supplier,
            'supplier_account': supplier_account,
        }
        
    except (Supplier.DoesNotExist, SupplierAccount.DoesNotExist):
        messages.warning(request, "Supplier account not found. Please contact administrator.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/account.html', context)


@supplier_required
def supplier_purchase_orders(request):
    """List of purchase orders for the supplier"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
        purchase_orders = PurchaseOrder.objects.filter(supplier=supplier).order_by('-created_date')
        
        context = {
            'supplier': supplier,
            'purchase_orders': purchase_orders,
        }
        
    except Supplier.DoesNotExist:
        messages.warning(request, "Supplier account not found. Please contact administrator.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/purchase_orders.html', context)


@supplier_required
def supplier_invoices(request):
    """List of invoices for the supplier"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
        supplier_account = SupplierAccount.objects.get(supplier=supplier)
        
        invoices = SupplierInvoice.objects.filter(
            supplier_transaction__supplier_account=supplier_account
        ).order_by('-received_date')
        
        context = {
            'supplier': supplier,
            'invoices': invoices,
        }
        
    except (Supplier.DoesNotExist, SupplierAccount.DoesNotExist):
        messages.warning(request, "Supplier account not found. Please contact administrator.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/invoices.html', context)


@supplier_required
def supplier_payments(request):
    """List of payments for the supplier"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
        supplier_account = SupplierAccount.objects.get(supplier=supplier)
        
        payments = SupplierPayment.objects.filter(
            supplier_transaction__supplier_account=supplier_account
        ).order_by('-payment_date')
        
        context = {
            'supplier': supplier,
            'payments': payments,
        }
        
    except (Supplier.DoesNotExist, SupplierAccount.DoesNotExist):
        messages.warning(request, "Supplier account not found. Please contact administrator.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/payments.html', context)


@supplier_required
def supplier_transactions(request):
    """Transaction history for the supplier"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
        supplier_account = SupplierAccount.objects.get(supplier=supplier)
        
        transactions = SupplierTransaction.objects.filter(
            supplier_account=supplier_account
        ).order_by('-transaction_date')
        
        context = {
            'supplier': supplier,
            'transactions': transactions,
        }
        
    except (Supplier.DoesNotExist, SupplierAccount.DoesNotExist):
        messages.warning(request, "Supplier account not found. Please contact administrator.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/transactions.html', context)


@supplier_required
def supplier_products(request):
    """Product catalog for the supplier"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
        products = supplier.warehouse_products.filter(is_active=True)
        
        context = {
            'supplier': supplier,
            'products': products,
        }
        
    except Supplier.DoesNotExist:
        messages.warning(request, "Supplier account not found. Please contact administrator.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/products.html', context)


@supplier_required
def supplier_reports(request):
    """Reports and analytics for the supplier"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
        supplier_account = SupplierAccount.objects.get(supplier=supplier)
        
        # Generate basic reports data
        monthly_transactions = SupplierTransaction.objects.filter(
            supplier_account=supplier_account
        ).extra(
            select={'month': "strftime('%%Y-%%m', transaction_date)"}
        ).values('month').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-month')[:12]
        
        context = {
            'supplier': supplier,
            'monthly_transactions': monthly_transactions,
        }
        
    except (Supplier.DoesNotExist, SupplierAccount.DoesNotExist):
        messages.warning(request, "Supplier account not found. Please contact administrator.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/reports.html', context)


@supplier_required
def supplier_settings(request):
    """Supplier settings page for profile and password management"""
    if request.method == 'POST':
        if 'change_password' in request.POST:
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not all([old_password, new_password, confirm_password]):
                messages.error(request, 'All password fields are required.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            elif not request.user.check_password(old_password):
                messages.error(request, 'Incorrect current password.')
            else:
                request.user.set_password(new_password)
                request.user.is_first_login = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
                return redirect('supplier_settings')

        elif 'edit_profile' in request.POST:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')

            if not all([first_name, last_name, email]):
                messages.error(request, 'First name, last name, and email are required.')
            else:
                # Check if email is already taken by another user
                from django.contrib.auth import get_user_model
                User = get_user_model()
                if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                    messages.error(request, 'A user with this email address already exists.')
                else:
                    request.user.first_name = first_name
                    request.user.last_name = last_name
                    request.user.email = email
                    request.user.phone_number = phone_number or ''
                    request.user.save()
                    messages.success(request, 'Profile updated successfully.')
                    return redirect('supplier_settings')

    return render(request, 'supplier/settings.html')
