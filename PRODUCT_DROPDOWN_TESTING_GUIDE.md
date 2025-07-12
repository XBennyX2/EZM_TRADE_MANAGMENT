# Product Dropdown Testing Guide

This guide provides step-by-step instructions for manually testing the product dropdown functionality in restock and transfer requests.

## Prerequisites

1. Django server is running
2. Database has been migrated
3. Test data is available (users, stores, products, stock)

## Test Setup

### 1. Create Test Data

Run the following in Django shell (`python manage.py shell`):

```python
from django.contrib.auth import get_user_model
from store.models import Store
from Inventory.models import Product, Stock, WarehouseProduct, Supplier
from users.models import CustomUser

User = get_user_model()

# Create users
head_manager = CustomUser.objects.create_user(
    username='head_manager_test',
    email='head@test.com',
    password='testpass123',
    role='head_manager',
    first_name='Head',
    last_name='Manager'
)

store_manager1 = CustomUser.objects.create_user(
    username='store_manager1_test',
    email='sm1@test.com',
    password='testpass123',
    role='store_manager',
    first_name='Store',
    last_name='Manager1'
)

store_manager2 = CustomUser.objects.create_user(
    username='store_manager2_test',
    email='sm2@test.com',
    password='testpass123',
    role='store_manager',
    first_name='Store',
    last_name='Manager2'
)

# Create stores
store1 = Store.objects.create(
    name='Test Store 1',
    address='Address 1',
    store_manager=store_manager1
)

store2 = Store.objects.create(
    name='Test Store 2',
    address='Address 2',
    store_manager=store_manager2
)

# Create supplier
supplier = Supplier.objects.create(
    name='Test Supplier',
    contact_person='John Doe',
    email='supplier@test.com',
    phone='1234567890',
    address='123 Supplier St'
)

# Create products
product1 = Product.objects.create(
    name='Test Pipe',
    category='Pipes',
    description='Test pipe product',
    price=10.00,
    material='Steel'
)

product2 = Product.objects.create(
    name='Test Wire',
    category='Electric Wire',
    description='Test wire product',
    price=20.00,
    material='Copper'
)

product3 = Product.objects.create(
    name='Test Cement',
    category='Cement',
    description='Test cement product',
    price=30.00,
    material='Concrete'
)

# Create warehouse products
WarehouseProduct.objects.create(
    product_id='WP001',
    product_name='Test Pipe',
    category='Pipes',
    quantity_in_stock=100,
    unit_price=8.00,
    minimum_stock_level=10,
    maximum_stock_level=200,
    reorder_point=20,
    sku='SKU001',
    supplier=supplier,
    is_active=True
)

WarehouseProduct.objects.create(
    product_id='WP002',
    product_name='Test Wire',
    category='Electric Wire',
    quantity_in_stock=50,
    unit_price=18.00,
    minimum_stock_level=5,
    maximum_stock_level=100,
    reorder_point=15,
    sku='SKU002',
    supplier=supplier,
    is_active=True
)

# Create stock in stores
# Store 1 has Test Pipe (low stock) and Test Wire (out of stock)
Stock.objects.create(
    product=product1,
    store=store1,
    quantity=2,  # Low stock
    selling_price=12.00
)

Stock.objects.create(
    product=product2,
    store=store1,
    quantity=0,  # Out of stock
    selling_price=25.00
)

# Store 2 has Test Wire and Test Cement
Stock.objects.create(
    product=product2,
    store=store2,
    quantity=15,
    selling_price=24.00
)

Stock.objects.create(
    product=product3,
    store=store2,
    quantity=8,
    selling_price=35.00
)

print("Test data created successfully!")
```

## Manual Testing Scenarios

### Test 1: Restock Request Product Dropdown

**Objective**: Verify that restock request dropdown shows products from warehouse and other stores.

**Steps**:
1. Login as `store_manager1_test` (password: `testpass123`)
2. Navigate to Store Manager dashboard
3. Go to "Stock Management" section
4. Click "Request Restock" button
5. Check the product dropdown

