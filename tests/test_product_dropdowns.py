"""
Test cases for product dropdown functionality in restock and transfer requests.

This module tests:
1. Restock request product dropdown shows products from warehouse and other stores
2. Transfer request product dropdown shows only products from current store with stock > 0
3. API endpoints return correct product data
4. Form validation works correctly
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import transaction
import json

from store.models import Store, StoreCashier
from Inventory.models import Product, Stock, WarehouseProduct, Supplier, RestockRequest, StoreStockTransferRequest
from users.models import CustomUser

User = get_user_model()


class ProductDropdownTestCase(TestCase):
    """Base test case with common setup for product dropdown tests."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.head_manager = CustomUser.objects.create_user(
            username='head_manager',
            email='head@test.com',
            password='testpass123',
            role='head_manager',
            first_name='Head',
            last_name='Manager'
        )
        
        self.store_manager1 = CustomUser.objects.create_user(
            username='store_manager1',
            email='sm1@test.com',
            password='testpass123',
            role='store_manager',
            first_name='Store',
            last_name='Manager1'
        )
        
        self.store_manager2 = CustomUser.objects.create_user(
            username='store_manager2',
            email='sm2@test.com',
            password='testpass123',
            role='store_manager',
            first_name='Store',
            last_name='Manager2'
        )
        
        # Create stores
        self.store1 = Store.objects.create(
            name='Store 1',
            address='Address 1',
            store_manager=self.store_manager1
        )

        self.store2 = Store.objects.create(
            name='Store 2',
            address='Address 2',
            store_manager=self.store_manager2
        )
        
        # Create supplier
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_person='John Doe',
            email='supplier@test.com',
            phone='1234567890',
            address='123 Supplier St'
        )
        
        # Create products
        self.product1 = Product.objects.create(
            name='Product 1',
            category='Pipes',
            description='Test product 1',
            price=10.00,
            material='Steel'
        )
        
        self.product2 = Product.objects.create(
            name='Product 2',
            category='Electric Wire',
            description='Test product 2',
            price=20.00,
            material='Copper'
        )
        
        self.product3 = Product.objects.create(
            name='Product 3',
            category='Cement',
            description='Test product 3',
            price=30.00,
            material='Concrete'
        )
        
        # Create warehouse products
        self.warehouse_product1 = WarehouseProduct.objects.create(
            product_id='WP001',
            product_name='Product 1',
            category='Pipes',
            quantity_in_stock=100,
            unit_price=8.00,
            minimum_stock_level=10,
            maximum_stock_level=200,
            reorder_point=20,
            sku='SKU001',
            supplier=self.supplier,
            is_active=True
        )
        
        self.warehouse_product2 = WarehouseProduct.objects.create(
            product_id='WP002',
            product_name='Product 2',
            category='Electric Wire',
            quantity_in_stock=50,
            unit_price=18.00,
            minimum_stock_level=5,
            maximum_stock_level=100,
            reorder_point=15,
            sku='SKU002',
            supplier=self.supplier,
            is_active=True
        )
        
        # Create stock in stores
        # Store 1 has Product 1 and Product 2
        self.stock1_1 = Stock.objects.create(
            product=self.product1,
            store=self.store1,
            quantity=5,
            selling_price=12.00
        )
        
        self.stock1_2 = Stock.objects.create(
            product=self.product2,
            store=self.store1,
            quantity=0,  # Out of stock
            selling_price=25.00
        )
        
        # Store 2 has Product 2 and Product 3
        self.stock2_2 = Stock.objects.create(
            product=self.product2,
            store=self.store2,
            quantity=15,
            selling_price=24.00
        )
        
        self.stock2_3 = Stock.objects.create(
            product=self.product3,
            store=self.store2,
            quantity=8,
            selling_price=35.00
        )
        
        self.client = Client()


