from django.urls import path
from . import views

urlpatterns = [
    # Payment initiation
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    
    # Payment selection for multiple suppliers
    path('selection/', views.payment_selection, name='payment_selection'),
    
    # Payment success/return from Chapa
    path('success/', views.payment_success, name='payment_success'),

    # Payment completed page
    path('completed/<str:tx_ref>/', views.payment_completed, name='payment_completed'),

    # Payment status page
    path('status/<str:tx_ref>/', views.payment_status, name='payment_status'),
    
    # Webhook endpoint
    path('webhook/', views.chapa_webhook, name='chapa_webhook'),
    
    # Payment methods information
    path('methods/', views.payment_methods_info, name='payment_methods_info'),

    # Payment history
    path('history/', views.payment_history, name='payment_history'),

    # Receipt and invoice downloads
    path('receipt/<str:tx_ref>/', views.download_payment_receipt, name='download_payment_receipt'),
    path('invoice/<str:order_id>/', views.download_order_invoice, name='download_order_invoice'),
]
