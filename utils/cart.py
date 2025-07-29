"""
Shopping Cart Utility for Head Manager Product Catalog
Handles session-based cart storage and management
"""

from decimal import Decimal
from django.conf import settings
from Inventory.models import SupplierProduct, Supplier


class Cart:
    """
    Session-based shopping cart for Head Managers
    """
    
    def __init__(self, request):
        """
        Initialize the cart with the current session
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        """
        Add a product to the cart or update its quantity

        Args:
            product: SupplierProduct instance
            quantity: int, quantity to add
            override_quantity: bool, if True, replace quantity instead of adding

        Returns:
            dict: Result with success status and message
        """
        product_id = str(product.id)

        # Check if product is available and has stock
        if not product.is_available():
            return {
                'success': False,
                'message': f'{product.product_name} is not available for ordering.'
            }

        if not product.is_in_stock():
            return {
                'success': False,
                'message': f'{product.product_name} is out of stock.'
            }

        # Calculate new quantity
        current_quantity = 0
        if product_id in self.cart:
            current_quantity = self.cart[product_id]['quantity']

        if override_quantity:
            new_quantity = quantity
        else:
            new_quantity = current_quantity + quantity

        # Ensure minimum order quantity is met
        if new_quantity < product.minimum_order_quantity:
            new_quantity = product.minimum_order_quantity

        # Check if supplier has sufficient stock
        if not product.can_fulfill_quantity(new_quantity):
            return {
                'success': False,
                'message': f'Insufficient stock for {product.product_name}. '
                          f'Available: {product.stock_quantity}, Requested: {new_quantity}'
            }

        # Add or update cart item
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.unit_price),
                'product_name': product.product_name,
                'product_code': product.product_code,
                'supplier_id': product.supplier.id,
                'supplier_name': product.supplier.name,
                'currency': product.currency,
                'minimum_order_quantity': product.minimum_order_quantity,
                'availability_status': product.availability_status,
                'stock_quantity': product.stock_quantity,
            }

        self.cart[product_id]['quantity'] = new_quantity
        self.cart[product_id]['stock_quantity'] = product.stock_quantity  # Update current stock
        self.save()

        return {
            'success': True,
            'message': f'{product.product_name} added to cart successfully.'
        }

    def save(self):
        """
        Mark the session as modified to make sure it gets saved
        """
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def update_quantity(self, product_id, quantity):
        """
        Update the quantity of a specific product

        Returns:
            dict: Result with success status and message
        """
        product_id = str(product_id)
        if product_id not in self.cart:
            return {
                'success': False,
                'message': 'Product not found in cart'
            }

        if quantity <= 0:
            del self.cart[product_id]
            self.save()
            return {
                'success': True,
                'message': 'Product removed from cart'
            }

        # Get the product to check stock and minimum order quantity
        try:
            product = SupplierProduct.objects.get(id=product_id)

            # Check if product is still available
            if not product.is_available():
                del self.cart[product_id]
                self.save()
                return {
                    'success': False,
                    'message': f'{product.product_name} is no longer available and has been removed from cart'
                }

            # Ensure minimum order quantity is met
            if quantity < product.minimum_order_quantity:
                quantity = product.minimum_order_quantity

            # Check if supplier has sufficient stock
            if not product.can_fulfill_quantity(quantity):
                return {
                    'success': False,
                    'message': f'Insufficient stock for {product.product_name}. '
                              f'Available: {product.stock_quantity}, Requested: {quantity}'
                }

            # Update quantity
            self.cart[product_id]['quantity'] = quantity
            self.cart[product_id]['stock_quantity'] = product.stock_quantity
            self.save()

            return {
                'success': True,
                'message': 'Quantity updated successfully'
            }

        except SupplierProduct.DoesNotExist:
            del self.cart[product_id]
            self.save()
            return {
                'success': False,
                'message': 'Product no longer exists and has been removed from cart'
            }

    def get_total_price(self):
        """
        Calculate the total price of all items in the cart
        """
        return sum(Decimal(item['price']) * item['quantity'] 
                  for item in self.cart.values())

    def get_total_items(self):
        """
        Get the total number of items in the cart
        """
        return sum(item['quantity'] for item in self.cart.values())

    def clear(self):
        """
        Remove all items from the cart
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def validate_stock(self):
        """
        Validate that all items in cart have sufficient stock

        Returns:
            dict: Validation result with success status and any issues
        """
        issues = []
        product_ids = list(self.cart.keys())
        products = SupplierProduct.objects.filter(id__in=product_ids)

        for product in products:
            cart_data = self.cart[str(product.id)]
            requested_quantity = cart_data['quantity']

            # Check if product is still available
            if not product.is_available():
                issues.append({
                    'product_name': product.product_name,
                    'issue': 'Product is no longer available',
                    'action': 'remove'
                })
                continue

            # Check if product has sufficient stock
            if not product.can_fulfill_quantity(requested_quantity):
                issues.append({
                    'product_name': product.product_name,
                    'issue': f'Insufficient stock. Available: {product.stock_quantity}, Requested: {requested_quantity}',
                    'action': 'reduce',
                    'max_quantity': product.stock_quantity
                })
                continue

            # Check if stock has changed since added to cart
            if product.stock_quantity != cart_data.get('stock_quantity', 0):
                # Update cart with current stock info
                self.cart[str(product.id)]['stock_quantity'] = product.stock_quantity

        if issues:
            return {
                'success': False,
                'message': 'Some items in your cart have stock issues',
                'issues': issues
            }

        # Update all stock quantities in cart
        self.save()
        return {
            'success': True,
            'message': 'All items in cart are available'
        }

    def remove_unavailable_items(self):
        """
        Remove items from cart that are no longer available or out of stock

        Returns:
            list: List of removed items
        """
        removed_items = []
        product_ids = list(self.cart.keys())
        products = SupplierProduct.objects.filter(id__in=product_ids)

        for product in products:
            if not product.is_available() or not product.is_in_stock():
                removed_items.append({
                    'product_name': product.product_name,
                    'reason': 'Out of stock' if not product.is_in_stock() else 'No longer available'
                })
                del self.cart[str(product.id)]

        self.save()
        return removed_items

    def get_cart_items(self):
        """
        Get all cart items with additional product information
        """
        product_ids = self.cart.keys()
        products = SupplierProduct.objects.filter(id__in=product_ids)
        cart_items = []
        
        for product in products:
            cart_data = self.cart[str(product.id)]
            cart_items.append({
                'product': product,
                'quantity': cart_data['quantity'],
                'price': Decimal(cart_data['price']),
                'total_price': Decimal(cart_data['price']) * cart_data['quantity'],
                'supplier_name': cart_data['supplier_name'],
                'currency': cart_data.get('currency', 'ETB'),
            })
        
        return cart_items

    def get_cart_by_supplier(self):
        """
        Group cart items by supplier for order confirmation
        """
        cart_items = self.get_cart_items()
        suppliers_cart = {}
        
        for item in cart_items:
            supplier_id = item['product'].supplier.id
            supplier_name = item['supplier_name']
            
            if supplier_id not in suppliers_cart:
                suppliers_cart[supplier_id] = {
                    'supplier_name': supplier_name,
                    'supplier_id': supplier_id,
                    'items': [],
                    'total_price': Decimal('0'),
                    'total_items': 0,
                }
            
            suppliers_cart[supplier_id]['items'].append(item)
            suppliers_cart[supplier_id]['total_price'] += item['total_price']
            suppliers_cart[supplier_id]['total_items'] += item['quantity']
        
        return suppliers_cart

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database
        """
        product_ids = self.cart.keys()
        products = SupplierProduct.objects.filter(id__in=product_ids)
        cart = self.cart.copy()
        
        for product in products:
            cart[str(product.id)]['product'] = product
        
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """
        Count all items in the cart
        """
        return sum(item['quantity'] for item in self.cart.values())
