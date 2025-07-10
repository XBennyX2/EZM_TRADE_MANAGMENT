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
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from Inventory.models import SupplierProfile, SupplierProduct
from Inventory.forms import SupplierProfileForm, SupplierProductForm
from django.core.paginator import Paginator
from django.db.models import Q


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

    try:
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

    except (Supplier.DoesNotExist, SupplierAccount.DoesNotExist) as e:
        if isinstance(e, Supplier.DoesNotExist):
            messages.warning(request,
                "Supplier profile not found. Please contact the administrator to set up your supplier profile. "
                f"Your registered email ({request.user.email}) needs to be linked to a supplier account."
            )
        else:
            messages.warning(request,
                "Supplier account not found. Please contact the administrator to set up your supplier account. "
                "A supplier profile exists but the financial account needs to be created."
            )

        context = {
            'supplier': None,
            'supplier_account': None,
            'recent_transactions': [],
            'pending_orders': 0,
            'total_payments': 0,
            'pending_invoices': 0,
            'user_email': request.user.email,
            'setup_required': True,
            'user_full_name': request.user.get_full_name() or request.user.username,
            'user_phone': request.user.phone_number,
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
        messages.warning(request, "Supplier account not found. Please contact the administrator to set up your supplier profile.")
        return redirect('supplier_dashboard')
    
    return render(request, 'supplier/payments.html', context)


@supplier_profile_required
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
        messages.warning(request, "Supplier account not found. Please contact the administrator to set up your supplier profile.")
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
        form = SupplierProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.supplier = supplier
            product.save()
            messages.success(request, f"Product '{product.product_name}' added successfully!")
            return redirect('supplier_product_catalog')
    else:
        form = SupplierProductForm()

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
        form = SupplierProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.product_name}' updated successfully!")
            return redirect('supplier_product_catalog')
    else:
        form = SupplierProductForm(instance=product)

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
