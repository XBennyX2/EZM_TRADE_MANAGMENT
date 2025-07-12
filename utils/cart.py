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
        """
        product_id = str(product.id)
        
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
            }
        
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
            
        # Ensure minimum order quantity is met
        if self.cart[product_id]['quantity'] < product.minimum_order_quantity:
            self.cart[product_id]['quantity'] = product.minimum_order_quantity
            
        self.save()

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
        """
        product_id = str(product_id)
        if product_id in self.cart:
            if quantity <= 0:
                del self.cart[product_id]
            else:
                # Get the product to check minimum order quantity
                try:
                    product = SupplierProduct.objects.get(id=product_id)
                    if quantity < product.minimum_order_quantity:
                        quantity = product.minimum_order_quantity
                except SupplierProduct.DoesNotExist:
                    pass
                    
                self.cart[product_id]['quantity'] = quantity
            self.save()

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
