from django.db import models
from django.conf import settings
from Inventory.models import Product
from store.models import Store

class Transaction(models.Model):
    """
    Logs every inventory movement, such as sales, restocks, or transfers.
    This provides a complete audit trail.
    """
    TRANSACTION_TYPES = [
        ('sale', 'Sale'),
        ('restock', 'Restock'),
        ('transfer', 'Transfer'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(help_text="Quantity of product involved. Can be negative for sales.")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.transaction_type} of {self.quantity} {self.product.name} at {self.store.name}'

class FinancialRecord(models.Model):
    """
    Tracks all revenues and expenses for each store to monitor profitability.
    """
    RECORD_TYPES = [
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='financial_records')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    record_type = models.CharField(max_length=10, choices=RECORD_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f'{self.record_type} of {self.amount} at {self.store.name}'

class Receipt(models.Model):
    """
    Represents a receipt generated for a sales transaction.
    """
    
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, limit_choices_to={'transaction_type': 'sale'})
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Receipt for transaction {self.transaction.id}'

class Order(models.Model):
    """
    Links multiple products and their quantities to a single receipt,
    representing the items in a customer's purchase.
    """
    # This is the key change: we allow this field to be null initially.
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,  # Allows the order to exist without a receipt
        blank=True
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_time_of_sale = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        receipt_id = self.receipt.id if self.receipt else "unassigned"
        return f'{self.quantity} of {self.product.name} for receipt {receipt_id}'