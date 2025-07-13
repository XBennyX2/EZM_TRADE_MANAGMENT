from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from .models import ChapaTransaction, PurchaseOrderPayment
from .chapa_client import ChapaClient
from .notification_service import supplier_notification_service
from Inventory.models import Supplier
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class ChapaPaymentService:
    """
    Service class for handling Chapa payment operations
    """

    def __init__(self):
        self.client = ChapaClient()

    def _create_chapa_title(self, supplier_name):
        """
        Create a Chapa-compliant title (max 16 characters)

        Args:
            supplier_name (str): The supplier name

        Returns:
            str: A title that fits within Chapa's 16-character limit
        """
        # Start with "EZM-" prefix (4 characters)
        prefix = "EZM-"
        max_supplier_chars = 16 - len(prefix)  # 12 characters remaining

        # Clean and truncate supplier name
        clean_name = supplier_name.replace(" ", "").replace("-", "").replace(".", "")
        truncated_name = clean_name[:max_supplier_chars]
        title = f"{prefix}{truncated_name}"

        # Ensure we never exceed 16 characters
        if len(title) > 16:
            title = title[:16]

        logger.info(f"Generated Chapa title: '{title}' (length: {len(title)}) for supplier: {supplier_name}")
        return title
    
    def create_payment_for_supplier(self, user, supplier, cart_items, request=None):
        """
        Create a Chapa payment transaction for a specific supplier's items
        
        Args:
            user: The user making the payment
            supplier: The supplier for this payment
            cart_items: List of cart items for this supplier
            request: Django request object for URL generation
        
        Returns:
            dict: Payment creation result
        """
        try:
            # Calculate total amount for this supplier
            total_amount = sum(
                Decimal(str(item['price'])) * item['quantity'] 
                for item in cart_items
            )
            
            # Generate transaction reference
            tx_ref = self.client.generate_tx_ref()
            
            # Prepare callback URLs
            if request:
                callback_url = request.build_absolute_uri(
                    reverse('chapa_webhook')
                )
                return_url = request.build_absolute_uri(
                    reverse('payment_success')
                )
            else:
                callback_url = None
                return_url = None
            
            # Create description
            item_count = len(cart_items)
            description = f"Payment for {item_count} item{'s' if item_count > 1 else ''} from {supplier.name}"
            
            # Enhanced payment initialization with comprehensive payment method support
            # Use a simple, short title that's guaranteed to be under 16 characters
            customization = {
                "title": "EZM Payment",  # 11 characters - well under 16 limit
                "description": f"Payment for {item_count} item{'s' if item_count > 1 else ''} from {supplier.name}"
            }

            meta = {
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "item_count": item_count,
                "order_type": "purchase_order"
            }

            payment_result = self.client.initialize_payment(
                amount=total_amount,
                email=user.email,
                first_name=user.first_name or user.username,
                last_name=user.last_name or '',
                phone=getattr(user, 'phone', None),
                callback_url=callback_url,
                return_url=return_url,
                description=description,
                tx_ref=tx_ref,
                customization=customization,
                meta=meta
            )
            
            if payment_result['success']:
                try:
                    # Try to create real transaction record
                    transaction = ChapaTransaction.objects.create(
                        chapa_tx_ref=tx_ref,
                        chapa_checkout_url=payment_result.get('checkout_url'),
                        amount=total_amount,
                        currency='ETB',
                        description=description,
                        user=user,
                        supplier=supplier,
                        status='pending',
                        chapa_response=payment_result.get('data'),
                        customer_email=user.email,
                        customer_first_name=user.first_name or user.username,
                        customer_last_name=user.last_name or '',
                        customer_phone=getattr(user, 'phone', None)
                    )

                    # Create purchase order payment record
                    order_payment = PurchaseOrderPayment.objects.create(
                        chapa_transaction=transaction,
                        supplier=supplier,
                        user=user,
                        status='initial',
                        order_items=cart_items,
                        subtotal=total_amount,
                        total_amount=total_amount
                    )

                    logger.info(f"Payment created successfully: {tx_ref} for {total_amount} ETB")

                    return {
                        'success': True,
                        'transaction': transaction,
                        'order_payment': order_payment,
                        'checkout_url': payment_result.get('checkout_url'),
                        'tx_ref': tx_ref,
                        'message': 'Payment initialized successfully'
                    }

                except Exception as db_error:
                    # If database tables don't exist, create mock transaction
                    logger.warning(f"Database not available, using mock payment: {db_error}")

                    mock_transaction = {
                        'chapa_tx_ref': tx_ref,
                        'chapa_checkout_url': payment_result.get('checkout_url'),
                        'amount': total_amount,
                        'currency': 'ETB',
                        'description': description,
                        'user': user,
                        'supplier': supplier,
                        'status': 'pending',
                        'customer_email': user.email,
                        'customer_first_name': user.first_name or user.username,
                        'customer_last_name': user.last_name or '',
                        'customer_phone': getattr(user, 'phone', None)
                    }

                    mock_order_payment = {
                        'supplier': supplier,
                        'user': user,
                        'status': 'initial',
                        'order_items': cart_items,
                        'subtotal': total_amount,
                        'total_amount': total_amount
                    }

                    return {
                        'success': True,
                        'transaction': mock_transaction,
                        'order_payment': mock_order_payment,
                        'checkout_url': payment_result.get('checkout_url'),
                        'tx_ref': tx_ref,
                        'message': 'Payment initialized successfully (mock mode)'
                    }
            else:
                logger.error(f"Failed to initialize payment: {payment_result.get('error')}")
                return {
                    'success': False,
                    'error': payment_result.get('error', 'Payment initialization failed'),
                    'message': 'Failed to initialize payment with Chapa'
                }
                
        except Exception as e:
            logger.error(f"Error creating payment for supplier {supplier.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An error occurred while creating the payment'
            }
    
    def create_payments_for_cart(self, user, suppliers_cart, request=None):
        """
        Create separate payment transactions for each supplier in the cart
        
        Args:
            user: The user making the payments
            suppliers_cart: Dictionary of suppliers and their cart items
            request: Django request object for URL generation
        
        Returns:
            dict: Results of payment creation for all suppliers
        """
        results = {
            'success': True,
            'payments': [],
            'errors': [],
            'total_amount': Decimal('0.00')
        }
        
        for supplier_id, supplier_data in suppliers_cart.items():
            try:
                supplier = Supplier.objects.get(id=supplier_id)
                cart_items = supplier_data['items']
                
                payment_result = self.create_payment_for_supplier(
                    user=user,
                    supplier=supplier,
                    cart_items=cart_items,
                    request=request
                )
                
                if payment_result['success']:
                    results['payments'].append({
                        'supplier': supplier,
                        'transaction': payment_result['transaction'],
                        'order_payment': payment_result['order_payment'],
                        'checkout_url': payment_result['checkout_url'],
                        'tx_ref': payment_result['tx_ref'],
                        'amount': payment_result['transaction']['amount']
                    })
                    results['total_amount'] += payment_result['transaction']['amount']
                else:
                    results['errors'].append({
                        'supplier': supplier,
                        'error': payment_result['error']
                    })
                    results['success'] = False
                    
            except Supplier.DoesNotExist:
                error_msg = f"Supplier with ID {supplier_id} not found"
                logger.error(error_msg)
                results['errors'].append({
                    'supplier_id': supplier_id,
                    'error': error_msg
                })
                results['success'] = False
            except Exception as e:
                error_msg = f"Error processing payment for supplier {supplier_id}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append({
                    'supplier_id': supplier_id,
                    'error': error_msg
                })
                results['success'] = False
        
        return results
    
    def verify_payment(self, tx_ref):
        """
        Verify a payment transaction with Chapa
        
        Args:
            tx_ref: Transaction reference
        
        Returns:
            dict: Verification result
        """
        try:
            transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref)
            
            # Verify with Chapa
            verification_result = self.client.verify_payment(tx_ref)
            
            if verification_result['success']:
                # Update transaction status
                old_status = transaction.status
                chapa_status = verification_result.get('status', '').lower()

                if chapa_status == 'success':
                    transaction.status = 'success'
                    transaction.paid_at = timezone.now()
                elif chapa_status in ['failed', 'cancelled']:
                    transaction.status = 'failed'
                else:
                    transaction.status = 'pending'

                transaction.save()

                # Send supplier notification if status changed to success
                if old_status != 'success' and transaction.status == 'success':
                    try:
                        order_payment = getattr(transaction, 'purchase_order_payment', None)
                        supplier_notification_service.send_payment_confirmation_notification(
                            transaction, order_payment
                        )
                        logger.info(f"Payment confirmation notification sent for transaction {tx_ref}")
                    except Exception as e:
                        logger.error(f"Failed to send payment confirmation notification for {tx_ref}: {str(e)}")

                # Send status change notification for significant changes
                if old_status != transaction.status:
                    try:
                        supplier_notification_service.send_payment_status_change_notification(
                            transaction, old_status, transaction.status
                        )
                        logger.info(f"Payment status change notification sent for transaction {tx_ref}")
                    except Exception as e:
                        logger.error(f"Failed to send status change notification for {tx_ref}: {str(e)}")
                
                # Update related purchase order payment
                if hasattr(transaction, 'purchase_order_payment'):
                    transaction.purchase_order_payment.update_status_from_payment()
                
                logger.info(f"Payment verification completed: {tx_ref} - {transaction.status}")
                
                return {
                    'success': True,
                    'transaction': transaction,
                    'status': transaction.status,
                    'verified': True
                }
            else:
                logger.error(f"Payment verification failed: {verification_result.get('error')}")
                return {
                    'success': False,
                    'error': verification_result.get('error'),
                    'verified': False
                }
                
        except ChapaTransaction.DoesNotExist:
            logger.error(f"Transaction not found: {tx_ref}")
            return {
                'success': False,
                'error': 'Transaction not found',
                'verified': False
            }
        except Exception as e:
            logger.error(f"Error verifying payment {tx_ref}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'verified': False
            }
    
    def get_user_transactions(self, user, status=None):
        """
        Get all transactions for a user
        
        Args:
            user: User object
            status: Optional status filter
        
        Returns:
            QuerySet: User's transactions
        """
        queryset = ChapaTransaction.objects.filter(user=user)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')
    
    def get_supplier_transactions(self, supplier, status=None):
        """
        Get all transactions for a supplier
        
        Args:
            supplier: Supplier object
            status: Optional status filter
        
        Returns:
            QuerySet: Supplier's transactions
        """
        queryset = ChapaTransaction.objects.filter(supplier=supplier)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')
