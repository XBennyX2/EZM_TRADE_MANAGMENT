# users/urls.py
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from .views import (
    login_view, logout_view, admin_dashboard, store_manager_page, cashier_page, head_manager_page,
    manage_users, toggle_user_status, change_user_role, view_user_detail, create_user, delete_user,
    admin_settings, admin_edit_profile, admin_change_password, head_manager_settings,
    head_manager_change_password, head_manager_edit_profile,
    store_manager_settings, store_manager_change_password, cashier_settings, cashier_edit_profile, cashier_change_password,
    CustomPasswordChangeView,
    # Store Manager request views
    submit_restock_request, submit_transfer_request, update_product_price,
    # Head Manager request management views
    head_manager_restock_requests, head_manager_transfer_requests,
    approve_restock_request, reject_restock_request,
    approve_transfer_request, reject_transfer_request
)

# Import API views
from . import api_views
from .supplier_views import (
    supplier_dashboard, supplier_account, supplier_purchase_orders, supplier_invoices,
    supplier_payments, supplier_transactions, supplier_products, supplier_reports, supplier_settings,
    check_supplier_setup_status, supplier_onboarding, supplier_product_catalog,
    supplier_add_product, supplier_edit_product, supplier_delete_product
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    #admin
     path('admin/manage-users/', manage_users, name='manage_users'),
    path('admin/user/<int:user_id>/toggle-status/', toggle_user_status, name='toggle_user_status'),
    path('admin/user/<int:user_id>/change-role/', change_user_role, name='change_user_role'),
    path('admin/user/<int:user_id>/delete/', delete_user, name='delete_user'),
    path('admin/user/<int:user_id>/', view_user_detail, name='view_user_detail'),
    path('admin/create-user/', create_user, name='create_user'),

    # Role-based pages
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('head-manager/', head_manager_page, name='head_manager_page'),
    path('store-manager/', store_manager_page, name='store_manager_page'),
    path('cashier/', cashier_page, name='cashier_page'),

    # Store Manager request URLs
    path('store-manager/submit-restock-request/', submit_restock_request, name='submit_restock_request'),
    path('store-manager/submit-transfer-request/', submit_transfer_request, name='submit_transfer_request'),
    path('store-manager/update-product-price/', update_product_price, name='update_product_price'),

    # Head Manager request management URLs
    path('head-manager/restock-requests/', head_manager_restock_requests, name='head_manager_restock_requests'),
    path('head-manager/transfer-requests/', head_manager_transfer_requests, name='head_manager_transfer_requests'),
    path('head-manager/restock-requests/<int:request_id>/approve/', approve_restock_request, name='approve_restock_request'),
    path('head-manager/restock-requests/<int:request_id>/reject/', reject_restock_request, name='reject_restock_request'),
    path('head-manager/transfer-requests/<int:request_id>/approve/', approve_transfer_request, name='approve_transfer_request'),
    path('head-manager/transfer-requests/<int:request_id>/reject/', reject_transfer_request, name='reject_transfer_request'),


    path('admin/settings/', admin_settings, name='admin_settings'),
    path('admin/profile/edit/', admin_edit_profile, name='admin_edit_profile'),
    path('admin/profile/change-password/', admin_change_password, name='admin_change_password'),
    path('head-manager/settings/', head_manager_settings, name='head_manager_settings'),
    path('head-manager/profile/edit/', head_manager_edit_profile, name='head_manager_edit_profile'),
    path('head-manager/profile/change-password/', head_manager_change_password, name='head_manager_change_password'),
    path('store-manager/settings/', store_manager_settings, name='store_manager_settings'),
    path('store-manager/profile/change-password/', store_manager_change_password, name='store_manager_change_password'),
    path('cashier/settings/', cashier_settings, name='cashier_settings'),
    path('cashier/profile/edit/', cashier_edit_profile, name='cashier_edit_profile'),
    path('cashier/profile/change-password/', cashier_change_password, name='cashier_change_password'),

    # Generic password change for all authenticated users
    path('account/password/', CustomPasswordChangeView.as_view(), name='password_change'),

    # Password reset URLs
    path('password-reset/', PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        subject_template_name='users/password_reset_subject.txt',
        success_url='/users/password-reset/done/'
    ), name='password_reset'),

    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url='/users/password-reset-complete/'
    ), name='password_reset_confirm'),

    path('password-reset-complete/', PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Supplier URLs
    path('supplier/dashboard/', supplier_dashboard, name='supplier_dashboard'),
    path('supplier/account/', supplier_account, name='supplier_account'),
    path('supplier/purchase-orders/', supplier_purchase_orders, name='supplier_purchase_orders'),
    path('supplier/invoices/', supplier_invoices, name='supplier_invoices'),
    path('supplier/payments/', supplier_payments, name='supplier_payments'),
    path('supplier/transactions/', supplier_transactions, name='supplier_transactions'),
    path('supplier/products/', supplier_products, name='supplier_products'),
    path('supplier/reports/', supplier_reports, name='supplier_reports'),
    path('supplier/settings/', supplier_settings, name='supplier_settings'),
    path('supplier/onboarding/', supplier_onboarding, name='supplier_onboarding'),
    path('supplier/catalog/', supplier_product_catalog, name='supplier_product_catalog'),
    path('supplier/catalog/add/', supplier_add_product, name='supplier_add_product'),
    path('supplier/catalog/<int:product_id>/edit/', supplier_edit_product, name='supplier_edit_product'),
    path('supplier/catalog/<int:product_id>/delete/', supplier_delete_product, name='supplier_delete_product'),
    path('supplier/setup-status/', check_supplier_setup_status, name='supplier_setup_status'),
    path('supplier/dashboard-test/', lambda request: render(request, 'supplier/dashboard_test.html'), name='supplier_dashboard_test'),
]
