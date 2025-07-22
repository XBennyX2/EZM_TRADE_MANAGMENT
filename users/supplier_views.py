# users/supplier_views.py
from django.shortcuts import render, redirect, get_object_or_404
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
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)
from django.utils import timezone
from Inventory.models import SupplierProfile, SupplierProduct, WarehouseProduct, ProductCategory
from Inventory.forms import SupplierProfileForm, SupplierProductForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt


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


def supplier_profile_required(view_func):
    """Decorator to ensure supplier has completed their profile before accessing features"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('login')
        if request.user.role != 'supplier':
            messages.error(request, "Access denied. Supplier privileges required.")
            return redirect('login')

        # Check if supplier profile is complete
        try:
            supplier = Supplier.objects.get(email=request.user.email)
            try:
                supplier_profile = SupplierProfile.objects.get(supplier=supplier)
                if not supplier_profile.is_onboarding_complete:
                    messages.warning(request, "Please complete your supplier profile to access this feature.")
                    return redirect('supplier_onboarding')
            except SupplierProfile.DoesNotExist:
                messages.warning(request, "Please complete your supplier profile to access this feature.")
                return redirect('supplier_onboarding')
        except Supplier.DoesNotExist:
            messages.warning(request, "Please complete your supplier profile to access this feature.")
            return redirect('supplier_onboarding')

        return view_func(request, *args, **kwargs)
    return wrapper


@supplier_required
def supplier_dashboard(request):
    """Supplier dashboard with overview of account status and recent activity"""
    try:
        # Get supplier account
        supplier = Supplier.objects.get(email=request.user.email)
    except Supplier.DoesNotExist:
        # Create a basic supplier record for the user if it doesn't exist
        supplier = Supplier.objects.create(
            name=request.user.get_full_name() or request.user.username,
            email=request.user.email,
            contact_person=request.user.get_full_name() or request.user.username,
            phone=getattr(request.user, 'phone_number', '') or '',
            is_active=True
        )
        messages.info(request, "Welcome! Please complete your supplier profile to access all features.")
        return redirect('supplier_onboarding')

    # Check onboarding status
    try:
        supplier_profile = SupplierProfile.objects.get(supplier=supplier)
        onboarding_complete = supplier_profile.is_onboarding_complete
    except SupplierProfile.DoesNotExist:
        supplier_profile = None
        onboarding_complete = False

    # If onboarding is not complete, redirect to onboarding
    if not onboarding_complete:
        messages.info(request, "Please complete your supplier profile to access all features.")
        return redirect('supplier_onboarding')

    # Get supplier account (create if doesn't exist)
    try:
        supplier_account = SupplierAccount.objects.get(supplier=supplier)
    except SupplierAccount.DoesNotExist:
        # Create a basic supplier account if it doesn't exist
        supplier_account = SupplierAccount.objects.create(
            supplier=supplier,
            payment_terms='net_30',
            credit_limit=0.00,
            is_active=True
        )

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

    # Get supplier product statistics
    total_products = SupplierProduct.objects.filter(supplier=supplier).count()
    active_products = SupplierProduct.objects.filter(supplier=supplier, is_active=True).count()

    context = {
        'supplier': supplier,
        'supplier_profile': supplier_profile,
        'supplier_account': supplier_account,
        'recent_transactions': recent_transactions,
        'pending_orders': pending_orders,
        'total_payments': total_payments,
        'pending_invoices': pending_invoices,
        'total_products': total_products,
        'active_products': active_products,
        'onboarding_complete': onboarding_complete,
    }

    return render(request, 'supplier/dashboard.html', context)


@supplier_profile_required
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
        messages.warning(request, "Supplier account not found. Please contact the administrator to set up your supplier profile.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/account.html', context)


@supplier_profile_required
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
        messages.warning(request, "Supplier profile not found. Please contact the administrator to set up your supplier profile.")
        return redirect('supplier_dashboard')

    return render(request, 'supplier/purchase_orders.html', context)


@login_required
@require_http_methods(["POST"])
def supplier_mark_in_transit(request, order_id):
    """
    Allow supplier to mark order as in transit
    """
    try:
        # Get supplier
        supplier = Supplier.objects.get(email=request.user.email)

        # Get the purchase order
        order = get_object_or_404(PurchaseOrder, id=order_id, supplier=supplier)

        # Check if order can be marked as in transit
        if order.status != 'payment_confirmed':
            return JsonResponse({
                'success': False,
                'message': 'Order must be payment confirmed to mark as in transit'
            })

        # Get tracking number from request
        tracking_number = request.POST.get('tracking_number', '').strip()

        # Mark order as in transit
        from django.db import transaction
        from Inventory.models import OrderStatusHistory

        with transaction.atomic():
            previous_status = order.status
            order.mark_in_transit(tracking_number)

            # Create status history record
            OrderStatusHistory.objects.create(
                purchase_order=order,
                previous_status=previous_status,
                new_status=order.status,
                changed_by=request.user,
                reason=f'Marked as in transit by supplier{" with tracking: " + tracking_number if tracking_number else ""}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            # Send notification to head manager
            try:
                from payments.notification_service import supplier_notification_service
                supplier_notification_service.send_order_status_change_notification(
                    order, previous_status, order.status, request.user
                )
            except Exception as e:
                logger.error(f"Failed to send status change notification: {str(e)}")

        return JsonResponse({
            'success': True,
            'message': 'Order marked as in transit successfully',
            'new_status': order.status,
            'tracking_number': tracking_number
        })

    except Supplier.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Supplier profile not found'
        }, status=403)
    except Exception as e:
        logger.error(f"Error marking order {order_id} as in transit: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Unable to update order status'
        }, status=500)


@supplier_profile_required
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
        messages.warning(request, "Supplier account not found. Please contact the administrator to set up your supplier profile.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/invoices.html', context)


@supplier_profile_required
def supplier_payments(request):
    """Enhanced payment notifications and history for the supplier"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)

        # Get Chapa payment transactions for this supplier
        from payments.models import ChapaTransaction, PurchaseOrderPayment

        # Get all Chapa transactions for this supplier
        chapa_transactions = ChapaTransaction.objects.filter(
            supplier=supplier
        ).order_by('-created_at')

        # Get purchase order payments
        purchase_order_payments = PurchaseOrderPayment.objects.filter(
            supplier=supplier
        ).order_by('-created_at')

        # Get delivery confirmations and issue reports
        from Inventory.models import DeliveryConfirmation, IssueReport
        delivery_confirmations = DeliveryConfirmation.objects.filter(
            purchase_order__supplier=supplier
        ).order_by('-confirmed_at')[:10]

        issue_reports = IssueReport.objects.filter(
            purchase_order__supplier=supplier
        ).order_by('-reported_at')[:10]

        # Get traditional supplier payments (for backward compatibility)
        try:
            supplier_account = SupplierAccount.objects.get(supplier=supplier)
            traditional_payments = SupplierPayment.objects.filter(
                supplier_transaction__supplier_account=supplier_account
            ).order_by('-payment_date')
        except SupplierAccount.DoesNotExist:
            traditional_payments = []

        # Payment statistics
        total_chapa_payments = chapa_transactions.filter(status='success').aggregate(
            total=Sum('amount')
        )['total'] or 0

        pending_payments = chapa_transactions.filter(status='pending').count()
        failed_payments = chapa_transactions.filter(status='failed').count()
        successful_payments = chapa_transactions.filter(status='success').count()

        context = {
            'supplier': supplier,
            'chapa_transactions': chapa_transactions,
            'purchase_order_payments': purchase_order_payments,
            'traditional_payments': traditional_payments,
            'delivery_confirmations': delivery_confirmations,
            'issue_reports': issue_reports,
            'total_chapa_payments': total_chapa_payments,
            'pending_payments': pending_payments,
            'failed_payments': failed_payments,
            'successful_payments': successful_payments,
            'total_transactions': chapa_transactions.count(),
        }

    except Supplier.DoesNotExist:
        messages.warning(request, "Supplier profile not found. Please contact the administrator to set up your supplier profile.")
        return redirect('supplier_dashboard')

    return render(request, 'supplier/payments.html', context)


