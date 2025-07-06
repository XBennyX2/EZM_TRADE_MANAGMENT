from django.shortcuts import render, redirect
from store.models import StoreCashier
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import CustomLoginForm, EditProfileForm, ChangePasswordForm
from .models import CustomUser
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
                if user.role == 'admin':
                    return redirect('admin_change_password')
                elif user.role == 'head_manager':
                    return redirect('head_manager_settings')
                elif user.role == 'store_manager':
                    return redirect('store_manager_settings')
                elif user.role == 'cashier':
                    return redirect('cashier_settings')
            else:
                if user.role == 'admin':
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
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()

    users = User.objects.order_by('-date_joined')[:10]

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'users': users,
    }
    return render(request, 'mainpages/admin_dashboard.html', context)

@login_required
def head_manager_page(request):
    if request.user.role != 'head_manager':
        messages.warning(request, "Access denied. You don't have permission to access this page.")
        return redirect('login')

    stores = Store.objects.all().select_related('store_manager')

    return render(request, 'mainpages/head_manager_page.html', {
        'stores': stores
    })

@login_required
def store_manager_page(request):
    store = None
    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.warning(request, "You are not assigned to manage any store.")
        # return redirect('admin_dashboard')

    cashier_assignment = None
    if store:
        cashier_assignment = StoreCashier.objects.filter(store=store, is_active=True).first()

    return render(request, 'mainpages/store_manager_page.html', {
        'store': store,
        'cashier_assignment': cashier_assignment
    })

@login_required
def store_manager_stock_view(request):
    """View for store manager to see their own store stock and other stores' stock"""
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store managers only.")
        return redirect('login')

    try:
        manager_store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.warning(request, "You are not assigned to manage any store.")
        return redirect('login')

    # Get own store stock
    own_stock = Stock.objects.filter(store=manager_store).select_related('product', 'store')

    # Get other stores' stock
    other_stores_stock = Stock.objects.exclude(store=manager_store).select_related('product', 'store')

    context = {
        'manager_store': manager_store,
        'own_stock': own_stock,
        'other_stores_stock': other_stores_stock,
    }
    return render(request, 'store_manager/stock_view.html', context)

@login_required
def store_manager_sales_view(request):
    """View for store manager to see sales of their own store"""
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store managers only.")
        return redirect('login')

    try:
        manager_store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.warning(request, "You are not assigned to manage any store.")
        return redirect('login')

    # Get sales transactions for the store
    sales_transactions = Transaction.objects.filter(
        store=manager_store,
        transaction_type='sale'
    ).order_by('-timestamp')

    # Get financial records for the store
    financial_records = FinancialRecord.objects.filter(
        store=manager_store
    ).order_by('-timestamp')

    # Calculate totals
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    today_sales = financial_records.filter(
        timestamp__date=today,
        record_type='revenue'
    ).aggregate(total=Sum('amount'))['total'] or 0

    week_sales = financial_records.filter(
        timestamp__date__gte=week_ago,
        record_type='revenue'
    ).aggregate(total=Sum('amount'))['total'] or 0

    month_sales = financial_records.filter(
        timestamp__date__gte=month_ago,
        record_type='revenue'
    ).aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'manager_store': manager_store,
        'sales_transactions': sales_transactions[:20],  # Latest 20 transactions
        'financial_records': financial_records[:20],  # Latest 20 records
        'today_sales': today_sales,
        'week_sales': week_sales,
        'month_sales': month_sales,
    }
    return render(request, 'store_manager/sales_view.html', context)

@login_required
def store_manager_cashier_management(request):
    """View for store manager to manage cashiers"""
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store managers only.")
        return redirect('login')

    try:
        manager_store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.warning(request, "You are not assigned to manage any store.")
        return redirect('login')

    # Get all cashiers assigned to this store
    store_cashiers = StoreCashier.objects.filter(store=manager_store).select_related('cashier')

    # Get search query
    search_query = request.GET.get('search', '')

    # Get all available cashiers (not active in any store)
    # Include cashiers that are inactive in other stores
    active_cashier_ids = StoreCashier.objects.filter(is_active=True).values_list('cashier_id', flat=True)
    available_cashiers = CustomUser.objects.filter(
        role='cashier',
        is_active=True
    ).exclude(id__in=active_cashier_ids).order_by('username')

    # Apply search filter
    if search_query:
        available_cashiers = available_cashiers.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # Pagination for available cashiers
    from django.core.paginator import Paginator
    paginator = Paginator(available_cashiers, 5)  # Show 5 cashiers per page
    page_number = request.GET.get('page')
    available_cashiers_page = paginator.get_page(page_number)

    context = {
        'manager_store': manager_store,
        'store_cashiers': store_cashiers,
        'available_cashiers': available_cashiers_page,
        'search_query': search_query,
    }
    return render(request, 'store_manager/cashier_management.html', context)

