from django.urls import path
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView,
    StockListView, StockCreateView, StockUpdateView, StockDeleteView,
    SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView,
    WarehouseListView, WarehouseDetailView, WarehouseCreateView, WarehouseUpdateView, WarehouseDeleteView, WarehouseDebugView,
    SupplierProductListView, WarehouseProductCreateView, WarehouseProductUpdateView, WarehouseProductDeleteView,
    PurchaseOrderListView, PurchaseOrderCreateView, PurchaseOrderDetailView, PurchaseOrderUpdateView,
    activate_supplier_account, supplier_account_status, supplier_profile_view, supplier_product_catalog_view,
    purchase_request_list, purchase_request_create, purchase_request_detail, purchase_request_from_catalog,
    convert_request_to_order, WarehouseProductStockEditView, warehouse_product_toggle_status,
    ProductStockThresholdEditView, product_toggle_status
)
from . import order_tracking_views
from . import stock_alert_views
from . import restock_workflow_views
from . import fifo_views

urlpatterns = [
    # Product URLs
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/new/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),
    path('products/<int:pk>/edit-threshold/', ProductStockThresholdEditView.as_view(), name='product_stock_threshold_edit'),
    path('products/<int:pk>/toggle-status/', product_toggle_status, name='product_toggle_status'),

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
    path('warehouse-products/new/', WarehouseProductCreateView.as_view(), name='warehouse_product_create_direct'),
    path('suppliers/<int:supplier_id>/profile/', supplier_profile_view, name='supplier_profile_view'),
    path('suppliers/<int:supplier_id>/catalog/', supplier_product_catalog_view, name='supplier_product_catalog_view'),
    path('suppliers/<int:supplier_id>/activate/', activate_supplier_account, name='activate_supplier_account'),
    path('suppliers/<int:supplier_id>/status/', supplier_account_status, name='supplier_account_status'),
    path('warehouse-products/<int:pk>/edit/', WarehouseProductUpdateView.as_view(), name='warehouse_product_update'),
    path('warehouse-products/<int:pk>/delete/', WarehouseProductDeleteView.as_view(), name='warehouse_product_delete'),
    path('warehouse-products/<int:pk>/edit-stock/', WarehouseProductStockEditView.as_view(), name='warehouse_product_stock_edit'),
    path('warehouse-products/<int:pk>/toggle-status/', warehouse_product_toggle_status, name='warehouse_product_toggle_status'),

    # Warehouse URLs
    path('warehouses/', WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/debug/', WarehouseDebugView.as_view(), name='warehouse_debug'),
    path('warehouses/<int:pk>/', WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouses/new/', WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/edit/', WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('warehouses/<int:pk>/delete/', WarehouseDeleteView.as_view(), name='warehouse_delete'),

    # Purchase Order URLs
    path('purchase-orders/', PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('purchase-orders/new/', PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('purchase-orders/<int:pk>/', PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/edit/', PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),

    # Order tracking and delivery confirmation APIs
    path('purchase-orders/<int:order_id>/details/', order_tracking_views.purchase_order_details_api, name='purchase_order_details_api'),
    path('purchase-orders/<int:order_id>/mark-in-transit/', order_tracking_views.mark_order_in_transit, name='mark_order_in_transit'),
    path('purchase-orders/<int:order_id>/confirm-delivery/', order_tracking_views.confirm_delivery, name='confirm_delivery'),
    path('purchase-orders/<int:order_id>/report-issue/', order_tracking_views.report_delivery_issue, name='report_delivery_issue'),
    path('purchase-orders/countdown-data/', order_tracking_views.countdown_data_api, name='countdown_data_api'),
    path('purchase-orders/statistics/', order_tracking_views.order_statistics_api, name='order_statistics_api'),

    # Purchase Requests
    path('purchase-requests/', purchase_request_list, name='purchase_request_list'),
    path('purchase-requests/create/', purchase_request_create, name='purchase_request_create'),
    path('purchase-requests/<int:pk>/', purchase_request_detail, name='purchase_request_detail'),
    path('purchase-requests/<int:pk>/convert/', convert_request_to_order, name='convert_request_to_order'),
    path('suppliers/<int:supplier_id>/request/', purchase_request_from_catalog, name='purchase_request_from_catalog'),

    # Stock Alert URLs
    path('stock-alerts/', stock_alert_views.stock_alerts_dashboard, name='stock_alerts_dashboard'),
    path('update-threshold/<int:product_id>/', stock_alert_views.update_stock_threshold, name='update_stock_threshold'),
    path('bulk-update-thresholds/', stock_alert_views.bulk_update_thresholds, name='bulk_update_thresholds'),
    path('warehouse-inventory/', stock_alert_views.warehouse_inventory_overview, name='warehouse_inventory_overview'),
    path('store-inventory/', stock_alert_views.store_inventory_view, name='store_inventory_view'),

    # Restock Workflow URLs
    path('restock-workflow/', restock_workflow_views.restock_workflow_dashboard, name='restock_workflow_dashboard'),
    path('restock-requests/<int:request_id>/ship/', restock_workflow_views.ship_restock_request, name='ship_restock_request'),
    path('restock-requests/<int:request_id>/receive/', restock_workflow_views.receive_restock_request, name='receive_restock_request'),
    path('store-restock-tracking/', restock_workflow_views.store_restock_tracking, name='store_restock_tracking'),
    path('api/warehouse-stock/<str:product_name>/', restock_workflow_views.get_warehouse_stock_info, name='get_warehouse_stock_info'),

    # FIFO Inventory URLs
    path('fifo-inventory/', fifo_views.fifo_inventory_view, name='fifo_inventory_view'),
    path('movement-history/<int:product_id>/', fifo_views.inventory_movement_history, name='inventory_movement_history'),
    path('api/fifo-product/<str:product_name>/', fifo_views.get_fifo_product_info, name='get_fifo_product_info'),
    path('batch-management/', fifo_views.batch_management_view, name='batch_management_view'),

    # Order Tracking URLs
    path('order-tracking/', order_tracking_views.order_tracking_dashboard, name='order_tracking_dashboard'),
    path('orders/<int:order_id>/confirm-delivery/', order_tracking_views.confirm_delivery, name='confirm_delivery'),
    path('orders/<int:order_id>/report-issue/', order_tracking_views.report_delivery_issue, name='report_delivery_issue'),
    path('orders/<int:order_id>/tracking/', order_tracking_views.order_tracking_detail, name='order_tracking_detail'),
]