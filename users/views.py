# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import CustomUserCreationForm, CustomLoginForm
from .models import CustomUser

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
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

@login_required
def admin_dashboard(request):
    return render(request, 'mainpages/admin_dashboard.html')

@login_required
def store_owner_page(request):
    return render(request, 'mainpages/store_owner_page.html')

@login_required
def store_manager_page(request):
    return render(request, 'mainpages/store_manager_page.html')

@login_required
def cashier_page(request):
    return render(request, 'mainpages/cashier_page.html')

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.db.models import Q
from .forms import ChangeUserRoleForm  # You'll create this form.

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

@user_passes_test(is_admin)
def manage_users(request):
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    users = User.objects.all()

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    if role_filter:
        users = users.filter(role=role_filter)

    context = {
        'users': users,
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
