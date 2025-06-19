# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import CustomUserCreationForm, CustomLoginForm
from .models import CustomUser

# users/views.py
from .utils import send_otp_email
from django.utils.crypto import get_random_string



from django.core.mail import send_mail
from django.contrib import messages
from django.utils.crypto import get_random_string
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

    text_content = f"Hi {user.username},\nWelcome to EZM Trade!\nYour OTP code is: {user.otp_code}"
    html_content = render_to_string('users/email_otp.html', context)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def register_view(request):
    if request.user.is_authenticated:
        user = request.user
        if user.is_superuser or user.role == 'admin':
            return redirect('admin_dashboard')
        elif user.role == 'customer':
            return redirect('customer_page')
        elif user.role == 'store_owner':
            return redirect('store_owner_page')
        elif user.role == 'store_manager':
            return redirect('store_manager_page')
        elif user.role == 'cashier':
            return redirect('cashier_page')
        else:
            messages.warning(request, "Your account has no assigned role. Contact admin.")
            return redirect('login')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Prevent login until verified

            # Generate and set OTP
            user.otp_code = get_random_string(length=6, allowed_chars='0123456789')
            user.otp_created_at = timezone.now()
            user.save()

            send_otp_email(user)
            request.session['otp_email'] = user.email

            return redirect('verify_otp', user_id=user.id)
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})

def resend_otp(request):
    if request.method in ['GET', 'POST']:
        email = request.session.get('otp_email')
        if not email:
            messages.error(request, "Session expired. Please register again.")
            return redirect('register')

        user = CustomUser.objects.filter(email=email).first()
        if not user:
            messages.error(request, "User not found.")
            return redirect('register')

        # Generate new OTP and reset timer
        user.otp_code = get_random_string(length=6, allowed_chars='0123456789')
        user.otp_created_at = timezone.now()
        user.save()

        send_otp_email(user)
        messages.success(request, "A new OTP has been sent to your email.")
        return redirect('verify_otp', user_id=user.id)

    return redirect('register')


from django.shortcuts import get_object_or_404

from django.utils import timezone
from datetime import timedelta

def verify_otp_view(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)

    if request.method == 'POST':
        otp = request.POST.get('otp')

        # Check expiration
        if user.otp_created_at and timezone.now() > user.otp_created_at + timedelta(minutes=5):
            messages.error(request, "OTP expired. Please request a new one.")
            return redirect('resend_otp')

        if otp == user.otp_code:
            user.is_active = True
            user.is_verified = True  
            user.otp_code = ''
            user.otp_created_at = None
            user.save()
            messages.success(request, "Your account has been verified.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'users/verify_otp.html', {'user': user})


from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import CustomLoginForm

def login_view(request):
    if request.user.is_authenticated:
        user = request.user
        if getattr(user, 'is_verified', False):
            # Verified users go to their dashboard pages
            if user.is_superuser or user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'customer':
                return redirect('customer_page')
            elif user.role == 'store_owner':
                return redirect('store_owner_page')
            elif user.role == 'store_manager':
                return redirect('store_manager_page')
            elif user.role == 'cashier':
                return redirect('cashier_page')
            else:
                messages.warning(request, "No role assigned. Contact admin.")
                return redirect('login')
        else:
            # Not verified → redirect to verify OTP page
            request.session['otp_email'] = user.email
            return redirect('verify_otp', user_id=user.id)

    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if not getattr(user, 'is_verified', False):
                # Send new OTP and redirect to verify page
                user.otp_code = get_random_string(length=6, allowed_chars='0123456789')
                user.otp_created_at = timezone.now()
                user.save()
                send_otp_email(user)

                request.session['otp_email'] = user.email
                messages.info(request, "Your account is not verified. A new OTP has been sent to your email.")
                return redirect('verify_otp', user_id=user.id)

            # Verified users: check if active
            if not user.is_active:
                messages.error(request, "Your account is inactive. Please contact the administrator.")
                return redirect('login')

            # Verified and active → log them in and redirect by role
            login(request, user)

            if user.is_superuser or user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'customer':
                return redirect('customer_page')
            elif user.role == 'store_owner':
                return redirect('store_owner_page')
            elif user.role == 'store_manager':
                return redirect('store_manager_page')
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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def customer_page(request):
    return render(request, 'mainpages/customer_page.html')



from django.shortcuts import render
from django.contrib.auth import get_user_model

User = get_user_model()
@login_required
def admin_dashboard(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()
    verified_users = User.objects.filter(is_verified=True).count()
    unverified_users = User.objects.filter(is_verified=False).count()

    users = User.objects.order_by('-date_joined')[:10]  # Latest 10 users

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'verified_users': verified_users,
        'unverified_users': unverified_users,
        'users': users,
    }
    return render(request, 'mainpages/admin_dashboard.html', context)



from store.models import Store
@login_required

def store_owner_page(request):
    if request.user.role != 'store_owner':
        return redirect('')  # restrict access if needed

    # Filter only the stores owned by the current store owner
    stores = Store.objects.filter(owner=request.user).select_related('manager_assignment__manager')

    return render(request, 'mainpages/store_owner_page.html', {
        'stores': stores
    })


from django.shortcuts import render
from store.models import Store  # adjust path if needed

@login_required
def store_manager_page(request):
    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        store = None

    cashier_assignment = None
    if store:
        cashier_assignment = StoreCashier.objects.filter(store=store, is_active=True).first()

    return render(request, 'mainpages/store_manager_page.html', {
        'store': store,
        'cashier_assignment': cashier_assignment
    })
from store.models import Store, Order  # adjust path if needed
from transactions.models import Transaction

@login_required
def cashier_page(request):
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')[:10]
    transactions = [order.transaction for order in orders if order.transaction]
    return render(request, 'mainpages/cashier_page.html', {'transactions': transactions})

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.db.models import Q
from .forms import ChangeUserRoleForm  # You'll create this form.

User = get_user_model()

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

    paginator = Paginator(users.order_by('username'), 5)  # Show 10 users per page
    page_obj = paginator.get_page(page_number)

    context = {
        'users': page_obj.object_list,
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': page_obj.has_other_pages(),  # Optional but useful in template
        'search_query': search_query,
        'role_filter': role_filter,
        'total_users': users.count()
    }
    return render(request, 'admin/manage_users.html', context)

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
