# users/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('register/', register_view, name='register'),
    path('verify-otp/<int:user_id>/', verify_otp_view, name='verify_otp'),
    path('resend-otp/<int:user_id>/', resend_otp, name='resend_otp'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    #admin
     path('admin/manage-users/', manage_users, name='manage_users'),
    path('admin/user/<int:user_id>/toggle-status/', toggle_user_status, name='toggle_user_status'),
    path('admin/user/<int:user_id>/change-role/', change_user_role, name='change_user_role'),
    path('admin/user/<int:user_id>/', view_user_detail, name='view_user_detail'),

    # Role-based pages
    path('customer/', customer_page, name='customer_page'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('store-owner/', store_owner_page, name='store_owner_page'),
    path('store-manager/', store_manager_page, name='store_manager_page'),
    path('cashier/', cashier_page, name='cashier_page'),
]
