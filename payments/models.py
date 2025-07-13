from django.db import models
from django.contrib.auth import get_user_model
from Inventory.models import Supplier
import uuid

User = get_user_model()


class ChapaTransaction(models.Model):
    """
    Model to track Chapa payment transactions
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Transaction identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapa_tx_ref = models.CharField(max_length=100, unique=True, help_text="Chapa transaction reference")
    chapa_checkout_url = models.URLField(blank=True, null=True, help_text="Chapa checkout URL")
    
    # Payment details
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount in ETB")
    currency = models.CharField(max_length=3, default='ETB')
    description = models.TextField(help_text="Payment description")
    
    # User and supplier information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chapa_transactions')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='chapa_transactions')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Chapa response data
    chapa_response = models.JSONField(blank=True, null=True, help_text="Full Chapa API response")
    webhook_data = models.JSONField(blank=True, null=True, help_text="Webhook notification data")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    # Additional metadata
    customer_email = models.EmailField()
    customer_first_name = models.CharField(max_length=100)
    customer_last_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chapa_tx_ref']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['supplier', 'status']),
        ]
    
    def __str__(self):
        return f"Transaction {self.chapa_tx_ref} - {self.amount} ETB - {self.status}"
    
    @property
    def is_successful(self):
        return self.status == 'success'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_failed(self):
        return self.status in ['failed', 'cancelled']


class PurchaseOrderPayment(models.Model):
    """
    Model to link purchase orders with Chapa transactions
    """
    PAYMENT_STATUS_CHOICES = [
        ('initial', 'Initial'),
        ('payment_pending', 'Payment Pending'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    chapa_transaction = models.OneToOneField(
        ChapaTransaction, 
        on_delete=models.CASCADE, 
        related_name='purchase_order_payment'
    )
    
    # Purchase order details
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purchase_order = models.OneToOneField(
        'Inventory.PurchaseOrder',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='payment_info'
    )
    
    # Order status
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='initial')
    
    # Order items (JSON field to store cart items for this supplier)
    order_items = models.JSONField(help_text="Cart items for this supplier")
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_confirmed_at = models.DateTimeField(blank=True, null=True)
    
    # Additional metadata
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['supplier', 'status']),
        ]
    
    def __str__(self):
        return f"Order Payment {self.id} - {self.supplier.name} - {self.status}"
    
    def update_status_from_payment(self):
        """Update order status based on payment transaction status"""
        if self.chapa_transaction.is_successful:
            self.status = 'payment_confirmed'
            if not self.payment_confirmed_at:
                from django.utils import timezone
                self.payment_confirmed_at = timezone.now()

            # Create purchase order if it doesn't exist
            if not self.purchase_order:
                self.create_purchase_order()

            # Update linked purchase order if exists
            if self.purchase_order:
                self.purchase_order.update_payment_status(
                    payment_reference=self.chapa_transaction.chapa_tx_ref,
                    payment_amount=self.chapa_transaction.amount
                )

        elif self.chapa_transaction.is_failed:
            self.status = 'cancelled'

            # Cancel linked purchase order if exists
            if self.purchase_order:
                self.purchase_order.cancel_order("Payment failed")

        self.save()

    def create_purchase_order(self):
        """Create a purchase order from the payment information"""
        from Inventory.models import PurchaseOrder, PurchaseOrderItem, SupplierProduct
        from django.utils import timezone
        from datetime import timedelta
        import uuid

        try:
            # Generate unique order number
            order_number = f"PO-{uuid.uuid4().hex[:8].upper()}"

            # Calculate expected delivery date (7 days from now)
            expected_delivery = timezone.now().date() + timedelta(days=7)

            # Create purchase order
            purchase_order = PurchaseOrder.objects.create(
                order_number=order_number,
                supplier=self.supplier,
                created_by=self.user,
                status='payment_confirmed',
                expected_delivery_date=expected_delivery,
                total_amount=self.total_amount,
                payment_reference=self.chapa_transaction.chapa_tx_ref,
                payment_amount=self.chapa_transaction.amount,
                payment_status='success',
                payment_initiated_date=self.chapa_transaction.created_at,
                payment_completed_date=self.chapa_transaction.paid_at,
                payment_confirmed_at=self.payment_confirmed_at,
                notes=f"Auto-generated from payment {self.chapa_transaction.chapa_tx_ref}"
            )

            # Create purchase order items from cart items
            for item_data in self.order_items:
                try:
                    # Get the supplier product
                    supplier_product = SupplierProduct.objects.get(
                        id=item_data.get('product_id'),
                        supplier=self.supplier
                    )

                    # Create purchase order item
                    PurchaseOrderItem.objects.create(
                        purchase_order=purchase_order,
                        warehouse_product=supplier_product,  # This might need adjustment based on your model structure
                        quantity_ordered=item_data.get('quantity', 1),
                        unit_price=item_data.get('price', 0),
                        total_price=item_data.get('total_price', 0)
                    )

                except SupplierProduct.DoesNotExist:
                    # Log error but continue with other items
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"SupplierProduct {item_data.get('product_id')} not found for purchase order {order_number}")
                    continue

            # Link the purchase order to this payment
            self.purchase_order = purchase_order
            self.save()

            # Send supplier notification
            try:
                from .notification_service import supplier_notification_service
                supplier_notification_service.send_purchase_order_notification(purchase_order)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send purchase order notification: {str(e)}")

            return purchase_order

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create purchase order for payment {self.chapa_transaction.chapa_tx_ref}: {str(e)}")
            return None


class PaymentWebhookLog(models.Model):
    """
    Model to log all webhook notifications from Chapa
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Webhook data
    webhook_data = models.JSONField(help_text="Raw webhook payload")
    signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Processing status
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, null=True)
    
    # Related transaction (if found)
    transaction = models.ForeignKey(
        ChapaTransaction, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='webhook_logs'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['processed']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Webhook {self.id} - {'Processed' if self.processed else 'Pending'}"
