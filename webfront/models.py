from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import datetime


def generate_ticket_number():
    """Generate unique customer ticket number"""
    return f"CT{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"


class CustomerTicket(models.Model):
    """
    Customer order tickets from webfront
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    ticket_number = models.CharField(max_length=50, unique=True, default=generate_ticket_number)
    store = models.ForeignKey('store.Store', on_delete=models.CASCADE, related_name='customer_tickets')
    customer_phone = models.CharField(max_length=20, help_text="Customer's phone number")
    customer_name = models.CharField(max_length=100, blank=True, help_text="Optional customer name")

    # Order details
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_items = models.PositiveIntegerField(default=0)

    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text="Special instructions or notes")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Staff handling
    confirmed_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_tickets'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['customer_phone']),
            models.Index(fields=['store', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.customer_phone}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = generate_ticket_number()
        super().save(*args, **kwargs)


class CustomerTicketItem(models.Model):
    """
    Individual items in a customer ticket
    """
    ticket = models.ForeignKey(CustomerTicket, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Inventory.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    # Stock reference for tracking
    stock = models.ForeignKey('Inventory.Stock', on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.quantity}x {self.product.name} - {self.ticket.ticket_number}"

    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
