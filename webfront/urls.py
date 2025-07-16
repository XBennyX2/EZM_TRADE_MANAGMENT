# webfront/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_page, name='webfront_home'),
    path('stock/', views.stock_list, name='webfront_stock_list'),
    path('stock/<int:stock_id>/', views.stock_detail, name='webfront_stock_detail'),
    path('store/<int:store_id>/', views.store_stock_view, name='webfront_store_stock'),
    path('product/<int:product_id>/stores/', views.product_stores_view, name='webfront_product_stores'),
    path('api/stock-search/', views.api_stock_search, name='webfront_api_stock_search'),
]
