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
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price of the product at this store.")

    class Meta:
        unique_together = ('product', 'store')  # Ensures one stock entry per product per store
        ordering = ['product__expiry_date', 'product__batch_number', 'product__name']  # FIFO ordering

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


class SupplierProfile(models.Model):
    """
    Extended supplier profile for onboarding and detailed business information.
    """
    BUSINESS_TYPE_CHOICES = [
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
        ('wholesaler', 'Wholesaler'),
        ('retailer', 'Retailer'),
        ('service_provider', 'Service Provider'),
        ('other', 'Other'),
    ]

    PAYMENT_TERMS_CHOICES = [
        ('net_15', 'Net 15 Days'),
        ('net_30', 'Net 30 Days'),
        ('net_45', 'Net 45 Days'),
        ('net_60', 'Net 60 Days'),
        ('cod', 'Cash on Delivery'),
        ('advance', 'Advance Payment'),
        ('credit_card', 'Credit Card'),
    ]

    supplier = models.OneToOneField(
        Supplier,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # Business Information
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES)
    business_registration_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)

    # Contact Details
    primary_contact_name = models.CharField(max_length=100)
    primary_contact_title = models.CharField(max_length=100, blank=True)
    primary_contact_phone = models.CharField(max_length=20)
    primary_contact_email = models.EmailField()

    # Business Address
    business_address_line1 = models.CharField(max_length=200)
    business_address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    # Business Operations
    product_categories = models.TextField(
        help_text="Comma-separated list of product categories supplied"
    )
    estimated_delivery_timeframe = models.CharField(
        max_length=100,
        help_text="e.g., '3-5 business days', '1-2 weeks'"
    )
    preferred_payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default='net_30'
    )
    minimum_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Minimum order value in USD"
    )

    # Certifications and Compliance
    business_license = models.CharField(max_length=200, blank=True)
    certifications = models.TextField(
        blank=True,
        help_text="List any relevant business certifications"
    )
    insurance_details = models.TextField(blank=True)

    # Banking Information
    bank_name = models.CharField(max_length=200, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    routing_number = models.CharField(max_length=20, blank=True)

    # Profile Status
    is_onboarding_complete = models.BooleanField(default=False)
    onboarding_completed_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['business_name']

    def __str__(self):
        return f"{self.business_name} - {self.supplier.name}"

    def get_product_categories_list(self):
        """Return product categories as a list"""
        if self.product_categories:
            return [cat.strip() for cat in self.product_categories.split(',')]
        return []


class ProductCategory(models.Model):
    """
    Product categories for supplier products.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Product Categories"

    def __str__(self):
        return self.name


class SupplierProduct(models.Model):
    """
    Products offered by suppliers in their catalog.
    """
    AVAILABILITY_CHOICES = [
        ('in_stock', 'In Stock'),
        ('limited_stock', 'Limited Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
        ('pre_order', 'Pre-Order'),
    ]

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='catalog_products'
    )

    # Product Information
    product_name = models.CharField(max_length=200)
    product_code = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100, blank=True)

    # Pricing and Quantities
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ETB')
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    maximum_order_quantity = models.PositiveIntegerField(null=True, blank=True)

    # Product Specifications
    specifications = models.TextField(
        blank=True,
        help_text="Detailed product specifications"
    )
    dimensions = models.CharField(max_length=100, blank=True)
    weight = models.CharField(max_length=50, blank=True)
    color_options = models.CharField(max_length=200, blank=True)
    material = models.CharField(max_length=100, blank=True)

    # Availability and Delivery
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='in_stock'
    )
    estimated_delivery_time = models.CharField(
        max_length=100,
        help_text="e.g., '2-3 business days', '1 week'"
    )
    stock_quantity = models.PositiveIntegerField(null=True, blank=True)

    # Product Images
    product_image = models.ImageField(
        upload_to='supplier_products/',
        blank=True,
        null=True
    )

    # Status and Timestamps
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product_name']
        unique_together = ['supplier', 'product_code']

    def __str__(self):
        return f"{self.product_name} - {self.supplier.name}"

    def is_available(self):
        """Check if product is available for ordering"""
        return self.availability_status in ['in_stock', 'limited_stock', 'pre_order']


class PurchaseRequest(models.Model):
    """
    Purchase requests from Head Managers to suppliers for specific products.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('acknowledged', 'Acknowledged by Supplier'),
        ('quoted', 'Quote Provided'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('converted', 'Converted to Purchase Order'),
        ('cancelled', 'Cancelled'),
    ]

    request_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='purchase_requests'
    )
    requested_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='purchase_requests'
    )

    # Request Details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    required_delivery_date = models.DateField()
    delivery_address = models.TextField()

    # Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    supplier_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    # Financial Information
    estimated_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    quoted_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    sent_date = models.DateTimeField(null=True, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"PR-{self.request_number} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        if not self.request_number:
            # Generate unique request number
            from datetime import datetime
            import uuid
            self.request_number = f"{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


class PurchaseRequestItem(models.Model):
    """
    Individual items in a purchase request.
    """
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items'
    )
    supplier_product = models.ForeignKey(
        SupplierProduct,
        on_delete=models.CASCADE,
        related_name='request_items'
    )

    # Requested Quantities and Specifications
    requested_quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    # Supplier Response
    quoted_unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    quoted_total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    supplier_notes = models.TextField(blank=True)

    # Special Requirements
    special_requirements = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.supplier_product.product_name} x {self.requested_quantity}"

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.unit_price * self.requested_quantity
        if self.quoted_unit_price:
            self.quoted_total_price = self.quoted_unit_price * self.requested_quantity
        super().save(*args, **kwargs)


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
    Enhanced with delivery tracking and confirmation capabilities.
    """
    STATUS_CHOICES = [
        ('initial', 'Initial'),
        ('payment_pending', 'Payment Pending'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('issue_reported', 'Issue Reported'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_purchase_orders'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initial')
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

    # Payment tracking fields
    payment_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Chapa transaction reference")
    payment_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Payment amount in ETB")
    payment_status = models.CharField(max_length=20, default='pending', help_text="Payment status from Chapa")
    payment_initiated_date = models.DateTimeField(blank=True, null=True, help_text="When payment was initiated")
    payment_completed_date = models.DateTimeField(blank=True, null=True, help_text="When payment was completed")
    payment_confirmed_at = models.DateTimeField(blank=True, null=True)

    # Enhanced delivery tracking fields
    shipped_at = models.DateTimeField(blank=True, null=True, help_text="When supplier marked order as shipped")
    estimated_delivery_hours = models.PositiveIntegerField(default=168, help_text="Estimated delivery time in hours (default: 7 days)")
    tracking_number = models.CharField(max_length=100, blank=True, null=True, help_text="Shipping tracking number")
    delivery_address = models.TextField(blank=True, help_text="Delivery address for this order")

    # Delivery confirmation fields
    delivered_at = models.DateTimeField(blank=True, null=True, help_text="When delivery was confirmed by Head Manager")
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_deliveries',
        help_text="Head Manager who confirmed delivery"
    )
    delivery_notes = models.TextField(blank=True, help_text="Notes from delivery confirmation")

    # Issue tracking fields
    has_issues = models.BooleanField(default=False, help_text="Whether delivery has reported issues")
    issue_reported_at = models.DateTimeField(blank=True, null=True, help_text="When issues were first reported")
    issue_reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_order_issues',
        help_text="Head Manager who reported issues"
    )

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"PO-{self.order_number} - {self.supplier.name}"

    def update_payment_status(self, payment_reference, payment_amount=None):
        """Update purchase order when payment is confirmed"""
        self.payment_reference = payment_reference
        if payment_amount:
            self.payment_amount = payment_amount
        self.status = 'payment_confirmed'
        self.payment_status = 'success'
        if not self.payment_confirmed_at:
            from django.utils import timezone
            self.payment_confirmed_at = timezone.now()
            self.payment_completed_date = timezone.now()
        self.save()

    def mark_payment_pending(self, payment_reference):
        """Mark purchase order as payment pending"""
        self.payment_reference = payment_reference
        self.status = 'payment_pending'
        self.payment_status = 'pending'
        if not self.payment_initiated_date:
            from django.utils import timezone
            self.payment_initiated_date = timezone.now()
        self.save()

    def mark_in_transit(self, tracking_number=None):
        """Mark order as in transit (shipped by supplier)"""
        from django.utils import timezone
        self.status = 'in_transit'
        self.shipped_at = timezone.now()
        if tracking_number:
            self.tracking_number = tracking_number
        self.save()

    def confirm_delivery(self, confirmed_by, delivery_notes=None):
        """Confirm successful delivery"""
        from django.utils import timezone
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.actual_delivery_date = timezone.now().date()
        self.confirmed_by = confirmed_by
        if delivery_notes:
            self.delivery_notes = delivery_notes
        self.save()

    def report_issue(self, reported_by, issue_description=None):
        """Report delivery issues"""
        from django.utils import timezone
        self.status = 'issue_reported'
        self.has_issues = True
        self.issue_reported_at = timezone.now()
        self.issue_reported_by = reported_by
        if issue_description:
            self.delivery_notes = f"{self.delivery_notes}\nIssue: {issue_description}" if self.delivery_notes else f"Issue: {issue_description}"
        self.save()

    def cancel_order(self, reason=None):
        """Cancel the purchase order"""
        self.status = 'cancelled'
        if reason:
            self.notes = f"{self.notes}\nCancelled: {reason}" if self.notes else f"Cancelled: {reason}"
        self.save()

    @property
    def is_payment_confirmed(self):
        """Check if payment is confirmed"""
        return self.status == 'payment_confirmed'

    @property
    def is_payment_pending(self):
        """Check if payment is pending"""
        return self.status == 'payment_pending'

    @property
    def can_be_shipped(self):
        """Check if order can be shipped (payment confirmed)"""
        return self.status == 'payment_confirmed'

    @property
    def is_in_transit(self):
        """Check if order is in transit"""
        return self.status == 'in_transit'

    @property
    def is_delivered(self):
        """Check if order is delivered"""
        return self.status == 'delivered'

    @property
    def has_delivery_issues(self):
        """Check if order has delivery issues"""
        return self.status == 'issue_reported' or self.has_issues

    @property
    def estimated_delivery_datetime(self):
        """Calculate estimated delivery datetime"""
        if self.shipped_at and self.estimated_delivery_hours:
            from datetime import timedelta
            return self.shipped_at + timedelta(hours=self.estimated_delivery_hours)
        elif self.payment_confirmed_at and self.estimated_delivery_hours:
            from datetime import timedelta
            return self.payment_confirmed_at + timedelta(hours=self.estimated_delivery_hours)
        return None

    @property
    def delivery_countdown_seconds(self):
        """Get remaining seconds until estimated delivery"""
        estimated_delivery = self.estimated_delivery_datetime
        if estimated_delivery:
            from django.utils import timezone
            remaining = estimated_delivery - timezone.now()
            return max(0, int(remaining.total_seconds()))
        return 0

    @property
    def is_overdue(self):
        """Check if delivery is overdue"""
        return self.delivery_countdown_seconds == 0 and self.status in ['payment_confirmed', 'in_transit']

    @property
    def delivery_status_display(self):
        """Get human-readable delivery status"""
        status_map = {
            'initial': 'Order Created',
            'payment_pending': 'Awaiting Payment',
            'payment_confirmed': 'Payment Confirmed - Preparing Shipment',
            'in_transit': 'In Transit',
            'delivered': 'Delivered Successfully',
            'issue_reported': 'Delivery Issues Reported',
            'cancelled': 'Order Cancelled'
        }
        return status_map.get(self.status, self.status.title())


class PurchaseOrderItem(models.Model):
    """
    Individual items in a purchase order.
    Enhanced with delivery confirmation tracking.
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

    # Delivery confirmation fields
    is_confirmed_received = models.BooleanField(default=False, help_text="Whether this item was confirmed as received")
    has_issues = models.BooleanField(default=False, help_text="Whether this item has delivery issues")
    issue_description = models.TextField(blank=True, help_text="Description of any issues with this item")
    confirmed_at = models.DateTimeField(blank=True, null=True, help_text="When this item was confirmed as received")

    def save(self, *args, **kwargs):
        self.total_price = self.quantity_ordered * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.warehouse_product.product_name} - {self.quantity_ordered} units"

    @property
    def is_fully_received(self):
        """Check if full quantity was received"""
        return self.quantity_received >= self.quantity_ordered

    @property
    def missing_quantity(self):
        """Get quantity of missing items"""
        return max(0, self.quantity_ordered - self.quantity_received)


