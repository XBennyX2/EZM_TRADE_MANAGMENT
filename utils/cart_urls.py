"""
URL patterns for shopping cart functionality
"""

from django.urls import path
from utils.cart_views import (
    cart_view,
    cart_add,
    cart_remove,
    cart_update_quantity,
    cart_clear,
    cart_count,
    order_confirmation,
    proceed_to_purchase_requests
)

urlpatterns = [
    path('', cart_view, name='cart_view'),
    path('add/', cart_add, name='cart_add'),
    path('remove/', cart_remove, name='cart_remove'),
    path('update/', cart_update_quantity, name='cart_update_quantity'),
    path('clear/', cart_clear, name='cart_clear'),
    path('count/', cart_count, name='cart_count'),
    path('order-confirmation/', order_confirmation, name='order_confirmation'),
    path('proceed/', proceed_to_purchase_requests, name='proceed_to_purchase_requests'),
]
