from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models import ChapaTransaction


class Command(BaseCommand):
    help = 'Fix pending payment transactions by updating them to success status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tx-ref',
            type=str,
            help='Specific transaction reference to update',
        )
        parser.add_argument(
            '--all-pending',
            action='store_true',
            help='Update all pending transactions to success',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Update pending transactions for specific user (username)',
        )

    def handle(self, *args, **options):
        tx_ref = options.get('tx_ref')
        all_pending = options.get('all_pending')
        username = options.get('user')

        if tx_ref:
            # Update specific transaction
            try:
                transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref)
                if transaction.status == 'pending':
                    transaction.status = 'success'
                    transaction.paid_at = timezone.now()
                    transaction.save()
                    
                    # Update purchase order payment
                    if hasattr(transaction, 'purchase_order_payment'):
                        order_payment = transaction.purchase_order_payment
                        if order_payment.status in ['initial', 'payment_pending']:
                            order_payment.status = 'payment_confirmed'
                            order_payment.payment_confirmed_at = timezone.now()
                            order_payment.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated transaction {tx_ref} to success')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Transaction {tx_ref} is already {transaction.status}')
                    )
            except ChapaTransaction.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Transaction {tx_ref} not found')
                )

        elif all_pending or username:
            # Update multiple transactions
            queryset = ChapaTransaction.objects.filter(status='pending')
            
            if username:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(username=username)
                    queryset = queryset.filter(user=user)
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'User {username} not found')
                    )
                    return

            updated_count = 0
            for transaction in queryset:
                transaction.status = 'success'
                transaction.paid_at = timezone.now()
                transaction.save()
                
                # Update purchase order payment
                if hasattr(transaction, 'purchase_order_payment'):
                    order_payment = transaction.purchase_order_payment
                    if order_payment.status in ['initial', 'payment_pending']:
                        order_payment.status = 'payment_confirmed'
                        order_payment.payment_confirmed_at = timezone.now()
                        order_payment.save()
                
                updated_count += 1
                self.stdout.write(f'Updated {transaction.chapa_tx_ref} to success')

            self.stdout.write(
                self.style.SUCCESS(f'Updated {updated_count} transactions to success')
            )

        else:
            self.stdout.write(
                self.style.ERROR('Please specify --tx-ref, --all-pending, or --user')
            )
            self.stdout.write('')
            self.stdout.write('Examples:')
            self.stdout.write('  python manage.py fix_pending_payments --tx-ref EZM-TEST-12345')
            self.stdout.write('  python manage.py fix_pending_payments --user head_manager_test')
            self.stdout.write('  python manage.py fix_pending_payments --all-pending')