class DeliveryConfirmation(models.Model):
    """
    Records delivery confirmations for purchase orders.
    """
    purchase_order = models.OneToOneField(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='delivery_confirmation'
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='confirmed_deliveries_detail'
    )
    confirmed_at = models.DateTimeField(auto_now_add=True)

    # Delivery details
    delivery_notes = models.TextField(blank=True, help_text="General notes about the delivery")
    all_items_received = models.BooleanField(default=True, help_text="Whether all items were received as expected")
    delivery_condition = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('damaged', 'Damaged')
        ],
        default='good',
        help_text="Overall condition of delivered items"
    )

    # Photo documentation
    delivery_photos = models.JSONField(
        default=list,
        blank=True,
        help_text="List of photo file paths for delivery documentation"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-confirmed_at']

    def __str__(self):
        return f"Delivery confirmation for {self.purchase_order.order_number} by {self.confirmed_by.get_full_name()}"


class IssueReport(models.Model):
    """
    Records delivery issues and problems reported by Head Managers.
    """
    ISSUE_TYPES = [
        ('missing_items', 'Missing Items'),
        ('damaged_items', 'Damaged Items'),
        ('wrong_items', 'Wrong Items'),
        ('quality_issues', 'Quality Issues'),
        ('packaging_issues', 'Packaging Issues'),
        ('late_delivery', 'Late Delivery'),
        ('other', 'Other'),
    ]

    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='issue_reports'
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reported_delivery_issues'
    )
    reported_at = models.DateTimeField(auto_now_add=True)

    # Issue details
    issue_type = models.CharField(max_length=20, choices=ISSUE_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    title = models.CharField(max_length=200, help_text="Brief description of the issue")
    description = models.TextField(help_text="Detailed description of the issue")

    # Affected items
    affected_items = models.ManyToManyField(
        PurchaseOrderItem,
        blank=True,
        related_name='issue_reports',
        help_text="Specific items affected by this issue"
    )

    # Documentation
    issue_photos = models.JSONField(
        default=list,
        blank=True,
        help_text="List of photo file paths documenting the issue"
    )

    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, help_text="Notes about how the issue was resolved")
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_delivery_issues'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.get_issue_type_display()} - {self.title} ({self.purchase_order.order_number})"


