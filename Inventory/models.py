from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from store.models import Store
from transactions.models import Transaction
from decimal import Decimal

SETTINGS_CHOICES = [
    ('Pipes', 'Pipes'),
    ('Electric Wire', 'Electric Wire'),
    ('Cement', 'Cement'),
    ('Ceramics', 'Ceramics'),
    ('Glass and Finishing Materials', 'Glass and Finishing Materials'),
]

PRODUCT_TYPE_CHOICES = [
    ('raw_material', 'Raw Material'),
    ('finished_product', 'Finished Product'),
    ('component', 'Component'),
    ('tool', 'Tool'),
    ('equipment', 'Equipment'),
    ('consumable', 'Consumable'),
]

SIZE_CHOICES = [
    ('XS', 'Extra Small'),
    ('S', 'Small'),
    ('M', 'Medium'),
    ('L', 'Large'),
    ('XL', 'Extra Large'),
    ('XXL', 'Double Extra Large'),
    ('custom', 'Custom Size'),
]

STORING_CONDITION_CHOICES = [
    ('room_temperature', 'Room Temperature'),
    ('cool_dry_place', 'Cool Dry Place'),
    ('moisture_free', 'Moisture Free'),
    ('temperature_sensitive', 'Temperature Sensitive'),
    ('electrical_safe', 'Electrical Safe Storage'),
    ('ceramic_safe', 'Ceramic Safe Storage'),
    ('chemical_safe', 'Chemical Safe Storage'),
]

class Product(models.Model):
    """
    Represents a specific product with its details.
    """
    # Basic Information
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, choices=SETTINGS_CHOICES, default='')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    material = models.TextField()

    # Product Specifications
    size = models.CharField(max_length=50, choices=SIZE_CHOICES, blank=True, null=True, help_text="Product size")
    variation = models.CharField(max_length=100, blank=True, null=True, help_text="Product variation (color, model, etc.)")
    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPE_CHOICES, default='finished_product', help_text="Type of product")

    # Supplier Information
    supplier_company = models.CharField(max_length=200, blank=True, null=True, help_text="Supplier company name")

    # Batch and Tracking
    batch_number = models.CharField(max_length=100, blank=True, null=True, help_text="Batch or lot number")
    expiry_date = models.DateField(blank=True, null=True, help_text="Product expiry date (if applicable)")

    # Storage Location
    room = models.CharField(max_length=50, blank=True, null=True, help_text="Storage room")
    shelf = models.CharField(max_length=50, blank=True, null=True, help_text="Shelf location")
    floor = models.CharField(max_length=50, blank=True, null=True, help_text="Floor level")

    # Storage Conditions
    storing_condition = models.CharField(
        max_length=50,
        choices=STORING_CONDITION_CHOICES,
        default='room_temperature',
        help_text="Required storage conditions"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['supplier_company']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.variation})" if self.variation else self.name

    def is_expired(self):
        """Check if product is expired"""
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date < timezone.now().date()
        return False

    def get_full_location(self):
        """Get complete storage location"""
        location_parts = []
        if self.room:
            location_parts.append(f"Room: {self.room}")
        if self.floor:
            location_parts.append(f"Floor: {self.floor}")
        if self.shelf:
            location_parts.append(f"Shelf: {self.shelf}")
        return " | ".join(location_parts) if location_parts else "Location not specified"

class Stock(models.Model):
    """
    Tracks the quantity of a specific product at a specific store.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_levels')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stock_items')
    quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    low_stock_threshold = models.PositiveIntegerField(default=10, help_text="Threshold for low stock alerts.")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price of the product at this store.")  # New field

    class Meta:
        unique_together = ('product', 'store')  # Ensures one stock entry per product per store

    def __str__(self):
        return f'{self.product.name} at {self.store.name}: {self.quantity}'

class StockTransferRequest(models.Model):
    """
    Manages the request-and-approval workflow for moving stock between stores.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    from_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='transfer_requests_sent')
    to_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='transfer_requests_received')
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    resolution_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Transfer of {self.quantity} {self.product.name} from {self.from_store.name}'
    # In transactions/models.py

