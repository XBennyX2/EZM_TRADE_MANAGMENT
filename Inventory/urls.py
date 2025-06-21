from django.urls import path
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView,
    StockListView, StockCreateView, StockUpdateView, StockDeleteView
)

urlpatterns = [
    # Product URLs
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/new/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),

    # Stock URLs
    path('stock/', StockListView.as_view(), name='stock_list'),
    path('stock/new/', StockCreateView.as_view(), name='stock_create'),
    path('stock/<int:pk>/update/', StockUpdateView.as_view(), name='stock_update'),
    path('stock/<int:pk>/delete/', StockDeleteView.as_view(), name='stock_delete'),
]