class OrderStatusHistory(models.Model):
    """
    Tracks all status changes for purchase orders for audit trail.
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='order_status_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    # Change details
    reason = models.TextField(blank=True, help_text="Reason for status change")
    notes = models.TextField(blank=True, help_text="Additional notes about the change")

    # System tracking
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Order status histories"

    def __str__(self):
        return f"{self.purchase_order.order_number}: {self.previous_status} → {self.new_status}"


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


# ============================================================================
# STORE MANAGER REQUEST MODELS
# ============================================================================

class RestockRequest(models.Model):
    """
    Handles restock requests from store managers to head manager.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('fulfilled', 'Fulfilled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    request_number = models.CharField(max_length=50, unique=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='restock_requests')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='restock_requests')
    requested_quantity = models.PositiveIntegerField(help_text="Quantity requested for restock")
    current_stock = models.PositiveIntegerField(help_text="Current stock level at time of request")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    reason = models.TextField(help_text="Reason for restock request")

    # Request tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='submitted_restock_requests',
        limit_choices_to={'role': 'store_manager'}
    )
    requested_date = models.DateTimeField(auto_now_add=True)

    # Approval tracking
    reviewed_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_restock_requests',
        limit_choices_to={'role': 'head_manager'}
    )
    reviewed_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, help_text="Notes from head manager review")

    # Fulfillment tracking
    approved_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Quantity approved by head manager")
    fulfilled_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Actual quantity fulfilled")
    fulfilled_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_date']
        indexes = [
            models.Index(fields=['request_number']),
            models.Index(fields=['store', 'status']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['requested_date']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.request_number:
            from datetime import datetime
            import uuid
            self.request_number = f"RR{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Restock Request {self.request_number} - {self.product.name} for {self.store.name}"

    def can_submit_duplicate(self):
        """Check if store can submit another request for same product while this is pending"""
        return not RestockRequest.objects.filter(
            store=self.store,
            product=self.product,
            status='pending'
        ).exclude(pk=self.pk).exists()


class StoreStockTransferRequest(models.Model):
    """
    Handles stock transfer requests between stores via head manager approval.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    request_number = models.CharField(max_length=50, unique=True, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transfer_requests')
    from_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='outgoing_transfer_requests')
    to_store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='incoming_transfer_requests')
    requested_quantity = models.PositiveIntegerField(help_text="Quantity requested for transfer")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    reason = models.TextField(help_text="Reason for stock transfer request")

    # Request tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='submitted_transfer_requests',
        limit_choices_to={'role': 'store_manager'}
    )
    requested_date = models.DateTimeField(auto_now_add=True)

    # Approval tracking
    reviewed_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_transfer_requests',
        limit_choices_to={'role': 'head_manager'}
    )
    reviewed_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, help_text="Notes from head manager review")

    # Transfer tracking
    approved_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Quantity approved for transfer")
    shipped_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    actual_quantity_transferred = models.PositiveIntegerField(null=True, blank=True, help_text="Actual quantity transferred")

    class Meta:
        ordering = ['-requested_date']
        indexes = [
            models.Index(fields=['request_number']),
            models.Index(fields=['from_store', 'status']),
            models.Index(fields=['to_store', 'status']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['requested_date']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.request_number:
            from datetime import datetime
            import uuid
            self.request_number = f"TR{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Transfer Request {self.request_number} - {self.product.name} from {self.from_store.name} to {self.to_store.name}"

    def can_submit_duplicate(self):
        """Check if store can submit another transfer request for same product while this is pending"""
        return not StoreStockTransferRequest.objects.filter(
            from_store=self.from_store,
            to_store=self.to_store,
            product=self.product,
            status='pending'
        ).exclude(pk=self.pk).exists()

    def clean(self):
        """Validate that from_store and to_store are different"""
        from django.core.exceptions import ValidationError
        if self.from_store == self.to_store:
            raise ValidationError("Source and destination stores must be different.")


class RequestNotification(models.Model):
    """
    Handles notifications for request status changes.
    """
    NOTIFICATION_TYPES = [
        ('restock_submitted', 'Restock Request Submitted'),
        ('restock_approved', 'Restock Request Approved'),
        ('restock_rejected', 'Restock Request Rejected'),
        ('restock_fulfilled', 'Restock Request Fulfilled'),
        ('transfer_submitted', 'Transfer Request Submitted'),
        ('transfer_approved', 'Transfer Request Approved'),
        ('transfer_rejected', 'Transfer Request Rejected'),
        ('transfer_completed', 'Transfer Request Completed'),
    ]

    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    recipient = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='request_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)

    # Optional references to related requests
    restock_request = models.ForeignKey(RestockRequest, on_delete=models.CASCADE, null=True, blank=True)
    transfer_request = models.ForeignKey(StoreStockTransferRequest, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_date']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"


# ============================================================================
# REAL-TIME NOTIFICATION SYSTEM MODELS
# ============================================================================

class NotificationCategory(models.Model):
    """
    Categories for organizing notifications in the system.
    """
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='bi-bell')
    color = models.CharField(max_length=20, default='primary')
    priority = models.PositiveIntegerField(default=1, help_text="Lower numbers = higher priority")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['priority', 'display_name']
        verbose_name_plural = "Notification Categories"

    def __str__(self):
        return self.display_name


class SystemNotification(models.Model):
    """
    System-wide notifications for real-time updates.
    """
    NOTIFICATION_TYPES = [
        ('unassigned_store_manager', 'Unassigned Store Manager'),
        ('empty_store', 'Empty Store'),
        ('pending_restock_request', 'Pending Restock Request'),
        ('pending_transfer_request', 'Pending Transfer Request'),
        ('new_supplier_registration', 'New Supplier Registration'),
        ('request_approved', 'Request Approved'),
        ('request_rejected', 'Request Rejected'),
        ('low_stock_alert', 'Low Stock Alert'),
        ('system_announcement', 'System Announcement'),
    ]

    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    category = models.ForeignKey(NotificationCategory, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')

    # Target audience
    target_roles = models.JSONField(default=list, help_text="List of roles that should see this notification")
    target_users = models.ManyToManyField('users.CustomUser', blank=True, related_name='targeted_notifications')

    # Related objects (optional)
    related_user_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID of related user")
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)

    # Action links
    action_url = models.CharField(max_length=500, blank=True, help_text="URL for primary action")
    action_text = models.CharField(max_length=100, blank=True, help_text="Text for action button")

    # Metadata
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When notification should expire")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type']),
            models.Index(fields=['is_active', 'created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title}"

    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False

    def get_target_users(self):
        """Get all users who should see this notification"""
        from users.models import CustomUser

        users = set()

        # Add specifically targeted users
        users.update(self.target_users.all())

        # Add users based on roles
        if self.target_roles:
            role_users = CustomUser.objects.filter(role__in=self.target_roles, is_active=True)
            users.update(role_users)

        return list(users)


class UserNotificationStatus(models.Model):
    """
    Tracks read/unread status of notifications for each user.
    """
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='notification_statuses')
    notification = models.ForeignKey(SystemNotification, on_delete=models.CASCADE, related_name='user_statuses')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'notification']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'is_dismissed']),
            models.Index(fields=['notification', 'is_read']),
        ]

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"{self.user.username} - {self.notification.title} ({status})"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def mark_as_dismissed(self):
        """Mark notification as dismissed"""
        if not self.is_dismissed:
            from django.utils import timezone
            self.is_dismissed = True
            self.dismissed_at = timezone.now()
            self.save()