class ReturnRequest(models.Model):
    """
    Manages the customer's request to return a product.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    original_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, limit_choices_to={'transaction_type': 'sale'})
    reason = models.TextField(help_text="Reason for the return request.")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_date = models.DateTimeField(auto_now_add=True)
    resolution_date = models.DateTimeField(null=True, blank=True)
    is_item_restocked = models.BooleanField(default=False, help_text="Indicates if the item was returned to inventory.")

    def __str__(self):
        return f"Return request for transaction {self.original_transaction.id}"


class Supplier(models.Model):
    """
    Represents a supplier that provides products to the warehouse.
    """
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class WarehouseProduct(models.Model):
    """
    Represents products available in the warehouse with detailed information.
    """
    product_id = models.CharField(max_length=50, unique=True, help_text="Unique identifier for the product")
    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, choices=SETTINGS_CHOICES)
    quantity_in_stock = models.PositiveIntegerField(
        default=0,
        help_text="Current quantity available in warehouse",
        validators=[MinValueValidator(0)]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Cost price per unit from supplier",
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    minimum_stock_level = models.PositiveIntegerField(
        default=10,
        help_text="Minimum quantity that should be maintained in warehouse"
    )
    maximum_stock_level = models.PositiveIntegerField(
        default=1000,
        help_text="Maximum quantity that can be stored in warehouse"
    )
    reorder_point = models.PositiveIntegerField(
        default=20,
        help_text="Stock level at which reorder should be triggered"
    )
    sku = models.CharField(max_length=100, unique=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, blank=True, help_text="Product barcode")
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Weight per unit in kg"
    )
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        help_text="Product dimensions (L x W x H)"
    )
    is_active = models.BooleanField(default=True, help_text="Whether product is currently available")
    is_discontinued = models.BooleanField(default=False, help_text="Whether product is discontinued")
    warehouse_location = models.CharField(
        max_length=50,
        blank=True,
        help_text="Physical location in warehouse (e.g., Aisle A, Shelf 3)"
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='warehouse_products',
        help_text="Primary supplier for this product"
    )
    warehouse = models.ForeignKey(
        'Warehouse',
        on_delete=models.CASCADE,
        related_name='products',
        help_text="Warehouse where this product is stored",
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['product_name', 'category']

    def __str__(self):
        return f"{self.product_name} ({self.product_id})"


class WarehouseStockMovement(models.Model):
    """
    Tracks all stock movements in the warehouse for audit purposes.
    """
    MOVEMENT_CHOICES = [
        ('receipt', 'Stock Receipt'),
        ('shipment', 'Stock Shipment'),
        ('adjustment', 'Stock Adjustment'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('return', 'Return'),
        ('damage', 'Damage/Loss'),
    ]

    warehouse_product = models.ForeignKey(
        WarehouseProduct,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity_change = models.IntegerField(help_text="Positive for additions, negative for reductions")
    previous_stock_level = models.PositiveIntegerField(default=0)
    new_stock_level = models.PositiveIntegerField(default=0)
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="PO number, invoice number, etc."
    )
    reason = models.TextField(help_text="Reason for stock movement")
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.movement_type} - {self.quantity_change} units of {self.warehouse_product.product_name}"


class PurchaseOrder(models.Model):
    """
    Represents purchase orders created by head manager to suppliers.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('shipped', 'Shipped'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_purchase_orders'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField(blank=True, null=True)
    actual_delivery_date = models.DateField(blank=True, null=True)
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    notes = models.TextField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"PO-{self.order_number} - {self.supplier.name}"


class PurchaseOrderItem(models.Model):
    """
    Individual items in a purchase order.
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    warehouse_product = models.ForeignKey(WarehouseProduct, on_delete=models.PROTECT)
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    def save(self, *args, **kwargs):
        self.total_price = self.quantity_ordered * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.warehouse_product.product_name} - {self.quantity_ordered} units"


class Warehouse(models.Model):
    """
    Represents warehouse information and details.
    """
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    manager_name = models.CharField(max_length=100, blank=True)
    capacity = models.PositiveIntegerField(help_text="Maximum storage capacity")
    current_utilization = models.PositiveIntegerField(default=0, help_text="Current storage utilization")
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def utilization_percentage(self):
        if self.capacity > 0:
            return (self.current_utilization / self.capacity) * 100
        return 0