@login_required
def assign_cashier_to_store(request, cashier_id):
    """Assign a cashier to the store manager's store"""
    if request.user.role != 'store_manager':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied. Store managers only.'})
        messages.error(request, "Access denied. Store managers only.")
        return redirect('login')

    try:
        manager_store = Store.objects.get(store_manager=request.user)
        cashier = CustomUser.objects.get(id=cashier_id, role='cashier')

        # Check if store already has an active cashier
        existing_active_cashier = StoreCashier.objects.filter(store=manager_store, is_active=True).first()
        if existing_active_cashier:
            message = f"Store {manager_store.name} already has an active cashier: {existing_active_cashier.cashier.username}. Please deactivate them first."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': message, 'type': 'warning'})
            messages.warning(request, message)
            return redirect('store_manager_cashier_management')

        # Check if cashier is already active in another store
        existing_assignment = StoreCashier.objects.filter(cashier=cashier, is_active=True).first()
        if existing_assignment:
            message = f"{cashier.username} is already active at {existing_assignment.store.name}"
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': message, 'type': 'warning'})
            messages.warning(request, message)
            return redirect('store_manager_cashier_management')

        # Check if cashier is already assigned to this store (but inactive)
        existing_store_assignment = StoreCashier.objects.filter(store=manager_store, cashier=cashier).first()
        if existing_store_assignment:
            # Reactivate existing assignment
            existing_store_assignment.is_active = True
            existing_store_assignment.save()
            message = f"Reactivated {cashier.username} for {manager_store.name}"
        else:
            # Create new assignment
            StoreCashier.objects.create(
                store=manager_store,
                cashier=cashier,
                is_active=True
            )
            message = f"Successfully assigned {cashier.username} to {manager_store.name}"

        # Update cashier's store field
        cashier.store = manager_store
        cashier.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': message, 'type': 'success'})
        messages.success(request, message)

    except Store.DoesNotExist:
        message = "You are not assigned to manage any store."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message, 'type': 'error'})
        messages.error(request, message)
    except CustomUser.DoesNotExist:
        message = "Cashier not found."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message, 'type': 'error'})
        messages.error(request, message)

    return redirect('store_manager_cashier_management')

@login_required
def toggle_cashier_status(request, cashier_assignment_id):
    """Activate or deactivate a cashier assignment"""
    if request.user.role != 'store_manager':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Access denied. Store managers only.'})
        messages.error(request, "Access denied. Store managers only.")
        return redirect('login')

    try:
        manager_store = Store.objects.get(store_manager=request.user)
        cashier_assignment = StoreCashier.objects.get(
            id=cashier_assignment_id,
            store=manager_store
        )

        # If trying to activate, check if store already has an active cashier
        if not cashier_assignment.is_active:
            existing_active_cashier = StoreCashier.objects.filter(
                store=manager_store,
                is_active=True
            ).exclude(id=cashier_assignment_id).first()

            if existing_active_cashier:
                message = f"Store {manager_store.name} already has an active cashier: {existing_active_cashier.cashier.username}. Please deactivate them first."
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': message, 'type': 'warning'})
                messages.warning(request, message)
                return redirect('store_manager_cashier_management')

            # Check if cashier is already active in another store
            cashier_active_elsewhere = StoreCashier.objects.filter(
                cashier=cashier_assignment.cashier,
                is_active=True
            ).exclude(store=manager_store).first()

            if cashier_active_elsewhere:
                message = f"{cashier_assignment.cashier.username} is already active at {cashier_active_elsewhere.store.name}"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': message, 'type': 'warning'})
                messages.warning(request, message)
                return redirect('store_manager_cashier_management')

        # Toggle the status
        cashier_assignment.is_active = not cashier_assignment.is_active
        cashier_assignment.save()

        # Update cashier's store field based on status
        if not cashier_assignment.is_active:
            cashier_assignment.cashier.store = None
        else:
            cashier_assignment.cashier.store = manager_store
        cashier_assignment.cashier.save()

        status = "activated" if cashier_assignment.is_active else "deactivated"
        message = f"Successfully {status} {cashier_assignment.cashier.username}"

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'type': 'success',
                'new_status': cashier_assignment.is_active,
                'cashier_id': cashier_assignment.id
            })
        messages.success(request, message)

    except Store.DoesNotExist:
        message = "You are not assigned to manage any store."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message, 'type': 'error'})
        messages.error(request, message)
    except StoreCashier.DoesNotExist:
        message = "Cashier assignment not found."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message, 'type': 'error'})
        messages.error(request, message)

    return redirect('store_manager_cashier_management')
