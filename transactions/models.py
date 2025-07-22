from django.db import models
from django.conf import settings
from decimal import Decimal
from django.core.validators import MinValueValidator
import uuid
from datetime import datetime


def generate_supplier_account_number():
    """Generate unique supplier account number"""
    return f"SA{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


def generate_transaction_number():
    """Generate unique supplier transaction number"""
    return f"ST{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


def generate_payment_number():
    """Generate unique supplier payment number"""
    return f"SP{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


def generate_credit_number():
    """Generate unique supplier credit number"""
    return f"SC{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


class Transaction(models.Model):
    """
    Logs every inventory movement, such as sales, restocks, or transfers.
    This provides a complete audit trail.
    """
    TRANSACTION_TYPES = [
        ('sale', 'Sale'),
        ('restock', 'Restock'),
        ('transfer', 'Transfer'),
        ('refund', 'Refund'),
    ]
    PAYMENT_TYPE_CHOICES = [
        ('cash', 'Cash'),
        ('mobile', 'Mobile Banking'),
        ('bank', 'Bank Transfer'),
       
    ]
    # Use strings 'app_name.ModelName' to define relationships to other apps.
    # product = models.ForeignKey('Inventory.Product', on_delete=models.CASCADE) # Remove this line
    quantity = models.IntegerField(help_text="Quantity of product involved. Can be negative for sales.")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    store = models.ForeignKey('store.Store', on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Add this line
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='cash')

    def __str__(self):
        # We use try-except blocks to avoid errors if related objects don't exist yet
        try:
            # product_name = self.product.name # Remove this line
            store_name = self.store.name
            return f'{self.transaction_type} of {self.quantity} at {store_name} via {self.payment_type}' # Update this line
        except (AttributeError,):
            return f'Transaction ID: {self.id}'


class FinancialRecord(models.Model):
    """
    Tracks all revenues and expenses for each store to monitor profitability.
    """
    RECORD_TYPES = [
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]
    store = models.ForeignKey('store.Store', on_delete=models.CASCADE, related_name='financial_records')
    cashier = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='financial_records')
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
    # This relationship is fine as-is because Transaction is defined in the same file.
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, limit_choices_to={'transaction_type': 'sale'})
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Customer information
    customer_name = models.CharField(max_length=100, default='Walk-in Customer', blank=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)

    # Price breakdown
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'Receipt for transaction {self.transaction.id}'

class Order(models.Model):
    """
    Links multiple products and their quantities to a single receipt,
    representing the items in a customer's purchase.
    """
    # This relationship is also fine as Receipt is defined above in the same file.
    # We allow it to be null to handle the workflow where orders are created before the receipt.
    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,
        blank=True
    )
    # This must be a string to avoid the circular import with the 'inventory' app.
    product = models.ForeignKey('Inventory.Product', on_delete=models.CASCADE, related_name='transaction_orders', null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price_at_time_of_sale = models.DecimalField(max_digits=10, decimal_places=2)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)

    def __str__(self):
        receipt_id = self.receipt.id if self.receipt else "unassigned"
        product_name = self.product.name if self.product else "Unknown Product"
        return f'{self.quantity} of {product_name} for receipt {receipt_id}'


# ============================================================================
# SUPPLIER TRANSACTION MODELS
# ============================================================================

class SupplierAccount(models.Model):
    """
    Maintains supplier account balances and payment terms.
    """
    PAYMENT_TERMS_CHOICES = [
        ('net_30', 'Net 30 Days'),
        ('net_60', 'Net 60 Days'),
        ('net_90', 'Net 90 Days'),
        ('immediate', 'Immediate Payment'),
        ('cod', 'Cash on Delivery'),
        ('advance', 'Advance Payment'),
    ]

    supplier = models.OneToOneField(
        'Inventory.Supplier',
        on_delete=models.CASCADE,
        related_name='account'
    )
    account_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique account number for the supplier"
    )
    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current outstanding balance (positive = we owe supplier)"
    )
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Maximum credit limit allowed for this supplier"
    )
    payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default='net_30'
    )
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['supplier__name']
        indexes = [
            models.Index(fields=['account_number']),
            models.Index(fields=['supplier']),
            models.Index(fields=['current_balance']),
        ]

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = generate_supplier_account_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Account {self.account_number} - {self.supplier.name}"


