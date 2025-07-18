"""
Payment to Transaction Service
Handles the complete workflow from Chapa payment completion to transaction creation
"""

from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import timedelta
import logging

from .models import ChapaTransaction, PurchaseOrderPayment
from transactions.models import Transaction, FinancialRecord, SupplierTransaction
from Inventory.models import PurchaseOrder, Store
from store.models import Store as StoreModel

User = get_user_model()
logger = logging.getLogger(__name__)


class PaymentTransactionService:
    """
    Service to handle payment completion and transaction creation workflow
    """
    
    @staticmethod
    def create_transaction_from_payment(chapa_transaction):
        """
        Create a Transaction record from a completed Chapa payment
        
        Args:
            chapa_transaction (ChapaTransaction): The completed payment transaction
            
        Returns:
            dict: Result with success status and created transaction details
        """
        try:
            with db_transaction.atomic():
                # Get the purchase order payment
                if not hasattr(chapa_transaction, 'purchase_order_payment'):
                    logger.error(f"No purchase order payment found for transaction {chapa_transaction.chapa_tx_ref}")
                    return {
                        'success': False,
                        'error': 'No purchase order payment found'
                    }
                
                order_payment = chapa_transaction.purchase_order_payment
                order_items = order_payment.order_items or []
                
                # Get or create a default store for the transaction
                store, created = StoreModel.objects.get_or_create(
                    name='Head Office',
                    defaults={
                        'address': 'Main Office Location',
                        'phone_number': '+251911000000',
                        'store_manager': chapa_transaction.user
                    }
                )
                
                if created:
                    logger.info(f"Created default store 'Head Office' for transaction {chapa_transaction.chapa_tx_ref}")
                
                # Create main transaction record
                transaction_record = Transaction.objects.create(
                    quantity=sum(item.get('quantity', 0) for item in order_items),
                    transaction_type='sale',  # This is a purchase from supplier = sale to us
                    store=store,
                    total_amount=chapa_transaction.amount,
                    payment_type='mobile',  # Chapa is mobile/online payment
                )
                
                # Create financial record
                financial_record = FinancialRecord.objects.create(
                    store=store,
                    amount=chapa_transaction.amount,
                    record_type='expense',  # Purchase from supplier is an expense
                    description=f"Purchase from {chapa_transaction.supplier.name} - Payment Ref: {chapa_transaction.chapa_tx_ref}"
                )
                
                # Create supplier transaction
                supplier_transaction = PaymentTransactionService._create_supplier_transaction(
                    chapa_transaction, transaction_record
                )
                
                # Create or update purchase order
                purchase_order = PaymentTransactionService._create_or_update_purchase_order(
                    chapa_transaction, order_payment
                )
                
                logger.info(f"Successfully created transaction records for payment {chapa_transaction.chapa_tx_ref}")
                
                return {
                    'success': True,
                    'transaction': transaction_record,
                    'financial_record': financial_record,
                    'supplier_transaction': supplier_transaction,
                    'message': 'Transaction records created successfully'
                }
                
        except Exception as e:
            logger.error(f"Error creating transaction from payment {chapa_transaction.chapa_tx_ref}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _create_supplier_transaction(chapa_transaction, transaction_record):
        """
        Create a supplier transaction record
        
        Args:
            chapa_transaction (ChapaTransaction): The payment transaction
            transaction_record (Transaction): The main transaction record
            
        Returns:
            SupplierTransaction: The created supplier transaction
        """
        from transactions.models import SupplierAccount
        
        # Get or create supplier account
        supplier_account, created = SupplierAccount.objects.get_or_create(
            supplier=chapa_transaction.supplier,
            defaults={
                'account_number': f"SA-{chapa_transaction.supplier.id:06d}",
                'current_balance': Decimal('0.00'),
                'credit_limit': Decimal('100000.00'),
                'payment_terms': 'net_30',
                'is_active': True
            }
        )
        
        if created:
            logger.info(f"Created supplier account for {chapa_transaction.supplier.name}")
        
        # Create supplier transaction
        supplier_transaction = SupplierTransaction.objects.create(
            transaction_number=f"ST-{chapa_transaction.chapa_tx_ref}",
            supplier_account=supplier_account,
            transaction_type='payment',
            amount=chapa_transaction.amount,
            status='completed',
            description=f"Payment for purchase order - Chapa Ref: {chapa_transaction.chapa_tx_ref}",
            reference_number=chapa_transaction.chapa_tx_ref,
            created_by=chapa_transaction.user
        )
        
        # Update supplier account balance
        supplier_account.current_balance += chapa_transaction.amount
        supplier_account.save()
        
        return supplier_transaction

    @staticmethod
    def _create_or_update_purchase_order(chapa_transaction, order_payment):
        """
        Create or update purchase order from payment transaction

        Args:
            chapa_transaction (ChapaTransaction): The payment transaction
            order_payment (PurchaseOrderPayment): The order payment record

        Returns:
            PurchaseOrder: The created or updated purchase order
        """
        from Inventory.models import PurchaseOrder, PurchaseOrderItem, WarehouseProduct
        from django.utils import timezone
        import uuid

        try:
            # Check if purchase order already exists
            if hasattr(order_payment, 'purchase_order') and order_payment.purchase_order:
                purchase_order = order_payment.purchase_order
                purchase_order.status = 'payment_confirmed'
                purchase_order.payment_confirmed_at = timezone.now()
                purchase_order.save()
                return purchase_order

            # Create new purchase order
            order_number = f"PO-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

            purchase_order = PurchaseOrder.objects.create(
                order_number=order_number,
                supplier=chapa_transaction.supplier,
                created_by=chapa_transaction.user,
                order_date=timezone.now().date(),
                expected_delivery_date=timezone.now().date() + timedelta(days=7),
                delivery_address="Head Office - Main Location",
                status='payment_confirmed',
                payment_status='completed',
                payment_reference=chapa_transaction.chapa_tx_ref,
                payment_confirmed_at=timezone.now(),
                total_amount=chapa_transaction.amount,
                notes=f"Order created from Chapa payment: {chapa_transaction.chapa_tx_ref}"
            )

            # Create purchase order items from order_items
            order_items = order_payment.order_items or []
            for item_data in order_items:
                # Try to find warehouse product by name
                try:
                    warehouse_product = WarehouseProduct.objects.filter(
                        product_name=item_data.get('product_name', ''),
                        is_active=True
                    ).first()

                    if warehouse_product:
                        PurchaseOrderItem.objects.create(
                            purchase_order=purchase_order,
                            warehouse_product=warehouse_product,
                            quantity_ordered=item_data.get('quantity', 1),
                            unit_price=item_data.get('price', 0),
                            total_price=item_data.get('total_price', 0)
                        )
                except Exception as e:
                    logger.error(f"Error creating purchase order item: {str(e)}")
                    continue

            # Link the purchase order to the order payment
            order_payment.purchase_order = purchase_order
            order_payment.save()

            logger.info(f"Created purchase order {order_number} from payment {chapa_transaction.chapa_tx_ref}")
            return purchase_order

        except Exception as e:
            logger.error(f"Error creating purchase order from payment: {str(e)}")
            return None

    @staticmethod
    def get_transaction_display_data(chapa_transaction):
        """
        Get properly formatted data for transaction display
        
        Args:
            chapa_transaction (ChapaTransaction): The payment transaction
            
        Returns:
            dict: Formatted transaction data for template display
        """
        try:
            # Get order items
            order_items = []
            if hasattr(chapa_transaction, 'purchase_order_payment'):
                order_payment = chapa_transaction.purchase_order_payment
                order_items = order_payment.order_items or []
            
            # Format customer name
            customer_name = f"{chapa_transaction.customer_first_name} {chapa_transaction.customer_last_name}".strip()
            
            # Format payment reference (clean up the format)
            payment_ref = chapa_transaction.chapa_tx_ref
            if payment_ref.startswith('EZM-'):
                # Clean up the reference format for better display
                ref_parts = payment_ref.split('-')
                if len(ref_parts) >= 2:
                    payment_ref = f"EZM-{ref_parts[1][:8]}"  # Show first 8 chars after EZM-
            
            # Format supplier name
            supplier_name = chapa_transaction.supplier.name if chapa_transaction.supplier else "Unknown Supplier"
            
            return {
                'transaction_id': payment_ref,
                'customer_name': customer_name,
                'customer_email': chapa_transaction.customer_email,
                'customer_phone': chapa_transaction.customer_phone or 'Not provided',
                'supplier_name': supplier_name,
                'amount': chapa_transaction.amount,
                'currency': chapa_transaction.currency,
                'payment_date': chapa_transaction.paid_at or chapa_transaction.created_at,
                'order_date': chapa_transaction.created_at,
                'status': chapa_transaction.status,
                'order_items': order_items,
                'description': chapa_transaction.description,
                'payment_method': 'Chapa Payment Gateway'
            }
            
        except Exception as e:
            logger.error(f"Error formatting transaction display data: {str(e)}")
            return {
                'transaction_id': chapa_transaction.chapa_tx_ref,
                'customer_name': 'Unknown Customer',
                'supplier_name': 'Unknown Supplier',
                'amount': chapa_transaction.amount,
                'currency': chapa_transaction.currency,
                'payment_date': chapa_transaction.created_at,
                'status': chapa_transaction.status,
                'order_items': [],
                'error': 'Error formatting transaction data'
            }
    
    @staticmethod
    def process_payment_completion(tx_ref, user):
        """
        Complete payment processing workflow
        
        Args:
            tx_ref (str): Transaction reference
            user (User): The user who made the payment
            
        Returns:
            dict: Complete processing result
        """
        try:
            # Get the transaction
            chapa_transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref, user=user)
            
            # Ensure payment is successful
            if chapa_transaction.status != 'success':
                return {
                    'success': False,
                    'error': 'Payment not completed successfully'
                }
            
            # Create transaction records
            transaction_result = PaymentTransactionService.create_transaction_from_payment(chapa_transaction)
            
            # Get display data
            display_data = PaymentTransactionService.get_transaction_display_data(chapa_transaction)
            
            return {
                'success': True,
                'chapa_transaction': chapa_transaction,
                'transaction_result': transaction_result,
                'display_data': display_data,
                'message': 'Payment processing completed successfully'
            }
            
        except ChapaTransaction.DoesNotExist:
            return {
                'success': False,
                'error': 'Transaction not found'
            }
        except Exception as e:
            logger.error(f"Error processing payment completion for {tx_ref}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