class RestockProductDropdownTest(ProductDropdownTestCase):
    """Test restock request product dropdown functionality."""
    
    def test_restock_products_api_endpoint(self):
        """Test that restock products API returns products from warehouse and other stores."""
        self.client.login(username='store_manager1', password='testpass123')
        
        response = self.client.get(reverse('get_restock_products'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        products = data['products']
        
        # Should include products from warehouse and other stores
        product_names = [p['name'] for p in products]
        
        # Product 1 and Product 2 should be available (from warehouse)
        self.assertIn('Product 1', product_names)
        self.assertIn('Product 2', product_names)
        
        # Product 2 should also be available from Store 2
        # Product 3 should be available from Store 2
        self.assertIn('Product 3', product_names)
    
    def test_restock_products_api_unauthorized(self):
        """Test that non-store managers cannot access restock products API."""
        # Test without login
        response = self.client.get(reverse('get_restock_products'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test with head manager (should be denied)
        self.client.login(username='head_manager', password='testpass123')
        response = self.client.get(reverse('get_restock_products'))
        self.assertEqual(response.status_code, 403)
    
    def test_restock_form_product_queryset(self):
        """Test that restock form shows correct products."""
        from Inventory.forms import RestockRequestForm
        
        form = RestockRequestForm(store=self.store1)
        available_products = form.fields['product'].queryset
        
        # Should include products from warehouse and other stores
        product_names = [p.name for p in available_products]
        
        # Should include warehouse products and products from other stores
        self.assertIn('Product 1', product_names)  # From warehouse
        self.assertIn('Product 2', product_names)  # From warehouse and Store 2
        self.assertIn('Product 3', product_names)  # From Store 2


class TransferProductDropdownTest(ProductDropdownTestCase):
    """Test transfer request product dropdown functionality."""
    
    def test_transfer_products_api_endpoint(self):
        """Test that transfer products API returns only products from current store with stock > 0."""
        self.client.login(username='store_manager1', password='testpass123')
        
        response = self.client.get(reverse('get_transfer_products'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        products = data['products']
        
        # Should only include products from Store 1 with stock > 0
        self.assertEqual(len(products), 1)  # Only Product 1 has stock > 0 in Store 1
        
        product = products[0]
        self.assertEqual(product['name'], 'Product 1')
        self.assertEqual(product['available_stock'], 5)
    
    def test_transfer_products_api_unauthorized(self):
        """Test that non-store managers cannot access transfer products API."""
        # Test without login
        response = self.client.get(reverse('get_transfer_products'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test with head manager (should be denied)
        self.client.login(username='head_manager', password='testpass123')
        response = self.client.get(reverse('get_transfer_products'))
        self.assertEqual(response.status_code, 403)
    
    def test_transfer_form_product_queryset(self):
        """Test that transfer form shows only products from current store with stock > 0."""
        from Inventory.forms import StoreStockTransferRequestForm
        
        form = StoreStockTransferRequestForm(from_store=self.store1)
        available_products = form.fields['product'].queryset
        
        # Should only include products from Store 1 with stock > 0
        product_names = [p.name for p in available_products]
        
        self.assertIn('Product 1', product_names)  # Has stock in Store 1
        self.assertNotIn('Product 2', product_names)  # No stock in Store 1
        self.assertNotIn('Product 3', product_names)  # Not in Store 1
    
    def test_transfer_form_excludes_current_store_from_destinations(self):
        """Test that transfer form excludes current store from destination options."""
        from Inventory.forms import StoreStockTransferRequestForm
        
        form = StoreStockTransferRequestForm(from_store=self.store1)
        available_stores = form.fields['to_store'].queryset
        
        # Should not include Store 1 (current store)
        store_names = [s.name for s in available_stores]
        
        self.assertNotIn('Store 1', store_names)
        self.assertIn('Store 2', store_names)


class ProductDropdownIntegrationTest(ProductDropdownTestCase):
    """Integration tests for product dropdown functionality."""
    
    def test_restock_request_submission_with_warehouse_product(self):
        """Test submitting restock request for a warehouse product."""
        self.client.login(username='store_manager1', password='testpass123')
        
        # Submit restock request for Product 1 (available in warehouse)
        response = self.client.post(reverse('submit_restock_request'), {
            'product_id': self.product1.id,
            'requested_quantity': 20,
            'priority': 'high',
            'reason': 'Low stock alert'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that restock request was created
        restock_request = RestockRequest.objects.filter(
            store=self.store1,
            product=self.product1
        ).first()
        
        self.assertIsNotNone(restock_request)
        self.assertEqual(restock_request.requested_quantity, 20)
        self.assertEqual(restock_request.priority, 'high')
    
    def test_transfer_request_submission_with_available_product(self):
        """Test submitting transfer request for a product with available stock."""
        self.client.login(username='store_manager1', password='testpass123')
        
        # Submit transfer request for Product 1 (has stock in Store 1)
        response = self.client.post(reverse('submit_transfer_request'), {
            'product_id': self.product1.id,
            'to_store_id': self.store2.id,
            'requested_quantity': 3,
            'priority': 'medium',
            'reason': 'Store 2 needs this product'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that transfer request was created
        transfer_request = StoreStockTransferRequest.objects.filter(
            from_store=self.store1,
            to_store=self.store2,
            product=self.product1
        ).first()
        
        self.assertIsNotNone(transfer_request)
        self.assertEqual(transfer_request.requested_quantity, 3)
        self.assertEqual(transfer_request.priority, 'medium')
    
    def test_edge_case_no_warehouse_products(self):
        """Test behavior when no warehouse products are available."""
        # Deactivate all warehouse products
        WarehouseProduct.objects.update(is_active=False)
        
        self.client.login(username='store_manager1', password='testpass123')
        
        response = self.client.get(reverse('get_restock_products'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        products = data['products']
        
        # Should still include products from other stores
        product_names = [p['name'] for p in products]
        self.assertIn('Product 2', product_names)  # From Store 2
        self.assertIn('Product 3', product_names)  # From Store 2
    
    def test_edge_case_no_stock_in_other_stores(self):
        """Test behavior when no other stores have stock."""
        # Remove all stock from other stores
        Stock.objects.filter(store=self.store2).update(quantity=0)
        
        self.client.login(username='store_manager1', password='testpass123')
        
        response = self.client.get(reverse('get_restock_products'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        products = data['products']
        
        # Should still include warehouse products
        product_names = [p['name'] for p in products]
        self.assertIn('Product 1', product_names)  # From warehouse
        self.assertIn('Product 2', product_names)  # From warehouse