**Expected Results**:
- Dropdown should show:
  - "Test Pipe" (available in warehouse)
  - "Test Wire" (available in warehouse and Store 2)
  - "Test Cement" (available in Store 2)
- Should NOT show products that are only in current store without warehouse availability

### Test 2: Transfer Request Product Dropdown

**Objective**: Verify that transfer request dropdown shows only products from current store with stock > 0.

**Steps**:
1. Login as `store_manager1_test` (password: `testpass123`)
2. Navigate to Store Manager dashboard
3. Go to "Transfer Requests" section
4. Click "Request Transfer" button
5. Check the product dropdown

**Expected Results**:
- Dropdown should show:
  - "Test Pipe" (has stock in Store 1: 2 units)
- Should NOT show:
  - "Test Wire" (0 stock in Store 1)
  - "Test Cement" (not in Store 1)

### Test 3: API Endpoint Testing

**Objective**: Test API endpoints return correct data.

**Steps**:
1. Login as `store_manager1_test`
2. Open browser developer tools
3. Navigate to: `/users/api/restock-products/`
4. Check JSON response
5. Navigate to: `/users/api/transfer-products/`
6. Check JSON response

**Expected Results**:

Restock products API response should include:
```json
{
  "products": [
    {"id": 1, "name": "Test Pipe", "category": "Pipes", "price": "10.00"},
    {"id": 2, "name": "Test Wire", "category": "Electric Wire", "price": "20.00"},
    {"id": 3, "name": "Test Cement", "category": "Cement", "price": "30.00"}
  ]
}
```

Transfer products API response should include:
```json
{
  "products": [
    {
      "id": 1, 
      "name": "Test Pipe", 
      "category": "Pipes", 
      "price": "10.00",
      "available_stock": 2
    }
  ]
}
```

### Test 4: Cross-Store Verification

**Objective**: Verify different stores see different products for transfer.

**Steps**:
1. Login as `store_manager2_test` (password: `testpass123`)
2. Navigate to "Transfer Requests" section
3. Check product dropdown

**Expected Results**:
- Dropdown should show:
  - "Test Wire" (15 units in Store 2)
  - "Test Cement" (8 units in Store 2)
- Should NOT show "Test Pipe" (not in Store 2)

### Test 5: Form Submission Testing

**Objective**: Test actual form submission works correctly.

**Steps**:
1. Login as `store_manager1_test`
2. Submit restock request for "Test Wire" (available in warehouse)
3. Submit transfer request for "Test Pipe" to Store 2
4. Check that requests were created successfully

**Expected Results**:
- Both requests should be created successfully
- Success messages should be displayed
- Requests should appear in respective request lists

## Edge Case Testing

### Test 6: No Warehouse Products

**Steps**:
1. In Django admin, deactivate all warehouse products
2. Test restock dropdown
3. Should only show products from other stores

### Test 7: No Stock in Other Stores

**Steps**:
1. Set all stock quantities in other stores to 0
2. Test restock dropdown
3. Should only show warehouse products

### Test 8: Unauthorized Access

**Steps**:
1. Try accessing API endpoints without login
2. Try accessing with different user roles
3. Should get appropriate error responses

## Automated Test Execution

Run the automated test suite:

```bash
python run_product_dropdown_tests.py
```

This will execute all test cases and provide a comprehensive report.

## Troubleshooting

### Common Issues:

1. **Empty dropdowns**: Check that test data was created correctly
2. **API 403 errors**: Ensure user has correct role and is logged in
3. **Missing products**: Verify warehouse products are active and have stock > 0
4. **Form submission errors**: Check that all required fields are filled

### Debug Steps:

1. Check Django logs for errors
2. Verify database has correct data
3. Test API endpoints directly in browser
4. Use Django shell to query models directly

## Success Criteria

All tests pass when:
- ✅ Restock dropdown shows warehouse + other store products
- ✅ Transfer dropdown shows only current store products with stock > 0
- ✅ API endpoints return correct JSON data
- ✅ Forms submit successfully
- ✅ Unauthorized access is properly blocked
- ✅ Edge cases are handled gracefully
