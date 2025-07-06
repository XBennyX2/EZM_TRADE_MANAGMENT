from django.db import models
from store.models import Store
from transactions.models import Transaction
from django.conf import *

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