# users/urls.py
from django.urls import path
from django.shortcuts import render
from django.contrib.auth.views import (
    PasswordChangeView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from .views import (
    login_view, logout_view, admin_dashboard, store_manager_page, cashier_page, head_manager_page,
    manage_users, toggle_user_status, change_user_role, view_user_detail, create_user, delete_user,
    admin_settings, admin_edit_profile, admin_change_password, head_manager_settings,
    head_manager_change_password, head_manager_edit_profile,
    store_manager_settings, store_manager_edit_profile, store_manager_change_password, cashier_settings, cashier_edit_profile, cashier_change_password,
    CustomPasswordChangeView, CustomPasswordResetView, admin_login_logs, reset_user_account,
    # Store Manager request views
    submit_restock_request, submit_transfer_request, update_product_price,
    store_manager_restock_requests, store_manager_transfer_requests, store_manager_stock_management,
    mark_restock_received,
    # Head Manager request management views
    head_manager_restock_requests,
    approve_restock_request, reject_restock_request,
    # API endpoints for product dropdowns
    get_restock_products, get_transfer_products, get_stores_with_product, warehouse_products_api,
    # Analytics views
    analytics_dashboard, financial_reports, analytics_api,
    # Transaction history
    transaction_history,
    # Sales report
    store_sales_report,
    # PDF export
    export_store_report,
    # Stock threshold update
    update_stock_threshold,
    # Warehouse products view
    store_manager_warehouse_products,
    # First login password change
    first_login_password_change
)

# Import API views
from . import api_views
from .supplier_views import (
    supplier_dashboard, supplier_account, supplier_purchase_orders, supplier_invoices,
    supplier_payments, supplier_transactions, supplier_products, supplier_reports, supplier_settings,
    check_supplier_setup_status, supplier_onboarding, supplier_product_catalog,
    supplier_add_product, supplier_edit_product, supplier_delete_product, supplier_adjust_stock,
    supplier_payment_notifications_api, api_warehouse_products, api_product_categories, supplier_mark_in_transit
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('first-login-password-change/', first_login_password_change, name='first_login_password_change'),

    #admin
     path('admin/manage-users/', manage_users, name='manage_users'),
    path('admin/user/<int:user_id>/toggle-status/', toggle_user_status, name='toggle_user_status'),
    path('admin/user/<int:user_id>/change-role/', change_user_role, name='change_user_role'),
    path('admin/user/<int:user_id>/delete/', delete_user, name='delete_user'),
    path('admin/user/<int:user_id>/', view_user_detail, name='view_user_detail'),
    path('admin/user/<int:user_id>/reset/', reset_user_account, name='reset_user_account'),
    path('admin/create-user/', create_user, name='create_user'),
    path('admin/login-logs/', admin_login_logs, name='admin_login_logs'),

    # Role-based pages
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('head-manager/', head_manager_page, name='head_manager_page'),
    path('store-manager/', store_manager_page, name='store_manager_page'),
    path('cashier/', cashier_page, name='cashier_page'),

    # Store Manager request URLs
    path('store-manager/submit-restock-request/', submit_restock_request, name='submit_restock_request'),
    path('store-manager/submit-transfer-request/', submit_transfer_request, name='submit_transfer_request'),
    path('store-manager/update-product-price/', update_product_price, name='update_product_price'),
    path('store-manager/restock-requests/', store_manager_restock_requests, name='store_manager_restock_requests'),
    path('store-manager/mark-restock-received/', mark_restock_received, name='mark_restock_received'),
    path('store-manager/transfer-requests/', store_manager_transfer_requests, name='store_manager_transfer_requests'),
    path('store-manager/stock-management/', store_manager_stock_management, name='store_manager_stock_management'),
    path('store-manager/sales-report/', store_sales_report, name='store_sales_report'),
    path('store-manager/export-report/', export_store_report, name='export_store_report'),
    path('store-manager/update-threshold/', update_stock_threshold, name='update_stock_threshold'),
    path('store-manager/warehouse-products/', store_manager_warehouse_products, name='store_manager_warehouse_products'),

    # API endpoints for product dropdowns
    path('api/restock-products/', get_restock_products, name='get_restock_products'),
    path('api/transfer-products/', get_transfer_products, name='get_transfer_products'),
    path('api/stores-with-product/', get_stores_with_product, name='get_stores_with_product'),

    # API endpoints for supplier product selection
    path('api/warehouse-products/', warehouse_products_api, name='warehouse_products_api'),
    path('api/warehouse-products-legacy/', api_warehouse_products, name='api_warehouse_products'),
    path('api/product-categories/', api_product_categories, name='api_product_categories'),

    # Head Manager request management URLs
    path('head-manager/restock-requests/', head_manager_restock_requests, name='head_manager_restock_requests'),
    path('head-manager/restock-requests/<int:request_id>/approve/', approve_restock_request, name='approve_restock_request'),
    path('head-manager/restock-requests/<int:request_id>/reject/', reject_restock_request, name='reject_restock_request'),

    # Analytics and Reports URLs
    path('head-manager/analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('head-manager/financial-reports/', financial_reports, name='financial_reports'),
    path('api/analytics/', analytics_api, name='analytics_api'),


    path('admin/settings/', admin_settings, name='admin_settings'),
    path('admin/profile/edit/', admin_edit_profile, name='admin_edit_profile'),
    path('admin/profile/change-password/', admin_change_password, name='admin_change_password'),
    path('head-manager/settings/', head_manager_settings, name='head_manager_settings'),
    path('head-manager/profile/edit/', head_manager_edit_profile, name='head_manager_edit_profile'),
    path('head-manager/profile/change-password/', head_manager_change_password, name='head_manager_change_password'),
    path('store-manager/settings/', store_manager_settings, name='store_manager_settings'),
    path('store-manager/profile/edit/', store_manager_edit_profile, name='store_manager_edit_profile'),
    path('store-manager/profile/change-password/', store_manager_change_password, name='store_manager_change_password'),
    path('cashier/settings/', cashier_settings, name='cashier_settings'),
    path('cashier/profile/edit/', cashier_edit_profile, name='cashier_edit_profile'),
    path('cashier/profile/change-password/', cashier_change_password, name='cashier_change_password'),

    # Generic password change for all authenticated users
    path('account/password/', CustomPasswordChangeView.as_view(), name='password_change'),

    # Password reset URLs
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),

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
    path('supplier/payments/notifications/', supplier_payment_notifications_api, name='supplier_payment_notifications_api'),
    path('supplier/transactions/', supplier_transactions, name='supplier_transactions'),
    path('supplier/products/', supplier_products, name='supplier_products'),
    path('supplier/reports/', supplier_reports, name='supplier_reports'),
    path('supplier/settings/', supplier_settings, name='supplier_settings'),
    path('supplier/onboarding/', supplier_onboarding, name='supplier_onboarding'),
    path('supplier/catalog/', supplier_product_catalog, name='supplier_product_catalog'),
    path('supplier/catalog/add/', supplier_add_product, name='supplier_add_product'),
    path('supplier/catalog/<int:product_id>/edit/', supplier_edit_product, name='supplier_edit_product'),
    path('supplier/catalog/<int:product_id>/delete/', supplier_delete_product, name='supplier_delete_product'),
    path('supplier/catalog/adjust-stock/', supplier_adjust_stock, name='supplier_adjust_stock'),
    path('supplier/setup-status/', check_supplier_setup_status, name='supplier_setup_status'),
    path('supplier/orders/<int:order_id>/mark-in-transit/', supplier_mark_in_transit, name='supplier_mark_in_transit'),
    path('supplier/dashboard-test/', lambda request: render(request, 'supplier/dashboard_test.html'), name='supplier_dashboard_test'),

    # Transaction History
    path('transaction-history/', transaction_history, name='transaction_history'),
]