@supplier_profile_required
def supplier_payment_notifications_api(request):
    """
    API endpoint for real-time payment notification updates
    """
    try:
        supplier = Supplier.objects.get(email=request.user.email)

        # Get Chapa payment transactions for this supplier
        from payments.models import ChapaTransaction

        chapa_transactions = ChapaTransaction.objects.filter(
            supplier=supplier
        ).order_by('-created_at')

        # Payment statistics
        total_chapa_payments = chapa_transactions.filter(status='success').aggregate(
            total=Sum('amount')
        )['total'] or 0

        pending_payments = chapa_transactions.filter(status='pending').count()
        failed_payments = chapa_transactions.filter(status='failed').count()
        successful_payments = chapa_transactions.filter(status='success').count()

        # Recent transactions for real-time updates
        recent_transactions = []
        for transaction in chapa_transactions[:10]:
            recent_transactions.append({
                'chapa_tx_ref': transaction.chapa_tx_ref,
                'amount': float(transaction.amount),
                'status': transaction.status,
                'customer_first_name': transaction.customer_first_name,
                'customer_last_name': transaction.customer_last_name,
                'customer_email': transaction.customer_email,
                'created_at': transaction.created_at.isoformat(),
                'description': transaction.description,
            })

        data = {
            'successful_payments': successful_payments,
            'pending_payments': pending_payments,
            'failed_payments': failed_payments,
            'total_transactions': chapa_transactions.count(),
            'total_amount': float(total_chapa_payments),
            'recent_transactions': recent_transactions,
        }

        return JsonResponse(data)

    except Supplier.DoesNotExist:
        return JsonResponse({'error': 'Supplier not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@supplier_profile_required
def supplier_transactions(request):
    """Comprehensive transaction history for the supplier including all payment types"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)

        # Get Chapa payment transactions for this supplier
        from payments.models import ChapaTransaction, PurchaseOrderPayment
        from django.db.models import Q
        from itertools import chain
        from operator import attrgetter

        # Get all Chapa transactions for this supplier
        chapa_transactions = ChapaTransaction.objects.filter(
            supplier=supplier
        ).order_by('-created_at')

        # Get purchase order payments
        purchase_order_payments = PurchaseOrderPayment.objects.filter(
            supplier=supplier
        ).order_by('-created_at')

        # Get traditional supplier transactions (if supplier account exists)
        traditional_transactions = []
        try:
            supplier_account = SupplierAccount.objects.get(supplier=supplier)
            traditional_transactions = SupplierTransaction.objects.filter(
                supplier_account=supplier_account
            ).order_by('-transaction_date')
        except SupplierAccount.DoesNotExist:
            pass

        # Get supplier payments
        supplier_payments = []
        if traditional_transactions:
            supplier_payments = SupplierPayment.objects.filter(
                supplier_transaction__supplier_account__supplier=supplier
            ).order_by('-payment_date')

        # Create a unified transaction list with normalized data
        unified_transactions = []

        # Add Chapa transactions
        for transaction in chapa_transactions:
            unified_transactions.append({
                'type': 'chapa_payment',
                'date': transaction.created_at,
                'description': transaction.description,
                'amount': transaction.amount,
                'status': transaction.status,
                'reference': transaction.chapa_tx_ref,
                'payment_method': 'Chapa Payment Gateway',
                'transaction_id': str(transaction.id),
                'raw_object': transaction
            })

        # Add purchase order payments
        for payment in purchase_order_payments:
            unified_transactions.append({
                'type': 'purchase_order_payment',
                'date': payment.created_at,
                'description': f"Purchase Order Payment - {len(payment.order_items)} items",
                'amount': payment.total_amount,
                'status': payment.status,
                'reference': payment.chapa_transaction.chapa_tx_ref if payment.chapa_transaction else 'N/A',
                'payment_method': 'Purchase Order via Chapa',
                'transaction_id': str(payment.id),
                'raw_object': payment
            })

        # Add traditional supplier transactions
        for transaction in traditional_transactions:
            unified_transactions.append({
                'type': 'supplier_transaction',
                'date': transaction.transaction_date,
                'description': transaction.description,
                'amount': transaction.amount,
                'status': transaction.status,
                'reference': transaction.reference_number or transaction.transaction_number,
                'payment_method': transaction.get_transaction_type_display(),
                'transaction_id': str(transaction.id),
                'raw_object': transaction
            })

        # Add supplier payments
        for payment in supplier_payments:
            unified_transactions.append({
                'type': 'supplier_payment',
                'date': payment.payment_date,
                'description': f"Payment - {payment.get_payment_method_display()}",
                'amount': payment.amount_paid,
                'status': payment.status,
                'reference': payment.bank_reference or payment.check_number or payment.payment_number,
                'payment_method': payment.get_payment_method_display(),
                'transaction_id': str(payment.id),
                'raw_object': payment
            })

        # Sort all transactions by date (newest first)
        unified_transactions.sort(key=lambda x: x['date'], reverse=True)

        # Calculate summary statistics
        total_amount = sum(t['amount'] for t in unified_transactions if t['status'] in ['success', 'completed', 'payment_confirmed'])
        successful_transactions = len([t for t in unified_transactions if t['status'] in ['success', 'completed', 'payment_confirmed']])
        pending_transactions = len([t for t in unified_transactions if t['status'] in ['pending', 'payment_pending']])
        failed_transactions = len([t for t in unified_transactions if t['status'] in ['failed', 'cancelled']])

        context = {
            'supplier': supplier,
            'transactions': unified_transactions,
            'chapa_transactions': chapa_transactions,
            'purchase_order_payments': purchase_order_payments,
            'traditional_transactions': traditional_transactions,
            'supplier_payments': supplier_payments,
            'total_amount': total_amount,
            'successful_transactions': successful_transactions,
            'pending_transactions': pending_transactions,
            'failed_transactions': failed_transactions,
            'total_transactions': len(unified_transactions),
        }

    except Supplier.DoesNotExist:
        messages.warning(request, "Supplier account not found. Please contact the administrator to set up your supplier profile.")
        return redirect('supplier_dashboard')
    except Exception as e:
        messages.error(request, f"Error loading transaction history: {str(e)}")
        return redirect('supplier_dashboard')

    return render(request, 'supplier/transactions.html', context)


@supplier_profile_required
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
        messages.warning(request, "Supplier profile not found. Please contact the administrator to set up your supplier profile.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/products.html', context)


@supplier_profile_required
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
        messages.warning(request, "Supplier account not found. Please contact the administrator to set up your supplier profile.")
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


@supplier_required
def supplier_onboarding(request):
    """Supplier onboarding process for completing profile setup"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
    except Supplier.DoesNotExist:
        # Create a basic supplier record if it doesn't exist
        supplier = Supplier.objects.create(
            name=request.user.get_full_name() or request.user.username,
            email=request.user.email,
            contact_person=request.user.get_full_name() or request.user.username,
            phone=getattr(request.user, 'phone_number', '') or '',
            is_active=True
        )

    # Get or create supplier profile
    try:
        supplier_profile = SupplierProfile.objects.get(supplier=supplier)
    except SupplierProfile.DoesNotExist:
        supplier_profile = None

    if request.method == 'POST':
        form = SupplierProfileForm(request.POST, instance=supplier_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.supplier = supplier
            profile.is_onboarding_complete = True
            profile.onboarding_completed_date = timezone.now()
            profile.save()

            # Update the basic supplier record with profile information
            supplier.name = profile.business_name
            supplier.contact_person = profile.primary_contact_name
            supplier.phone = profile.primary_contact_phone
            supplier.address = f"{profile.business_address_line1}, {profile.city}, {profile.state_province} {profile.postal_code}, {profile.country}"
            supplier.save()

            messages.success(request, "Your supplier profile has been completed successfully! You now have access to all supplier features.")
            return redirect('supplier_dashboard')
    else:
        form = SupplierProfileForm(instance=supplier_profile)
        # Pre-populate form with user information if creating new profile
        if not supplier_profile:
            form.initial.update({
                'business_name': supplier.name,
                'primary_contact_name': request.user.get_full_name() or request.user.username,
                'primary_contact_email': request.user.email,
                'primary_contact_phone': getattr(request.user, 'phone_number', '') or supplier.phone,
            })

    context = {
        'form': form,
        'supplier': supplier,
        'supplier_profile': supplier_profile,
        'is_update': supplier_profile is not None,
        'user': request.user,
    }

    return render(request, 'supplier/onboarding.html', context)


@supplier_profile_required
def supplier_product_catalog(request):
    """Supplier product catalog management"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
    except Supplier.DoesNotExist:
        messages.error(request, "Supplier profile not found.")
        return redirect('supplier_dashboard')

    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')

    # Get supplier products
    products = SupplierProduct.objects.filter(supplier=supplier)

    # Apply filters
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(product_code__icontains=search_query)
        )

    if category_filter:
        products = products.filter(category__icontains=category_filter)

    if status_filter:
        if status_filter == 'active':
            products = products.filter(is_active=True)
        elif status_filter == 'inactive':
            products = products.filter(is_active=False)
        else:
            products = products.filter(availability_status=status_filter)

    # Pagination
    paginator = Paginator(products.order_by('-created_date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for filter dropdown
    categories = SupplierProduct.objects.filter(supplier=supplier).values_list('category', flat=True).distinct()

    context = {
        'supplier': supplier,
        'products': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories': categories,
        'total_products': products.count(),
    }

    return render(request, 'supplier/product_catalog.html', context)


@supplier_profile_required
def supplier_add_product(request):
    """Add new product to supplier catalog"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
    except Supplier.DoesNotExist:
        messages.error(request, "Supplier profile not found.")
        return redirect('supplier_dashboard')

    if request.method == 'POST':
        form = SupplierProductForm(request.POST, request.FILES, supplier=supplier)
        if form.is_valid():
            product = form.save(commit=False)
            product.supplier = supplier
            product.save()
            messages.success(request, f"Product '{product.product_name}' added successfully!")
            return redirect('supplier_product_catalog')
    else:
        form = SupplierProductForm(supplier=supplier)

    context = {
        'form': form,
        'supplier': supplier,
        'action': 'Add',
    }

    return render(request, 'supplier/product_form.html', context)


@supplier_profile_required
def supplier_edit_product(request, product_id):
    """Edit existing product in supplier catalog"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
        product = SupplierProduct.objects.get(id=product_id, supplier=supplier)
    except (Supplier.DoesNotExist, SupplierProduct.DoesNotExist):
        messages.error(request, "Product not found.")
        return redirect('supplier_product_catalog')

    if request.method == 'POST':
        form = SupplierProductForm(request.POST, request.FILES, instance=product, supplier=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.product_name}' updated successfully!")
            return redirect('supplier_product_catalog')
    else:
        form = SupplierProductForm(instance=product, supplier=supplier)

    context = {
        'form': form,
        'supplier': supplier,
        'product': product,
        'action': 'Edit',
    }

    return render(request, 'supplier/product_form.html', context)


@supplier_profile_required
def supplier_delete_product(request, product_id):
    """Delete product from supplier catalog"""
    try:
        supplier = Supplier.objects.get(email=request.user.email)
        product = SupplierProduct.objects.get(id=product_id, supplier=supplier)
    except (Supplier.DoesNotExist, SupplierProduct.DoesNotExist):
        messages.error(request, "Product not found.")
        return redirect('supplier_product_catalog')

    if request.method == 'POST':
        product_name = product.product_name
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully!")
        return redirect('supplier_product_catalog')

    context = {
        'supplier': supplier,
        'product': product,
    }

    return render(request, 'supplier/product_delete_confirm.html', context)


@require_http_methods(["GET"])
def check_supplier_setup_status(request):
    """
    API endpoint to check if supplier account is properly set up.
    This can be used by administrators or for debugging.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.user.role != 'supplier':
        return JsonResponse({'error': 'Supplier role required'}, status=403)

    try:
        supplier = Supplier.objects.get(email=request.user.email)
        supplier_exists = True
        supplier_data = {
            'name': supplier.name,
            'email': supplier.email,
            'phone': supplier.phone,
            'is_active': supplier.is_active,
        }
    except Supplier.DoesNotExist:
        supplier_exists = False
        supplier_data = None

    try:
        if supplier_exists:
            supplier_account = SupplierAccount.objects.get(supplier=supplier)
            account_exists = True
            account_data = {
                'account_number': supplier_account.account_number,
                'current_balance': str(supplier_account.current_balance),
                'payment_terms': supplier_account.payment_terms,
                'is_active': supplier_account.is_active,
            }
        else:
            account_exists = False
            account_data = None
    except SupplierAccount.DoesNotExist:
        account_exists = False
        account_data = None

    return JsonResponse({
        'user_email': request.user.email,
        'user_name': request.user.get_full_name() or request.user.username,
        'supplier_exists': supplier_exists,
        'supplier_data': supplier_data,
        'account_exists': account_exists,
        'account_data': account_data,
        'setup_complete': supplier_exists and account_exists,
        'next_steps': get_setup_next_steps(supplier_exists, account_exists)
    })


def get_setup_next_steps(supplier_exists, account_exists):
    """Helper function to determine what setup steps are needed"""
    if not supplier_exists:
        return [
            "Create Supplier profile in admin panel",
            "Link supplier email to user account",
            "Create SupplierAccount for financial tracking"
        ]
    elif not account_exists:
        return [
            "Create SupplierAccount for existing supplier",
            "Set up payment terms and credit limits"
        ]
    else:
        return ["Setup complete - all systems ready"]


# === API Endpoints for Product Selection ===

@login_required
@require_http_methods(["GET"])
def api_warehouse_products(request):
    """
    API endpoint to get warehouse products for dropdown selection.
    Returns products with unique identifiers and availability info.
    """
    try:
        # Get query parameters
        supplier_id = request.GET.get('supplier_id')
        category = request.GET.get('category')
        search = request.GET.get('search', '')

        # Base queryset - only active products with stock
        products = WarehouseProduct.objects.filter(
            is_active=True,
            quantity_in_stock__gt=0
        )

        # Filter by supplier if specified
        if supplier_id:
            products = products.filter(supplier_id=supplier_id)

        # Filter by category if specified
        if category:
            products = products.filter(category=category)

        # Search filter
        if search:
            products = products.filter(
                Q(product_name__icontains=search) |
                Q(product_id__icontains=search) |
                Q(sku__icontains=search)
            )

        # Prepare response data
        product_data = []
        for product in products.order_by('product_name')[:50]:  # Limit to 50 results
            product_data.append({
                'id': product.id,
                'product_id': product.product_id,
                'sku': product.sku,
                'name': product.product_name,
                'category': product.category,
                'display_name': f"{product.product_name} - [{product.product_id}]",
                'unit_price': str(product.unit_price),
                'quantity_in_stock': product.quantity_in_stock,
                'supplier_name': product.supplier.name if product.supplier else '',
                'minimum_order': 1,
                'maximum_order': min(product.quantity_in_stock, 1000)
            })

        return JsonResponse({
            'success': True,
            'products': product_data,
            'total_count': len(product_data)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_product_categories(request):
    """
    API endpoint to get available product categories.
    """
    try:
        # Get categories from warehouse products
        categories = WarehouseProduct.objects.filter(
            is_active=True,
            quantity_in_stock__gt=0
        ).values_list('category', flat=True).distinct().order_by('category')

        category_data = [{'value': cat, 'label': cat} for cat in categories if cat]

        return JsonResponse({
            'success': True,
            'categories': category_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
