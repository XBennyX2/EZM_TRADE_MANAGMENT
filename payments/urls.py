from django.urls import path
from . import views

urlpatterns = [
    # Payment initiation
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    
    # Payment selection for multiple suppliers
    path('selection/', views.payment_selection, name='payment_selection'),
    
    # Payment success/return from Chapa
    path('success/', views.payment_success, name='payment_success'),
    
    # Payment status page
    path('status/<str:tx_ref>/', views.payment_status, name='payment_status'),
    
    # Webhook endpoint
    path('webhook/', views.chapa_webhook, name='chapa_webhook'),
    
    # Payment history
    path('history/', views.payment_history, name='payment_history'),
]
