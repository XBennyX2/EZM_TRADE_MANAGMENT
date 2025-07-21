from django.urls import path
from . import views

urlpatterns = [
    # ... other URL patterns
    path('process_sale/', views.process_sale, name='process_sale'),
    path('get_product_price/<int:product_id>/', views.get_product_price, name='get_product_price'),
    path('create_store/', views.create_store, name='create_store'),
    path('manage_store/<int:store_id>/', views.manage_store, name='manage_store'),

    # Showroom Management URLs
    path('showrooms/', views.ShowroomListView.as_view(), name='showroom_list'),
    path('showrooms/<int:pk>/', views.ShowroomDetailView.as_view(), name='showroom_detail'),
    path('showrooms/new/', views.ShowroomCreateView.as_view(), name='showroom_create'),
    path('showrooms/<int:pk>/edit/', views.ShowroomUpdateView.as_view(), name='showroom_update'),
    path('showrooms/<int:pk>/delete/', views.ShowroomDeleteView.as_view(), name='showroom_delete'),

# Cashier Order System URLs
    path('process-single-sale/', views.process_single_sale, name='process_single_sale'),
    path('cashier/initiate-order/', views.initiate_order, name='initiate_order'),
    path('cashier/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cashier/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('cashier/complete-order/', views.complete_order, name='complete_order'),
    path('cashier/cart-status/', views.get_cart_status, name='get_cart_status'),
    path('cashier/transactions/', views.cashier_transactions, name='cashier_transactions'),
    path('receipt/<int:receipt_id>/', views.view_receipt, name='view_receipt'),
    path('receipt/<int:receipt_id>/pdf/', views.generate_receipt_pdf, name='generate_receipt_pdf'),
    path('receipt/<int:receipt_id>/email/', views.email_receipt, name='email_receipt'),

    # Store Manager Cashier Assignment URLs
    path('manager/assign-cashier/', views.assign_cashier, name='assign_cashier'),
    path('manager/assign-cashier/<int:store_id>/', views.assign_cashier, name='assign_cashier_to_store'),
    path('manager/create-cashier/', views.create_cashier, name='create_cashier'),
    path('manager/edit-cashier/<int:cashier_id>/', views.edit_cashier, name='edit_cashier'),
    path('manager/remove-cashier/<int:cashier_id>/', views.remove_cashier, name='remove_cashier'),
    path('manager/manage-cashiers/', views.manage_cashiers, name='manage_cashiers'),
    path('products/', views.store_product_list, name='store_product_list'),

    # Store Manager Transfer Request Approval URLs
    path('manager/approve-transfer-request/<int:request_id>/', views.approve_store_transfer_request, name='approve_store_transfer_request'),
    path('manager/decline-transfer-request/<int:request_id>/', views.decline_store_transfer_request, name='decline_store_transfer_request'),
    path('manager/complete-transfer-request/<int:request_id>/', views.complete_store_transfer_request, name='complete_store_transfer_request'),

    # Ticket Management API URLs
    path('api/tickets/', views.api_tickets_list, name='api_tickets_list'),
    path('api/tickets/<str:ticket_number>/', views.api_ticket_detail, name='api_ticket_detail'),
    path('api/tickets/<str:ticket_number>/status/', views.api_ticket_update_status, name='api_ticket_update_status'),
    path('api/tickets/<str:ticket_number>/process/', views.api_ticket_process, name='api_ticket_process'),

    # Ticket Processing URL
    path('process-ticket/<str:ticket_number>/', views.process_ticket_to_order, name='process_ticket_to_order'),
    path('api/tickets/<str:ticket_number>/', views.get_ticket_api, name='get_ticket_api'),
]