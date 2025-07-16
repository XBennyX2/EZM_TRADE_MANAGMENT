"""
Django management command to debug payment reference issues
Based on common Chapa API problems and solutions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from payments.models import ChapaTransaction
from payments.chapa_client import ChapaClient
from payments.services import ChapaPaymentService
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Debug payment reference issues and validate Chapa integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tx-ref',
            type=str,
            help='Specific transaction reference to debug'
        )
        parser.add_argument(
            '--test-generation',
            action='store_true',
            help='Test reference generation for uniqueness'
        )
        parser.add_argument(
            '--test-api',
            action='store_true',
            help='Test Chapa API integration'
        )
        parser.add_argument(
            '--check-duplicates',
            action='store_true',
            help='Check for duplicate references in database'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Payment Reference Debug Tool')
        )
        self.stdout.write('=' * 60)

        if options['tx_ref']:
            self.debug_specific_transaction(options['tx_ref'])
        
        if options['test_generation']:
            self.test_reference_generation()
        
        if options['test_api']:
            self.test_chapa_api()
        
        if options['check_duplicates']:
            self.check_duplicate_references()
        
        if not any([options['tx_ref'], options['test_generation'], 
                   options['test_api'], options['check_duplicates']]):
            self.run_comprehensive_check()

    def debug_specific_transaction(self, tx_ref):
        """Debug a specific transaction reference"""
        self.stdout.write(f"\n🔍 Debugging transaction: {tx_ref}")
        self.stdout.write("-" * 40)
        
        try:
            # Check database
            transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref)
            self.stdout.write(f"✅ Found in database:")
            self.stdout.write(f"   Status: {transaction.status}")
            self.stdout.write(f"   Created: {transaction.created_at}")
            self.stdout.write(f"   User: {transaction.user.username}")
            self.stdout.write(f"   Supplier: {transaction.supplier.name}")
            self.stdout.write(f"   Amount: ETB {transaction.amount}")
            self.stdout.write(f"   Checkout URL: {'Yes' if transaction.chapa_checkout_url else 'No'}")
            
            # Verify with Chapa
            client = ChapaClient()
            verification = client.verify_payment(tx_ref)
            
            if verification['success']:
                self.stdout.write(f"✅ Chapa verification successful:")
                self.stdout.write(f"   Chapa Status: {verification.get('status')}")
                self.stdout.write(f"   Amount: {verification.get('amount')}")
                self.stdout.write(f"   Currency: {verification.get('currency')}")
            else:
                self.stdout.write(f"❌ Chapa verification failed:")
                self.stdout.write(f"   Error: {verification.get('error')}")
                
        except ChapaTransaction.DoesNotExist:
            self.stdout.write(f"❌ Transaction not found in database")
            
            # Still try Chapa verification
            client = ChapaClient()
            verification = client.verify_payment(tx_ref)
            
            if verification['success']:
                self.stdout.write(f"⚠️  Found in Chapa but not in database:")
                self.stdout.write(f"   Status: {verification.get('status')}")
                self.stdout.write(f"   Amount: {verification.get('amount')}")
            else:
                self.stdout.write(f"❌ Not found in Chapa either:")
                self.stdout.write(f"   Error: {verification.get('error')}")

    def test_reference_generation(self):
        """Test reference generation for uniqueness and format"""
        self.stdout.write(f"\n🧪 Testing Reference Generation")
        self.stdout.write("-" * 35)
        
        client = ChapaClient()
        references = []
        
        # Generate multiple references
        for i in range(20):
            ref = client.generate_tx_ref()
            references.append(ref)
            if i < 5:  # Show first 5
                self.stdout.write(f"   {i+1:2d}. {ref}")
        
        if len(references) > 5:
            self.stdout.write(f"   ... and {len(references) - 5} more")
        
        # Check uniqueness
        unique_refs = set(references)
        if len(unique_refs) == len(references):
            self.stdout.write(f"✅ All {len(references)} references are unique")
        else:
            duplicates = len(references) - len(unique_refs)
            self.stdout.write(f"❌ Found {duplicates} duplicate references")
        
        # Check format
        format_issues = []
        for ref in references:
            if not ref.startswith('EZM-'):
                format_issues.append(f"Missing EZM- prefix: {ref}")
            if len(ref) > 50:
                format_issues.append(f"Too long (>{50}): {ref}")
            if len(ref) < 10:
                format_issues.append(f"Too short (<10): {ref}")
        
        if format_issues:
            self.stdout.write(f"❌ Format issues found:")
            for issue in format_issues[:5]:  # Show first 5
                self.stdout.write(f"   {issue}")
        else:
            self.stdout.write(f"✅ All references have valid format")

    def test_chapa_api(self):
        """Test Chapa API integration"""
        self.stdout.write(f"\n🌐 Testing Chapa API Integration")
        self.stdout.write("-" * 35)
        
        # Get test user
        user = User.objects.filter(role='head_manager').first()
        if not user:
            self.stdout.write(f"❌ No head manager user found for testing")
            return
        
        client = ChapaClient()
        
        # Test payment initialization
        result = client.initialize_payment(
            amount=Decimal('10.00'),
            email=user.email,
            first_name=user.first_name or user.username,
            last_name=user.last_name or 'Test',
            description='Debug test payment'
        )
        
        if result['success']:
            self.stdout.write(f"✅ Payment initialization successful:")
            self.stdout.write(f"   TX Ref: {result.get('tx_ref')}")
            self.stdout.write(f"   Checkout URL: {result.get('checkout_url', '')[:50]}...")
            
            # Test verification immediately
            tx_ref = result.get('tx_ref')
            verification = client.verify_payment(tx_ref)
            
            if verification['success']:
                self.stdout.write(f"✅ Immediate verification successful:")
                self.stdout.write(f"   Status: {verification.get('status')}")
            else:
                self.stdout.write(f"⚠️  Immediate verification failed (expected for new payment):")
                self.stdout.write(f"   Error: {verification.get('error')}")
        else:
            self.stdout.write(f"❌ Payment initialization failed:")
            self.stdout.write(f"   Error: {result.get('error')}")
            self.stdout.write(f"   Retry count: {result.get('retry_count', 0)}")

    def check_duplicate_references(self):
        """Check for duplicate references in database"""
        self.stdout.write(f"\n🔍 Checking for Duplicate References")
        self.stdout.write("-" * 40)
        
        from django.db.models import Count
        
        duplicates = ChapaTransaction.objects.values('chapa_tx_ref').annotate(
            count=Count('chapa_tx_ref')
        ).filter(count__gt=1)
        
        if duplicates:
            self.stdout.write(f"❌ Found {len(duplicates)} duplicate references:")
            for dup in duplicates:
                self.stdout.write(f"   {dup['chapa_tx_ref']}: {dup['count']} times")
        else:
            self.stdout.write(f"✅ No duplicate references found")
        
        # Check total transactions
        total = ChapaTransaction.objects.count()
        self.stdout.write(f"📊 Total transactions in database: {total}")

    def run_comprehensive_check(self):
        """Run all checks"""
        self.test_reference_generation()
        self.test_chapa_api()
        self.check_duplicate_references()
        
        self.stdout.write(f"\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS('🎉 Payment Reference Debug Complete!')
        )
        self.stdout.write(f"\nFor specific transaction debugging, use:")
        self.stdout.write(f"python manage.py debug_payment_references --tx-ref YOUR_TX_REF")
