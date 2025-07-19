"""
Webfront Shopping Cart Utility
Handles localStorage-based cart storage and management for webfront customers
"""

from decimal import Decimal
from django.conf import settings
from Inventory.models import Stock, Product
from store.models import Store
from .models import CustomerTicket, CustomerTicketItem
from django.utils import timezone
from django.db import transaction


class WebfrontCart:
    """
    Utility class to handle webfront cart operations
    """
    
    @staticmethod
    def validate_cart_data(cart_data, store_id):
        """
        Validate cart data from localStorage
        
        Args:
            cart_data: Dictionary containing cart items
            store_id: ID of the store
            
        Returns:
            dict: Validation result with success status and errors
        """
        errors = []
        validated_items = []
        total_amount = Decimal('0')
        
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return {
                'success': False,
                'errors': ['Invalid store selected'],
                'items': [],
                'total_amount': 0
            }
        
        if not cart_data or 'items' not in cart_data:
            return {
                'success': False,
                'errors': ['Cart is empty'],
                'items': [],
                'total_amount': 0
            }
        
        for item in cart_data['items']:
            try:
                # Validate required fields
                stock_id = item.get('stock_id')
                product_id = item.get('product_id')
                quantity = int(item.get('quantity', 0))

                if (not stock_id and not product_id) or quantity <= 0:
                    errors.append(f"Invalid item data")
                    continue

                # Get stock for this store - try by stock_id first, then product_id
                if stock_id:
                    try:
                        stock = Stock.objects.select_related('product').get(
                            id=stock_id,
                            store=store
                        )
                    except Stock.DoesNotExist:
                        # Fallback to product_id if stock_id doesn't work
                        stock = Stock.objects.select_related('product').get(
                            product_id=product_id,
                            store=store
                        )
                else:
                    stock = Stock.objects.select_related('product').get(
                        product_id=product_id,
                        store=store
                    )
                
                # Check availability
                if stock.quantity < quantity:
                    errors.append(
                        f"{stock.product.name}: Only {stock.quantity} available, requested {quantity}"
                    )
                    continue
                
                # Calculate item total
                item_total = stock.selling_price * quantity
                total_amount += item_total
                
                validated_items.append({
                    'product_id': stock.product.id,  # Use actual product ID from stock
                    'stock_id': stock.id,  # Include stock ID for reference
                    'product_name': stock.product.name,
                    'quantity': quantity,
                    'unit_price': stock.selling_price,
                    'total_price': item_total,
                    'stock': stock
                })
                
            except Stock.DoesNotExist:
                errors.append(f"Product not available in selected store")
            except (ValueError, KeyError) as e:
                errors.append(f"Invalid item data: {str(e)}")
        
        return {
            'success': len(errors) == 0,
            'errors': errors,
            'items': validated_items,
            'total_amount': total_amount,
            'store': store
        }
    
    @staticmethod
    def check_existing_ticket(phone_number):
        """
        Check if customer has an existing pending ticket
        
        Args:
            phone_number: Customer's phone number
            
        Returns:
            CustomerTicket or None
        """
        return CustomerTicket.objects.filter(
            customer_phone=phone_number,
            status__in=['pending', 'confirmed', 'preparing', 'ready']
        ).first()
    
    @staticmethod
    def create_ticket(cart_data, store_id, phone_number, customer_name='', notes=''):
        """
        Create a customer ticket from cart data
        
        Args:
            cart_data: Validated cart data
            store_id: Store ID
            phone_number: Customer phone number
            customer_name: Optional customer name
            notes: Optional notes
            
        Returns:
            dict: Result with success status and ticket or errors
        """
        # Check for existing ticket
        existing_ticket = WebfrontCart.check_existing_ticket(phone_number)
        if existing_ticket:
            return {
                'success': False,
                'error': f'You already have an active ticket #{existing_ticket.ticket_number}. Please wait for it to be completed.',
                'existing_ticket': existing_ticket
            }
        
        # Validate cart
        validation = WebfrontCart.validate_cart_data(cart_data, store_id)
        if not validation['success']:
            return {
                'success': False,
                'errors': validation['errors']
            }
        
        try:
            with transaction.atomic():
                # Create ticket
                ticket = CustomerTicket.objects.create(
                    store=validation['store'],
                    customer_phone=phone_number,
                    customer_name=customer_name,
                    total_amount=validation['total_amount'],
                    total_items=sum(item['quantity'] for item in validation['items']),
                    notes=notes
                )
                
                # Create ticket items
                for item_data in validation['items']:
                    CustomerTicketItem.objects.create(
                        ticket=ticket,
                        product_id=item_data['product_id'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        total_price=item_data['total_price'],
                        stock=item_data['stock']
                    )
                
                return {
                    'success': True,
                    'ticket': ticket
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create ticket: {str(e)}'
            }
    
    @staticmethod
    def get_ticket_status(ticket_number=None, phone_number=None):
        """
        Get ticket status by ticket number or phone number
        
        Args:
            ticket_number: Ticket number
            phone_number: Customer phone number
            
        Returns:
            CustomerTicket or None
        """
        if ticket_number:
            try:
                return CustomerTicket.objects.get(ticket_number=ticket_number)
            except CustomerTicket.DoesNotExist:
                return None
        
        if phone_number:
            return CustomerTicket.objects.filter(
                customer_phone=phone_number,
                status__in=['pending', 'confirmed', 'preparing', 'ready']
            ).first()
        
        return None
    
    @staticmethod
    def get_store_available_products(store_id):
        """
        Get all available products for a store
        
        Args:
            store_id: Store ID
            
        Returns:
            QuerySet of Stock objects
        """
        return Stock.objects.select_related('product').filter(
            store_id=store_id,
            quantity__gt=0
        ).order_by('product__name')
