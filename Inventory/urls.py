from django.urls import path
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView,
    StockListView, StockCreateView, StockUpdateView, StockDeleteView,
    SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView,
    WarehouseListView, WarehouseDetailView, WarehouseCreateView, WarehouseUpdateView, WarehouseDeleteView,
    SupplierProductListView, WarehouseProductCreateView, WarehouseProductUpdateView, WarehouseProductDeleteView,
    PurchaseOrderListView, PurchaseOrderCreateView, PurchaseOrderDetailView, PurchaseOrderUpdateView,
    activate_supplier_account, supplier_account_status, supplier_profile_view, supplier_product_catalog_view,
    purchase_request_list, purchase_request_create, purchase_request_detail, purchase_request_from_catalog,
    convert_request_to_order
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

    # Supplier URLs
    path('suppliers/', SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/new/', SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/edit/', SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<int:pk>/delete/', SupplierDeleteView.as_view(), name='supplier_delete'),
    path('suppliers/<int:supplier_id>/products/', SupplierProductListView.as_view(), name='supplier_products'),
    path('suppliers/<int:supplier_id>/products/new/', WarehouseProductCreateView.as_view(), name='warehouse_product_create'),
    path('suppliers/<int:supplier_id>/profile/', supplier_profile_view, name='supplier_profile_view'),
    path('suppliers/<int:supplier_id>/catalog/', supplier_product_catalog_view, name='supplier_product_catalog_view'),
    path('suppliers/<int:supplier_id>/activate/', activate_supplier_account, name='activate_supplier_account'),
    path('suppliers/<int:supplier_id>/status/', supplier_account_status, name='supplier_account_status'),
    path('warehouse-products/<int:pk>/edit/', WarehouseProductUpdateView.as_view(), name='warehouse_product_update'),
    path('warehouse-products/<int:pk>/delete/', WarehouseProductDeleteView.as_view(), name='warehouse_product_delete'),

    # Warehouse URLs
    path('warehouses/', WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/<int:pk>/', WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/new/', WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/edit/', WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('warehouses/<int:pk>/delete/', WarehouseDeleteView.as_view(), name='warehouse_delete'),

    # Purchase Order URLs
    path('purchase-orders/', PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('purchase-orders/new/', PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('purchase-orders/<int:pk>/', PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/edit/', PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),

    # Purchase Requests
    path('purchase-requests/', purchase_request_list, name='purchase_request_list'),
    path('purchase-requests/create/', purchase_request_create, name='purchase_request_create'),
    path('purchase-requests/<int:pk>/', purchase_request_detail, name='purchase_request_detail'),
    path('purchase-requests/<int:pk>/convert/', convert_request_to_order, name='convert_request_to_order'),
    path('suppliers/<int:supplier_id>/request/', purchase_request_from_catalog, name='purchase_request_from_catalog'),
]