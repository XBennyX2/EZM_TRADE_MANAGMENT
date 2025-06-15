from django.db import models

from django.db import models
from store.models import Store 
from transactions.models import Transaction
from django.conf import *

class Category(models.Model):
    """
    Organizes products into categories like 'Cement', 'Steel', etc. 
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    """
    Represents a specific product with its details. 
    """
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    

    def __str__(self):
        return self.name

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