class SupplierTransaction(models.Model):
    """
    Track all financial transactions between the company and suppliers.
    """
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('payment', 'Payment'),
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('adjustment', 'Adjustment'),
        ('refund', 'Refund'),
    ]

    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    transaction_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique transaction reference number"
    )
    supplier_account = models.ForeignKey(
        SupplierAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    description = models.TextField(help_text="Description of the transaction")
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="External reference number (PO, invoice, etc.)"
    )
    purchase_order = models.ForeignKey(
        'Inventory.PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplier_transactions'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_supplier_transactions'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_supplier_transactions'
    )
    transaction_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_number']),
            models.Index(fields=['supplier_account']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = generate_transaction_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_number} - {self.transaction_type} - ${self.amount}"


class SupplierPayment(models.Model):
    """
    Record payments made to suppliers for purchase orders.
    """
    PAYMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('wire_transfer', 'Wire Transfer'),
        ('mobile_payment', 'Mobile Payment'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    payment_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique payment reference number"
    )
    supplier_transaction = models.OneToOneField(
        SupplierTransaction,
        on_delete=models.CASCADE,
        related_name='payment',
        limit_choices_to={'transaction_type': 'payment'}
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(help_text="Payment due date")
    bank_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bank transaction reference"
    )
    check_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Check number if payment by check"
    )
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='processed_supplier_payments'
    )

    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['payment_number']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = generate_payment_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment {self.payment_number} - ${self.amount_paid}"


class SupplierCredit(models.Model):
    """
    Handle supplier credits, refunds, and adjustments.
    """
    CREDIT_TYPES = [
        ('refund', 'Refund'),
        ('return', 'Return Credit'),
        ('discount', 'Discount'),
        ('adjustment', 'Adjustment'),
        ('overpayment', 'Overpayment Credit'),
        ('promotional', 'Promotional Credit'),
    ]

    CREDIT_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('applied', 'Applied'),
        ('rejected', 'Rejected'),
    ]

    credit_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique credit reference number"
    )
    supplier_transaction = models.OneToOneField(
        SupplierTransaction,
        on_delete=models.CASCADE,
        related_name='credit',
        limit_choices_to={'transaction_type': 'credit'}
    )
    credit_type = models.CharField(max_length=20, choices=CREDIT_TYPES)
    credit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    reason = models.TextField(help_text="Reason for the credit")
    original_invoice = models.CharField(
        max_length=100,
        blank=True,
        help_text="Original invoice number if applicable"
    )
    status = models.CharField(max_length=20, choices=CREDIT_STATUS, default='pending')
    credit_date = models.DateTimeField(auto_now_add=True)
    applied_date = models.DateTimeField(null=True, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='requested_supplier_credits'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_supplier_credits'
    )

    class Meta:
        ordering = ['-credit_date']
        indexes = [
            models.Index(fields=['credit_number']),
            models.Index(fields=['credit_date']),
            models.Index(fields=['status']),
            models.Index(fields=['credit_type']),
        ]

    def save(self, *args, **kwargs):
        if not self.credit_number:
            self.credit_number = generate_credit_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Credit {self.credit_number} - {self.credit_type} - ${self.credit_amount}"


class SupplierInvoice(models.Model):
    """
    Store supplier invoices and billing information.
    """
    INVOICE_STATUS = [
        ('received', 'Received'),
        ('verified', 'Verified'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="Supplier's invoice number"
    )
    supplier_transaction = models.OneToOneField(
        SupplierTransaction,
        on_delete=models.CASCADE,
        related_name='invoice',
        limit_choices_to={'transaction_type': 'purchase'}
    )
    purchase_order = models.ForeignKey(
        'Inventory.PurchaseOrder',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    invoice_date = models.DateField(help_text="Date on the supplier's invoice")
    due_date = models.DateField(help_text="Payment due date")
    received_date = models.DateTimeField(auto_now_add=True)

    # Invoice amounts
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='received')
    notes = models.TextField(blank=True)

    # Verification and approval tracking
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_supplier_invoices'
    )
    verified_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_supplier_invoices'
    )
    approved_date = models.DateTimeField(null=True, blank=True)

    # File attachment for invoice document
    invoice_document = models.FileField(
        upload_to='supplier_invoices/',
        blank=True,
        null=True,
        help_text="Upload the supplier's invoice document"
    )

    class Meta:
        ordering = ['-received_date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['invoice_date']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
            models.Index(fields=['received_date']),
        ]

    def save(self, *args, **kwargs):
        """Calculate total amount automatically"""
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.purchase_order.supplier.name} - ${self.total_amount}"