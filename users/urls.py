# users/urls.py
from django.urls import path
from .views import login_view, logout_view, admin_dashboard, store_manager_page, cashier_page, change_password, head_manager_page, manage_users, toggle_user_status, change_user_role, view_user_detail, create_user, admin_settings

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    #admin
     path('admin/manage-users/', manage_users, name='manage_users'),
    path('admin/user/<int:user_id>/toggle-status/', toggle_user_status, name='toggle_user_status'),
    path('admin/user/<int:user_id>/change-role/', change_user_role, name='change_user_role'),
    path('admin/user/<int:user_id>/', view_user_detail, name='view_user_detail'),
    path('admin/create-user/', create_user, name='create_user'),

    # Role-based pages
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('head-manager/', head_manager_page, name='head_manager_page'),
    path('store-manager/', store_manager_page, name='store_manager_page'),
    path('cashier/', cashier_page, name='cashier_page'),
    path('change_password/', change_password, name='change_password'),
    path('admin/settings/', admin_settings, name='admin_settings'),
]
