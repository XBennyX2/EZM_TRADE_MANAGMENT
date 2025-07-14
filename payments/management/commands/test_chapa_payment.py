from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from payments.chapa_client import ChapaClient
from Inventory.models import Supplier
from decimal import Decimal
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Test Chapa payment integration and identify payment reference issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧪 Testing Chapa Payment Integration'))
        self.stdout.write('=' * 60)

        # Test 1: Basic client initialization
        self.stdout.write('\n📋 Test 1: Client Initialization')
        client = ChapaClient()
        self.stdout.write(f'   ✅ Base URL: {client.base_url}')
        self.stdout.write(f'   ✅ Public Key: {client.public_key[:20]}...')
        self.stdout.write(f'   ✅ Secret Key: {client.secret_key[:20]}...')

        # Test 2: Payment reference generation
        self.stdout.write('\n📋 Test 2: Payment Reference Generation')
        references = []
        for i in range(3):
            ref = client.generate_tx_ref()
            references.append(ref)
            self.stdout.write(f'   ✅ Reference {i+1}: {ref} (length: {len(ref)})')
        
        # Check uniqueness
        if len(set(references)) == len(references):
            self.stdout.write('   ✅ All references are unique')
        else:
            self.stdout.write('   ❌ Duplicate references found!')

        # Test 3: Test payment initialization with minimal data
        self.stdout.write('\n📋 Test 3: Payment Initialization Test')
        
        # Get test user and supplier
        user = User.objects.filter(role='head_manager').first()
        supplier = Supplier.objects.first()
        
        if not user:
            self.stdout.write('   ⚠️  No head manager found for testing')
            return
        
        if not supplier:
            self.stdout.write('   ⚠️  No supplier found for testing')
            return

        self.stdout.write(f'   👤 Test User: {user.username} ({user.email})')
        self.stdout.write(f'   🏢 Test Supplier: {supplier.name}')

        # Test payment initialization
        test_amount = Decimal('100.00')
        test_ref = client.generate_tx_ref()
        
        self.stdout.write(f'   💰 Test Amount: ETB {test_amount}')
        self.stdout.write(f'   🔗 Test Reference: {test_ref}')

        try:
            payment_result = client.initialize_payment(
                amount=test_amount,
                email=user.email,
                first_name=user.first_name or user.username,
                last_name=user.last_name or 'Test',
                phone=getattr(user, 'phone', '+251911000000'),
                tx_ref=test_ref,
                description=f'Test payment to {supplier.name}',
                callback_url='http://localhost:8001/payments/webhook/',
                return_url='http://localhost:8001/payments/success/',
                customization={
                    'title': 'EZM Trade Test',
                    'description': 'Test payment for debugging'
                }
            )
            
            self.stdout.write(f'   📊 Payment Result:')
            self.stdout.write(f'      Success: {payment_result.get("success")}')
            
            if payment_result.get('success'):
                self.stdout.write(f'      ✅ Checkout URL: {payment_result.get("checkout_url")}')
                self.stdout.write(f'      ✅ Transaction Ref: {payment_result.get("tx_ref")}')
                self.stdout.write(f'      ✅ Message: {payment_result.get("message")}')
                
                # Show response data
                data = payment_result.get('data', {})
                if data:
                    self.stdout.write(f'      📋 Response Data:')
                    for key, value in data.items():
                        if key != 'checkout_url':  # Already shown above
                            self.stdout.write(f'         {key}: {value}')
            else:
                self.stdout.write(f'      ❌ Error: {payment_result.get("error")}')
                self.stdout.write(f'      📋 Full Response: {json.dumps(payment_result.get("data", {}), indent=2)}')
                
                # Analyze the error
                error_data = payment_result.get('data', {})
                if 'message' in error_data:
                    self.stdout.write(f'      🔍 Chapa Message: {error_data["message"]}')
                if 'errors' in error_data:
                    self.stdout.write(f'      🔍 Chapa Errors: {error_data["errors"]}')

        except Exception as e:
            self.stdout.write(f'   ❌ Exception during payment initialization: {str(e)}')
            import traceback
            self.stdout.write(f'   📋 Traceback: {traceback.format_exc()}')

        # Test 4: Test different reference formats
        self.stdout.write('\n📋 Test 4: Testing Different Reference Formats')
        
        test_formats = [
            f"EZM-{test_ref[4:]}",  # Current format
            f"EZM_{test_ref[4:]}",  # Underscore instead of dash
            f"EZM{test_ref[4:]}",   # No separator
            test_ref[4:],           # Just the UUID part
            f"TEST-{test_ref[4:]}",  # Different prefix
        ]
        
        for i, ref_format in enumerate(test_formats):
            self.stdout.write(f'   🧪 Format {i+1}: {ref_format} (length: {len(ref_format)})')
            
            try:
                result = client.initialize_payment(
                    amount=Decimal('10.00'),
                    email=user.email,
                    first_name=user.first_name or user.username,
                    last_name=user.last_name or 'Test',
                    tx_ref=ref_format,
                    description='Reference format test'
                )
                
                if result.get('success'):
                    self.stdout.write(f'      ✅ Format {i+1} accepted by Chapa')
                else:
                    error_msg = result.get('error', 'Unknown error')
                    self.stdout.write(f'      ❌ Format {i+1} rejected: {error_msg}')
                    
            except Exception as e:
                self.stdout.write(f'      ❌ Format {i+1} caused exception: {str(e)}')

        # Test 5: Check for common issues
        self.stdout.write('\n📋 Test 5: Common Issues Check')
        
        # Check for special characters
        special_chars_ref = f"EZM-TEST@#$%"
        self.stdout.write(f'   🧪 Testing special characters: {special_chars_ref}')
        
        try:
            result = client.initialize_payment(
                amount=Decimal('10.00'),
                email=user.email,
                first_name=user.first_name or user.username,
                last_name=user.last_name or 'Test',
                tx_ref=special_chars_ref,
                description='Special characters test'
            )
            
            if result.get('success'):
                self.stdout.write(f'      ✅ Special characters accepted')
            else:
                self.stdout.write(f'      ❌ Special characters rejected: {result.get("error")}')
                
        except Exception as e:
            self.stdout.write(f'      ❌ Special characters caused exception: {str(e)}')

        # Check for length limits
        long_ref = f"EZM-{'A' * 50}"
        self.stdout.write(f'   🧪 Testing long reference: {long_ref} (length: {len(long_ref)})')
        
        try:
            result = client.initialize_payment(
                amount=Decimal('10.00'),
                email=user.email,
                first_name=user.first_name or user.username,
                last_name=user.last_name or 'Test',
                tx_ref=long_ref,
                description='Long reference test'
            )
            
            if result.get('success'):
                self.stdout.write(f'      ✅ Long reference accepted')
            else:
                self.stdout.write(f'      ❌ Long reference rejected: {result.get("error")}')
                
        except Exception as e:
            self.stdout.write(f'      ❌ Long reference caused exception: {str(e)}')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎯 Chapa Payment Integration Test Complete'))
        
        self.stdout.write('\n💡 RECOMMENDATIONS:')
        self.stdout.write('   1. Check the test results above for specific error messages')
        self.stdout.write('   2. Verify that Chapa test API keys are valid and active')
        self.stdout.write('   3. Ensure network connectivity to Chapa API endpoints')
        self.stdout.write('   4. Check if payment reference format meets Chapa requirements')
        self.stdout.write('   5. Review Chapa documentation for any recent API changes')
