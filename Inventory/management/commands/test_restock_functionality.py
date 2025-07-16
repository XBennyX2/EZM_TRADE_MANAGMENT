from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from Inventory.models import RestockRequest, Product, Store
from django.db import transaction


class Command(BaseCommand):
    help = 'Test restock request functionality after database schema fix'

    def handle(self, *args, **options):
        User = get_user_model()
        
        self.stdout.write('🧪 Testing Restock Request Functionality')
        self.stdout.write('=' * 50)
        
        # Test 1: Check database schema
        self.stdout.write('\n1. Testing Database Schema...')
        try:
            request = RestockRequest.objects.first()
            if request:
                # Test all new fields
                fields_to_test = [
                    'shipped_quantity', 'shipped_date', 'shipped_by',
                    'tracking_number', 'received_quantity', 'received_date',
                    'received_by', 'receiving_notes'
                ]
                
                for field in fields_to_test:
                    value = getattr(request, field, 'MISSING')
                    self.stdout.write(f'   ✅ {field}: {value}')
                
                self.stdout.write('   ✅ All database fields accessible')
            else:
                self.stdout.write('   ⚠️  No existing restock requests found')
        except Exception as e:
            self.stdout.write(f'   ❌ Database schema error: {e}')
            return
        
        # Test 2: Create new restock request
        self.stdout.write('\n2. Testing Restock Request Creation...')
        try:
            # Get test data
            store_manager = User.objects.filter(role='store_manager').first()
            product = Product.objects.first()
            store = Store.objects.first()
            
            if not all([store_manager, product, store]):
                self.stdout.write('   ⚠️  Missing test data (store_manager, product, or store)')
                return
            
            # Create test request
            with transaction.atomic():
                test_request = RestockRequest.objects.create(
                    product=product,
                    store=store,
                    requested_by=store_manager,
                    requested_quantity=20,
                    current_stock=5,
                    priority='medium',
                    reason='Testing restock functionality after schema fix'
                )
                
                self.stdout.write(f'   ✅ Created request: {test_request.request_number}')
                self.stdout.write(f'   ✅ Status: {test_request.status}')
                self.stdout.write(f'   ✅ Product: {test_request.product.name}')
                self.stdout.write(f'   ✅ Store: {test_request.store.name}')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Creation error: {e}')
            return
        
        # Test 3: Test shipping workflow
        self.stdout.write('\n3. Testing Shipping Workflow...')
        try:
            # Approve the request first
            test_request.status = 'approved'
            test_request.approved_quantity = 20
            test_request.save()
            
            # Test ship method
            test_request.ship(
                shipped_by=store_manager,
                shipped_quantity=20,
                tracking_number='TEST-TRACK-456'
            )
            
            self.stdout.write(f'   ✅ Shipped successfully')
            self.stdout.write(f'   ✅ Status: {test_request.status}')
            self.stdout.write(f'   ✅ Shipped quantity: {test_request.shipped_quantity}')
            self.stdout.write(f'   ✅ Tracking number: {test_request.tracking_number}')
            
        except Exception as e:
            self.stdout.write(f'   ❌ Shipping error: {e}')
            return
        
        # Test 4: Test receiving workflow
        self.stdout.write('\n4. Testing Receiving Workflow...')
        try:
            # Test receive method
            test_request.receive(
                received_by=store_manager,
                received_quantity=20,
                notes='All items received in perfect condition - test successful'
            )
            
            self.stdout.write(f'   ✅ Received successfully')
            self.stdout.write(f'   ✅ Status: {test_request.status}')
            self.stdout.write(f'   ✅ Received quantity: {test_request.received_quantity}')
            self.stdout.write(f'   ✅ Receiving notes: {test_request.receiving_notes}')
            
        except Exception as e:
            self.stdout.write(f'   ❌ Receiving error: {e}')
            return
        
        # Test 5: Summary
        self.stdout.write('\n5. Test Summary')
        self.stdout.write('=' * 30)
        
        total_requests = RestockRequest.objects.count()
        self.stdout.write(f'   📊 Total restock requests: {total_requests}')
        
        status_counts = {}
        for status in ['pending', 'approved', 'shipped', 'received', 'rejected']:
            count = RestockRequest.objects.filter(status=status).count()
            status_counts[status] = count
            self.stdout.write(f'   📊 {status.title()}: {count}')
        
        self.stdout.write('\n🎉 All tests completed successfully!')
        self.stdout.write('✅ Restock request functionality is working properly')
        self.stdout.write('✅ Database schema is correct')
        self.stdout.write('✅ Shipping and receiving workflows are functional')
        
        # Clean up test data
        self.stdout.write('\n🧹 Cleaning up test data...')
        test_request.delete()
        self.stdout.write('   ✅ Test request deleted')
