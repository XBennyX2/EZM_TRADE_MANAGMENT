
from django.urls import path
from . import views

app_name = 'webfront'

urlpatterns = [
    # Home page (main page)
    path('', views.home_page, name='home'),

    # Browse products page
    path('products/', views.stock_list, name='stock_list'),

    # Stock detail view
    path('stock/<int:stock_id>/', views.stock_detail, name='stock_detail'),

    # Store-specific stock view
    path('store/<int:store_id>/', views.store_stock_view, name='store_stock'),

    # Product across stores view
    path('product/<int:product_id>/stores/', views.product_stores_view, name='product_stores'),

    # API endpoints
    path('api/search/', views.api_stock_search, name='api_stock_search'),

    # Cart and ticket URLs
    path('api/cart/validate/', views.validate_cart, name='validate_cart'),
    path('api/cart/create-ticket/', views.create_ticket, name='create_ticket'),
    path('api/ticket/status/', views.check_ticket_status, name='check_ticket_status'),
]
