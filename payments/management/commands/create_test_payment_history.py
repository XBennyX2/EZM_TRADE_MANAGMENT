from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid
import json

from payments.models import ChapaTransaction, PurchaseOrderPayment
from Inventory.models import Supplier

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test payment history data for Head Manager testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating test payment history data...')

        # Get or create head manager
        head_manager, created = User.objects.get_or_create(
            username='head_manager_test',
            defaults={
                'email': 'head_manager@test.com',
                'role': 'head_manager',
                'is_first_login': False,
                'first_name': 'Head',
                'last_name': 'Manager'
            }
        )
        if created:
            head_manager.set_password('password123')
            head_manager.save()
            self.stdout.write(f'Created head manager: {head_manager.username}')

        # Get or create test suppliers
        suppliers_data = [
            {'name': 'ABC Construction Supplies', 'email': 'abc@supplier.com', 'phone': '555-0101'},
            {'name': 'XYZ Building Materials', 'email': 'xyz@supplier.com', 'phone': '555-0102'},
            {'name': 'Premium Hardware Co.', 'email': 'premium@supplier.com', 'phone': '555-0103'},
        ]

        suppliers = []
        for supplier_data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_data['name'],
                defaults={
                    'email': supplier_data['email'],
                    'phone': supplier_data['phone'],
                    'address': f"123 {supplier_data['name']} Street",
                    'is_active': True
                }
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f'Created supplier: {supplier.name}')

        # Create test payment transactions
        payment_data = [
            {
                'supplier': suppliers[0],
                'amount': Decimal('1250.00'),
                'status': 'success',
                'description': 'Payment for PVC pipes and fittings - Order #PO-001',
                'days_ago': 1,
                'items': [
                    {'name': 'PVC Pipe 2 inch', 'quantity': 50, 'price': '15.99'},
                    {'name': 'PVC Elbow Joint', 'quantity': 20, 'price': '3.25'},
                    {'name': 'PVC T-Joint', 'quantity': 15, 'price': '4.50'}
                ]
            },
            {
                'supplier': suppliers[1],
                'amount': Decimal('2750.50'),
                'status': 'success',
                'description': 'Payment for cement and aggregates - Order #PO-002',
                'days_ago': 3,
                'items': [
                    {'name': 'Portland Cement 50kg', 'quantity': 100, 'price': '12.50'},
                    {'name': 'Gravel 20mm', 'quantity': 5, 'price': '45.00'},
                    {'name': 'Sand Fine Grade', 'quantity': 3, 'price': '35.00'}
                ]
            },
            {
                'supplier': suppliers[2],
                'amount': Decimal('890.75'),
                'status': 'success',
                'description': 'Payment for electrical supplies - Order #PO-003',
                'days_ago': 5,
                'items': [
                    {'name': 'Copper Wire 12 AWG', 'quantity': 10, 'price': '89.99'},
                    {'name': 'Electrical Outlet', 'quantity': 25, 'price': '2.50'},
                    {'name': 'Circuit Breaker 20A', 'quantity': 5, 'price': '15.75'}
                ]
            },
            {
                'supplier': suppliers[0],
                'amount': Decimal('567.25'),
                'status': 'pending',
                'description': 'Payment for ceramic tiles - Order #PO-004',
                'days_ago': 0,
                'items': [
                    {'name': 'Ceramic Floor Tiles', 'quantity': 150, 'price': '3.25'},
                    {'name': 'Tile Adhesive', 'quantity': 10, 'price': '8.50'},
                    {'name': 'Grout White', 'quantity': 5, 'price': '6.75'}
                ]
            },
            {
                'supplier': suppliers[1],
                'amount': Decimal('1875.00'),
                'status': 'failed',
                'description': 'Payment for glass panels - Order #PO-005',
                'days_ago': 2,
                'items': [
                    {'name': 'Tempered Glass Panel', 'quantity': 15, 'price': '125.00'}
                ]
            }
        ]

        for i, data in enumerate(payment_data):
            # Generate transaction reference
            tx_ref = f"EZM-TEST-{uuid.uuid4().hex[:8].upper()}"
            
            # Calculate dates
            created_date = timezone.now() - timedelta(days=data['days_ago'])
            paid_date = created_date + timedelta(hours=2) if data['status'] == 'success' else None

            # Create transaction
            transaction = ChapaTransaction.objects.create(
                chapa_tx_ref=tx_ref,
                amount=data['amount'],
                currency='ETB',
                description=data['description'],
                user=head_manager,
                supplier=data['supplier'],
                status=data['status'],
                customer_email=head_manager.email,
                customer_first_name=head_manager.first_name,
                customer_last_name=head_manager.last_name,
                customer_phone='555-0100',
                created_at=created_date,
                paid_at=paid_date,
                chapa_response={
                    'status': 'success' if data['status'] == 'success' else 'failed',
                    'tx_ref': tx_ref,
                    'amount': str(data['amount']),
                    'currency': 'ETB'
                },
                webhook_data={
                    'tx_ref': tx_ref,
                    'status': data['status'],
                    'amount': str(data['amount']),
                    'currency': 'ETB',
                    'supplier_name': data['supplier'].name,
                    'customer_name': f"{head_manager.first_name} {head_manager.last_name}",
                    'payment_method': 'Test Payment',
                    'processed_at': created_date.isoformat()
                }
            )

            # Create purchase order payment
            order_status = 'payment_confirmed' if data['status'] == 'success' else 'initial'
            if data['status'] == 'failed':
                order_status = 'cancelled'

            order_payment = PurchaseOrderPayment.objects.create(
                chapa_transaction=transaction,
                supplier=data['supplier'],
                user=head_manager,
                status=order_status,
                order_items=data['items'],
                subtotal=data['amount'],
                total_amount=data['amount'],
                created_at=created_date,
                payment_confirmed_at=paid_date if data['status'] == 'success' else None,
                notes=f"Test order for {data['supplier'].name}"
            )

            self.stdout.write(f'Created payment transaction: {tx_ref} - {data["status"]} - ETB {data["amount"]}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Test payment history data created successfully!'))
        self.stdout.write('')
        self.stdout.write('Test account:')
        self.stdout.write(f'Head Manager: head_manager_test / password123')
        self.stdout.write('')
        self.stdout.write('You can now test the Payment History functionality!')
        self.stdout.write('Navigate to: http://localhost:8001/payments/history/')
