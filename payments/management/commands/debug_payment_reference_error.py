from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from payments.chapa_client import ChapaClient
from payments.services import ChapaPaymentService
from payments.models import ChapaTransaction
from Inventory.models import Supplier
from decimal import Decimal
import requests
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Debug the "Invalid payment reference" error with comprehensive testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 DEBUGGING: Invalid Payment Reference Error'))
        self.stdout.write('=' * 70)

        # Test 1: Check Chapa API connectivity and credentials
        self.stdout.write('\n📋 Test 1: Chapa API Connectivity & Credentials')
        self.test_chapa_connectivity()

        # Test 2: Test reference generation patterns
        self.stdout.write('\n📋 Test 2: Reference Generation Patterns')
        self.test_reference_patterns()

        # Test 3: Test actual payment initialization with detailed error analysis
        self.stdout.write('\n📋 Test 3: Payment Initialization with Error Analysis')
        self.test_payment_initialization()

        # Test 4: Test different reference formats
        self.stdout.write('\n📋 Test 4: Different Reference Formats')
        self.test_reference_formats()

        # Test 5: Check for existing references in database
        self.stdout.write('\n📋 Test 5: Database Reference Check')
        self.test_database_references()

        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('🎯 Debug Analysis Complete'))
        self.provide_solution()

    def test_chapa_connectivity(self):
        """Test basic Chapa API connectivity"""
        client = ChapaClient()
        
        self.stdout.write(f'   🔑 Public Key: {client.public_key}')
        self.stdout.write(f'   🔑 Secret Key: {client.secret_key[:20]}...')
        self.stdout.write(f'   🌐 Base URL: {client.base_url}')
        
        # Test basic API connectivity
        try:
            headers = client._get_headers()
            response = requests.get(
                f"{client.base_url}/banks",  # Simple endpoint to test connectivity
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.stdout.write('   ✅ Chapa API connectivity: SUCCESS')
                self.stdout.write(f'   📊 Response status: {response.status_code}')
            else:
                self.stdout.write(f'   ❌ Chapa API connectivity: FAILED ({response.status_code})')
                self.stdout.write(f'   📋 Response: {response.text[:200]}...')
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(f'   ❌ Network error: {str(e)}')
        except Exception as e:
            self.stdout.write(f'   ❌ Unexpected error: {str(e)}')

    def test_reference_patterns(self):
        """Test different reference generation patterns"""
        client = ChapaClient()
        
        # Generate multiple references and analyze patterns
        references = []
        for i in range(10):
            ref = client.generate_tx_ref()
            references.append(ref)
            if i < 5:  # Show first 5
                self.stdout.write(f'   📝 Reference {i+1}: {ref}')
        
        # Analyze patterns
        lengths = [len(ref) for ref in references]
        unique_lengths = set(lengths)
        
        self.stdout.write(f'   📊 Generated {len(references)} references')
        self.stdout.write(f'   📏 Length range: {min(lengths)} - {max(lengths)} characters')
        self.stdout.write(f'   🔄 Unique lengths: {unique_lengths}')
        
        # Check for duplicates
        unique_refs = set(references)
        if len(unique_refs) == len(references):
            self.stdout.write('   ✅ All references are unique')
        else:
            duplicates = len(references) - len(unique_refs)
            self.stdout.write(f'   ❌ Found {duplicates} duplicate references')
        
        # Check format consistency
        valid_format = all(ref.startswith('EZM-') for ref in references)
        if valid_format:
            self.stdout.write('   ✅ All references follow EZM- format')
        else:
            self.stdout.write('   ❌ Some references have invalid format')

    def test_payment_initialization(self):
        """Test actual payment initialization with detailed error analysis"""
        client = ChapaClient()
        user = User.objects.filter(role='head_manager').first()
        
        if not user:
            self.stdout.write('   ⚠️  No head manager found')
            return
        
        # Test with a fresh reference
        tx_ref = client.generate_tx_ref()
        self.stdout.write(f'   🆔 Testing with reference: {tx_ref}')
        
        try:
            result = client.initialize_payment(
                amount=Decimal('100.00'),
                email=user.email,
                first_name=user.first_name or user.username,
                last_name=user.last_name or 'Test',
                tx_ref=tx_ref,
                description='Debug test payment',
                customization={
                    'title': 'EZM Debug',
                    'description': 'Debug test'
                }
            )
            
            if result.get('success'):
                self.stdout.write('   ✅ Payment initialization: SUCCESS')
                self.stdout.write(f'   🔗 Checkout URL: {result.get("checkout_url", "")[:50]}...')
                self.stdout.write(f'   📋 Message: {result.get("message")}')
            else:
                error = result.get('error', 'Unknown error')
                self.stdout.write(f'   ❌ Payment initialization: FAILED')
                self.stdout.write(f'   🚨 Error: {error}')
                
                # Detailed error analysis
                if isinstance(error, dict):
                    self.stdout.write('   📋 Detailed error breakdown:')
                    for key, value in error.items():
                        self.stdout.write(f'      • {key}: {value}')
                
                # Check if it's the reference error
                error_str = str(error).lower()
                if 'reference' in error_str and ('used' in error_str or 'invalid' in error_str):
                    self.stdout.write('   🎯 CONFIRMED: This is a reference-related error')
                    return 'reference_error'
                else:
                    self.stdout.write('   ℹ️  This is not a reference error')
                    return 'other_error'
                    
        except Exception as e:
            self.stdout.write(f'   ❌ Exception during payment: {str(e)}')
            return 'exception'
        
        return 'success'

    def test_reference_formats(self):
        """Test different reference formats to see what Chapa accepts"""
        client = ChapaClient()
        user = User.objects.filter(role='head_manager').first()
        
        if not user:
            self.stdout.write('   ⚠️  No head manager found')
            return
        
        # Test different reference formats
        import time
        import uuid
        
        test_formats = [
            f"EZM-{int(time.time())}-{uuid.uuid4().hex[:8].upper()}",  # Current format
            f"EZM_{int(time.time())}_{uuid.uuid4().hex[:8].upper()}",  # Underscores
            f"EZM{int(time.time())}{uuid.uuid4().hex[:8].upper()}",    # No separators
            f"TEST-{int(time.time())}-{uuid.uuid4().hex[:8].upper()}", # Different prefix
            f"{uuid.uuid4().hex.upper()}",                             # Pure UUID
            f"EZM-{uuid.uuid4()}",                                     # UUID with dashes
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
                    description=f'Format test {i+1}'
                )
                
                if result.get('success'):
                    self.stdout.write(f'      ✅ Format {i+1} ACCEPTED by Chapa')
                else:
                    error = result.get('error', 'Unknown error')
                    self.stdout.write(f'      ❌ Format {i+1} REJECTED: {error}')
                    
            except Exception as e:
                self.stdout.write(f'      ❌ Format {i+1} EXCEPTION: {str(e)}')
            
            time.sleep(0.5)  # Small delay between tests

    def test_database_references(self):
        """Check existing references in database"""
        total_transactions = ChapaTransaction.objects.count()
        self.stdout.write(f'   📊 Total transactions in database: {total_transactions}')
        
        if total_transactions > 0:
            # Show recent references
            recent_transactions = ChapaTransaction.objects.order_by('-created_at')[:5]
            self.stdout.write('   📋 Recent transaction references:')
            for tx in recent_transactions:
                self.stdout.write(f'      • {tx.chapa_tx_ref} - {tx.status} - {tx.created_at}')
            
            # Check for any duplicate references in database
            from django.db.models import Count
            duplicates = ChapaTransaction.objects.values('chapa_tx_ref').annotate(
                count=Count('chapa_tx_ref')
            ).filter(count__gt=1)
            
            if duplicates:
                self.stdout.write(f'   ⚠️  Found {len(duplicates)} duplicate references in database:')
                for dup in duplicates:
                    self.stdout.write(f'      • {dup["chapa_tx_ref"]}: {dup["count"]} occurrences')
            else:
                self.stdout.write('   ✅ No duplicate references in database')
        else:
            self.stdout.write('   ℹ️  No transactions in database yet')

    def provide_solution(self):
        """Provide solution based on debug results"""
        self.stdout.write('\n🎯 SOLUTION ANALYSIS')
        self.stdout.write('-' * 50)
        
        # Test a payment to see current error
        client = ChapaClient()
        user = User.objects.filter(role='head_manager').first()
        
        if user:
            self.stdout.write('🧪 Final test with current system:')
            result = client.initialize_payment(
                amount=Decimal('50.00'),
                email=user.email,
                first_name=user.first_name or user.username,
                last_name=user.last_name or 'Test',
                description='Final debug test'
            )
            
            if result.get('success'):
                self.stdout.write('✅ CURRENT SYSTEM WORKING - No "Invalid payment reference" error!')
                self.stdout.write(f'   Reference: {result.get("tx_ref")}')
                self.stdout.write(f'   Checkout URL: {result.get("checkout_url", "")[:50]}...')
            else:
                error = result.get('error', 'Unknown error')
                self.stdout.write(f'❌ CURRENT ERROR: {error}')
                
                # Provide specific solution based on error
                error_str = str(error).lower()
                if 'reference' in error_str and 'used' in error_str:
                    self.stdout.write('\n🔧 SOLUTION FOR DUPLICATE REFERENCE:')
                    self.stdout.write('   1. Implement even more unique reference generation')
                    self.stdout.write('   2. Add random salt to timestamp')
                    self.stdout.write('   3. Check Chapa global reference registry')
                elif 'invalid' in error_str and 'reference' in error_str:
                    self.stdout.write('\n🔧 SOLUTION FOR INVALID REFERENCE FORMAT:')
                    self.stdout.write('   1. Check reference format requirements')
                    self.stdout.write('   2. Ensure proper character encoding')
                    self.stdout.write('   3. Validate reference length limits')
                elif 'authentication' in error_str or 'unauthorized' in error_str:
                    self.stdout.write('\n🔧 SOLUTION FOR AUTH ERROR:')
                    self.stdout.write('   1. Verify Chapa API keys are correct')
                    self.stdout.write('   2. Check if keys are active in Chapa dashboard')
                    self.stdout.write('   3. Ensure proper header format')
                else:
                    self.stdout.write(f'\n🔧 SOLUTION FOR OTHER ERROR: {error}')
                    self.stdout.write('   1. Check Chapa API documentation')
                    self.stdout.write('   2. Verify all required fields')
                    self.stdout.write('   3. Check network connectivity')
        
        self.stdout.write('\n💡 IMMEDIATE ACTIONS:')
        self.stdout.write('   1. Run this debug command to see exact error')
        self.stdout.write('   2. Check Chapa dashboard for any account issues')
        self.stdout.write('   3. Verify API keys are active and correct')
        self.stdout.write('   4. Test with minimal payment data')
        
        self.stdout.write('\n🚀 If error persists, the system will implement:')
        self.stdout.write('   • Ultra-unique reference generation with nanosecond precision')
        self.stdout.write('   • Multiple fallback reference formats')
        self.stdout.write('   • Enhanced error detection and retry logic')
        self.stdout.write('   • Real-time Chapa API status checking')