from store.models import Order, Store, StoreCashier, FinancialRecord
from transactions.models import Transaction
from Inventory.models import Stock
from django.db.models import Sum, Count
from datetime import datetime, timedelta
from django.http import JsonResponse

@login_required
def cashier_page(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')[:10]
    transactions = [order.transaction for order in orders if order.transaction]
    return render(request, 'mainpages/cashier_page.html', {'transactions': transactions})

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from .forms import ChangeUserRoleForm, CustomUserCreationFormAdmin
from django.core.paginator import Paginator

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@user_passes_test(is_admin)
def manage_users(request):
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    page_number = request.GET.get('page')

    users = User.objects.all()

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    if role_filter:
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
        'total_users': users.count(),
        'is_admin': role_filter == 'admin',
        'is_head_manager': role_filter == 'head_manager',
        'is_store_manager': role_filter == 'store_manager',
        'is_cashier': role_filter == 'cashier',
    }
    logger.debug(f"page_obj: {page_obj}")
    logger.debug(f"page_obj.paginator.page_range: {page_obj.paginator.page_range}")
    return render(request, 'admin/manage_users.html', context)

@user_passes_test(is_admin)
def create_user(request):
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
            'role': role
        }

        if not all([username, first_name, last_name, email, password, role]):
            messages.error(request, "All required fields must be filled.")
            return render(request, 'admin/create_user.html', context)

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose a different username.")
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

            subject = "Account Created"
            message = f"Your account has been created.\\n" \
                      f"Username: {user.username}\\n" \
                      f"Password: {password}\\n" \
                      f"Phone Number: {user.phone_number}"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]
            send_mail(subject, message, from_email, to_email, fail_silently=True)

            messages.success(request, f"User {user.username} created successfully. Email sent with credentials.")
            return redirect('manage_users')
        except Exception as e:
            messages.error(request, f"Error creating user: {e}")
            return render(request, 'admin/create_user.html', context)
    else:
        return render(request, 'admin/create_user.html')

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

@login_required
def admin_settings(request):
    if request.user.role == 'admin':
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
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data['old_password']
            new_password1 = form.cleaned_data['new_password1']
            if request.user.check_password(old_password):
                request.user.set_password(new_password1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')
                return redirect('admin_settings')
            else:
                messages.error(request, 'Incorrect old password.')
    else:
        form = ChangePasswordForm()
    return render(request, 'users/change_password.html', {'form': form})

@login_required
def head_manager_settings(request):
    # Mark user as no longer first login after visiting settings
    if request.user.is_first_login:
        request.user.is_first_login = False
        request.user.save()
        messages.info(request, "Welcome! Please update your password and profile information.")

    return render(request, 'mainpages/head_manager_settings.html')

@login_required
def store_manager_settings(request):
    return render(request, 'mainpages/store_manager_settings.html')

@login_required
def cashier_settings(request):
    # Mark user as no longer first login after visiting settings
    if request.user.is_first_login:
        request.user.is_first_login = False
        request.user.save()
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
                request.user.set_password(new_password1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully!')
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
        else:
            # Default fallback
            return reverse_lazy('login')
