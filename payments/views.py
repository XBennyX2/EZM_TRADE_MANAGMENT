import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.contrib import messages
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
from utils.cart import Cart
from .services import ChapaPaymentService
from .models import ChapaTransaction, PaymentWebhookLog
import hmac
import hashlib

logger = logging.getLogger(__name__)


def is_head_manager(user):
    """Check if user is a head manager"""
    return user.is_authenticated and user.role == 'head_manager'


@login_required
@user_passes_test(is_head_manager)
def initiate_payment(request):
    """
    Initiate payment process for cart items
    """
    try:
        cart = Cart(request)

        if not cart.cart:
            messages.error(request, 'Your cart is empty.')
            return redirect('cart_view')

        # Get suppliers cart data
        suppliers_cart = cart.get_cart_by_supplier()

        if not suppliers_cart:
            messages.error(request, 'No items found in cart.')
            return redirect('cart_view')

        # Handle GET request - show payment confirmation
        if request.method == 'GET':
            context = {
                'suppliers_cart': suppliers_cart,
                'total_suppliers': len(suppliers_cart),
                'total_items': cart.get_total_items(),
                'total_price': cart.get_total_price(),
            }
            return render(request, 'payments/payment_confirmation.html', context)

        # Handle POST request - create payments
        if request.method == 'POST':
            # Create payments for all suppliers
            payment_service = ChapaPaymentService()
            payment_results = payment_service.create_payments_for_cart(
                user=request.user,
                suppliers_cart=suppliers_cart,
                request=request
            )

            if payment_results['success']:
                # Store payment information in session for tracking
                request.session['payment_transactions'] = [
                    {
                        'tx_ref': payment['tx_ref'],
                        'supplier_id': payment['supplier'].id,
                        'supplier_name': payment['supplier'].name,
                        'amount': str(payment['amount']),
                        'checkout_url': payment['checkout_url']
                    }
                    for payment in payment_results['payments']
                ]

                # If single supplier, redirect directly to Chapa
                if len(payment_results['payments']) == 1:
                    checkout_url = payment_results['payments'][0]['checkout_url']
                    return redirect(checkout_url)
                else:
                    # Multiple suppliers - show payment selection page
                    return redirect('payment_selection')
            else:
                # Handle errors
                error_messages = []
                for error in payment_results['errors']:
                    if 'supplier' in error:
                        error_messages.append(f"Error with {error['supplier'].name}: {error['error']}")
                    else:
                        error_messages.append(f"Error: {error['error']}")

                for msg in error_messages:
                    messages.error(request, msg)

                return redirect('order_confirmation')
            
    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}")
        messages.error(request, 'An error occurred while initiating payment. Please try again.')
        return redirect('order_confirmation')


@login_required
@user_passes_test(is_head_manager)
def payment_selection(request):
    """
    Show payment selection page for multiple suppliers
    """
    payment_transactions = request.session.get('payment_transactions', [])
    
    if not payment_transactions:
        messages.error(request, 'No payment transactions found.')
        return redirect('cart_view')
    
    context = {
        'payment_transactions': payment_transactions,
        'total_amount': sum(float(tx['amount']) for tx in payment_transactions)
    }
    
    return render(request, 'payments/payment_selection.html', context)


@login_required
@user_passes_test(is_head_manager)
def payment_success(request):
    """
    Handle successful payment return from Chapa
    Enhanced to address common Chapa return URL issues
    """
    # Extract tx_ref from query parameters (handle both tx_ref and transaction_id)
    tx_ref = request.GET.get('tx_ref') or request.GET.get('transaction_id')

    # Debug logging for return URL parameters
    logger.info(f"Payment success callback - Query params: {dict(request.GET)}")

    # Validation 1: Check if tx_ref is present
    if not tx_ref:
        logger.error("Payment success callback missing tx_ref parameter")
        logger.error(f"Available query parameters: {dict(request.GET)}")

        # Try to find the most recent pending transaction for this user as fallback
        try:
            recent_transaction = ChapaTransaction.objects.filter(
                user=request.user,
                status='pending'
            ).order_by('-created_at').first()

            if recent_transaction:
                logger.info(f"Using most recent pending transaction as fallback: {recent_transaction.chapa_tx_ref}")
                tx_ref = recent_transaction.chapa_tx_ref
                messages.warning(request, 'Payment completed, but reference was missing. Using most recent transaction.')
            else:
                messages.error(request, 'Invalid payment reference. Missing transaction reference.')
                return redirect('cart_view')
        except Exception as e:
            logger.error(f"Error finding fallback transaction: {str(e)}")
            messages.error(request, 'Invalid payment reference. Missing transaction reference.')
            return redirect('cart_view')

    # Validation 2: Clean and validate tx_ref format
    tx_ref = tx_ref.strip()
    if not tx_ref or len(tx_ref) < 5:
        logger.error(f"Payment success callback with invalid tx_ref format: '{tx_ref}'")
        messages.error(request, 'Invalid payment reference format.')
        return redirect('cart_view')

    logger.info(f"Processing payment success for tx_ref: {tx_ref}")

    try:
        # Validation 3: Get the transaction and verify ownership
        transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref, user=request.user)

        # Force update transaction status to success since Chapa redirected here
        if transaction.status != 'success':
            transaction.status = 'success'
            transaction.paid_at = timezone.now()
            transaction.save()

            # Update purchase order payment status
            if hasattr(transaction, 'purchase_order_payment'):
                order_payment = transaction.purchase_order_payment
                if order_payment.status in ['initial', 'payment_pending']:
                    order_payment.status = 'payment_confirmed'
                    order_payment.payment_confirmed_at = timezone.now()
                    order_payment.save()

                    logger.info(f"Purchase order confirmed via payment success: {tx_ref} - Items: {len(order_payment.order_items)}")

                order_payment.update_status_from_payment()

            # Create transaction records for successful payment
            from .transaction_service import PaymentTransactionService
            transaction_result = PaymentTransactionService.create_transaction_from_payment(transaction)

            if transaction_result['success']:
                logger.info(f"Transaction records created for payment {tx_ref}")
            else:
                logger.error(f"Failed to create transaction records for payment {tx_ref}: {transaction_result.get('error')}")

            # Send receipt email to customer
            try:
                from users.email_service import email_service
                order_payment = transaction.purchase_order_payment if hasattr(transaction, 'purchase_order_payment') else None
                email_result = email_service.send_purchase_order_receipt_email(transaction, order_payment)

                if email_result[0]:  # Success
                    logger.info(f"Receipt email sent successfully for transaction {tx_ref}")
                else:
                    logger.error(f"Failed to send receipt email for transaction {tx_ref}: {email_result[1]}")
                    # Don't show error to user as payment was successful

            except Exception as e:
                logger.error(f"Error sending receipt email for transaction {tx_ref}: {str(e)}")
                # Don't show error to user as payment was successful

            # Log payment completion for payment history
            logger.info(f"Payment completed successfully: {tx_ref} - Amount: {transaction.amount} ETB - Supplier: {transaction.supplier.name} - Customer: {request.user.get_full_name() or request.user.username}")

        # Clear cart items for this supplier
        cart = Cart(request)

        messages.success(
            request,
            f'Payment successful! Your order with {transaction.supplier.name} '
            f'for ETB {transaction.amount} has been confirmed. Check Payment History for details.'
        )

        # Check if all payments are complete
        payment_transactions = request.session.get('payment_transactions', [])
        if payment_transactions:
            all_complete = True
            completed_suppliers = []
            total_amount = 0

            for tx_data in payment_transactions:
                try:
                    tx = ChapaTransaction.objects.get(chapa_tx_ref=tx_data['tx_ref'])
                    if tx.is_successful:
                        completed_suppliers.append(tx.supplier.name)
                        total_amount += tx.amount
                    else:
                        all_complete = False
                        break
                except ChapaTransaction.DoesNotExist:
                    all_complete = False
                    break

            if all_complete:
                # Clear cart and session data
                cart.clear()
                del request.session['payment_transactions']

                # Enhanced success message with payment history details
                supplier_list = ', '.join(completed_suppliers)
                messages.success(request, f'All payments completed successfully! Total: ETB {total_amount} to {len(completed_suppliers)} supplier(s): {supplier_list}. View details in Payment History.')
                return redirect('payment_history')

        # Redirect to payment completed page for individual transaction
        return redirect('payment_completed', tx_ref=tx_ref)

    except ChapaTransaction.DoesNotExist:
        logger.error(f"Transaction not found: {tx_ref}")
        messages.error(request, 'Payment transaction not found.')
        return redirect('cart_view')
    except Exception as e:
        logger.error(f"Error processing payment success: {str(e)}")
        messages.error(request, 'An error occurred while processing your payment.')
        return redirect('cart_view')


@login_required
@user_passes_test(is_head_manager)
def payment_completed(request, tx_ref):
    """
    Display payment completed page with transaction details and order summary
    """
    from .transaction_service import PaymentTransactionService

    try:
        # Process payment completion and create transaction records
        result = PaymentTransactionService.process_payment_completion(tx_ref, request.user)

        if not result['success']:
            messages.error(request, f"Payment processing error: {result['error']}")
            return redirect('payment_status', tx_ref=tx_ref)

        # Get the processed data
        chapa_transaction = result['chapa_transaction']
        display_data = result['display_data']
        transaction_result = result['transaction_result']

        # Get order items if available
        order_items = []
        if hasattr(chapa_transaction, 'purchase_order_payment'):
            order_payment = chapa_transaction.purchase_order_payment
            order_items = order_payment.order_items or []

        context = {
            'transaction': chapa_transaction,
            'display_data': display_data,
            'order_items': order_items,
            'transaction_created': transaction_result.get('success', False),
            'transaction_record': transaction_result.get('transaction'),
            'page_title': 'Payment Completed'
        }

        return render(request, 'payments/payment_completed.html', context)

    except Exception as e:
        logger.error(f"Error in payment_completed view: {str(e)}")
        messages.error(request, 'An error occurred while processing your payment. Please contact support.')
        return redirect('payment_history')


@login_required
@user_passes_test(is_head_manager)
def payment_status(request, tx_ref):
    """
    Show payment status page
    """
    try:
        # Try to get transaction from database
        try:
            transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref, user=request.user)

            context = {
                'transaction': transaction,
                'order_payment': getattr(transaction, 'purchase_order_payment', None),
                'is_real_transaction': True
            }

        except ChapaTransaction.DoesNotExist:
            # Transaction not found - this is likely a mock/test transaction
            context = {
                'tx_ref': tx_ref,
                'transaction': None,
                'order_payment': None,
                'is_real_transaction': False,
                'error_message': 'This appears to be a test transaction. The payment system is currently in demo mode.',
                'demo_mode': True
            }

        return render(request, 'payments/payment_status.html', context)

    except Exception as e:
        logger.error(f"Error showing payment status: {str(e)}")

        # If database tables don't exist, show demo mode message
        context = {
            'tx_ref': tx_ref,
            'transaction': None,
            'order_payment': None,
            'is_real_transaction': False,
            'error_message': 'Payment system is in demo mode. Database tables are not yet configured.',
            'demo_mode': True
        }

        return render(request, 'payments/payment_status.html', context)





@login_required
@user_passes_test(is_head_manager)
def payment_methods_info(request):
    """
    Display available payment methods information
    """
    from .chapa_client import ChapaClient

    client = ChapaClient()
    payment_methods = client.get_supported_payment_methods()

    context = {
        'payment_methods': payment_methods,
        'total_methods': (
            len(payment_methods['mobile_wallets']) +
            len(payment_methods['bank_cards']) +
            len(payment_methods['bank_transfers']) +
            len(payment_methods['international'])
        )
    }

    return render(request, 'payments/payment_methods_info.html', context)


@login_required
def download_payment_receipt(request, tx_ref):
    """
    Download payment receipt as PDF
    """
    try:
        # Get the transaction
        transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref)

        # Check permissions - only the customer or supplier can download
        if request.user != transaction.user and request.user.email != transaction.supplier.email:
            messages.error(request, "You don't have permission to download this receipt.")
            return redirect('payment_history')

        # Only allow download for successful payments
        if transaction.status != 'success':
            messages.error(request, "Receipt is only available for successful payments.")
            return redirect('payment_history')

        # Generate and return PDF receipt
        from .receipt_service import receipt_service
        return receipt_service.generate_payment_receipt_pdf(transaction)

    except ChapaTransaction.DoesNotExist:
        messages.error(request, "Transaction not found.")
        return redirect('payment_history')
    except Exception as e:
        logger.error(f"Error downloading receipt for {tx_ref}: {str(e)}")
        messages.error(request, "Unable to generate receipt. Please try again later.")
        return redirect('payment_history')


@login_required
def download_order_invoice(request, order_id):
    """
    Download purchase order invoice as PDF
    """
    try:
        # Get the order payment
        order_payment = PurchaseOrderPayment.objects.get(id=order_id)

        # Check permissions - only the customer or supplier can download
        if request.user != order_payment.user and request.user.email != order_payment.supplier.email:
            messages.error(request, "You don't have permission to download this invoice.")
            return redirect('payment_history')

        # Only allow download for confirmed payments
        if order_payment.status not in ['payment_confirmed', 'in_transit', 'delivered']:
            messages.error(request, "Invoice is only available for confirmed orders.")
            return redirect('payment_history')

        # Generate and return PDF invoice
        from .receipt_service import receipt_service
        return receipt_service.generate_purchase_order_invoice_pdf(order_payment)

    except PurchaseOrderPayment.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('payment_history')
    except Exception as e:
        logger.error(f"Error downloading invoice for order {order_id}: {str(e)}")
        messages.error(request, "Unable to generate invoice. Please try again later.")
        return redirect('payment_history')


@csrf_exempt
def chapa_webhook(request):
    """
    Handle Chapa webhook notifications
    Supports POST (for actual webhooks), GET (for verification), and OPTIONS (for CORS)
    """
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Chapa-Signature'
        return response

    # Handle GET request (verification or callback)
    if request.method == 'GET':
        # Extract parameters from URL
        tx_ref = request.GET.get('trx_ref')
        status = request.GET.get('status', '').lower()

        if tx_ref and status:
            logger.info(f"Webhook GET request: {tx_ref} - {status}")

            # Update transaction status
            try:
                transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref)

                if status == 'success':
                    transaction.status = 'success'
                    transaction.paid_at = timezone.now()

                    # Send receipt email for successful payment
                    try:
                        from users.email_service import email_service
                        order_payment = transaction.purchase_order_payment if hasattr(transaction, 'purchase_order_payment') else None
                        email_result = email_service.send_purchase_order_receipt_email(transaction, order_payment)

                        if email_result[0]:  # Success
                            logger.info(f"Receipt email sent successfully for webhook transaction {tx_ref}")
                        else:
                            logger.error(f"Failed to send receipt email for webhook transaction {tx_ref}: {email_result[1]}")

                    except Exception as e:
                        logger.error(f"Error sending receipt email for webhook transaction {tx_ref}: {str(e)}")

                elif status in ['failed', 'cancelled']:
                    transaction.status = 'failed'
                else:
                    transaction.status = 'pending'

                transaction.save()

                # Update related purchase order payment
                if hasattr(transaction, 'purchase_order_payment'):
                    transaction.purchase_order_payment.update_status_from_payment()

                logger.info(f"Transaction updated via GET webhook: {tx_ref} - {status}")
                return HttpResponse("OK")

            except ChapaTransaction.DoesNotExist:
                logger.error(f"Transaction not found for GET webhook: {tx_ref}")
                return HttpResponseBadRequest("Transaction not found")

        return HttpResponse("OK")

    # Handle POST request (standard webhook)
    if request.method != 'POST':
        return HttpResponseNotAllowed(['GET', 'POST', 'OPTIONS'])

    try:
        # Get raw payload
        payload = request.body.decode('utf-8')
        signature = request.headers.get('Chapa-Signature', '')
        
        # Log webhook
        webhook_log = PaymentWebhookLog.objects.create(
            webhook_data=json.loads(payload),
            signature=signature
        )
        
        # Verify signature (if configured)
        from .chapa_client import ChapaClient
        client = ChapaClient()
        
        if not client.verify_webhook_signature(payload, signature):
            logger.warning(f"Invalid webhook signature: {signature}")
            webhook_log.processing_error = "Invalid signature"
            webhook_log.save()
            return HttpResponseBadRequest("Invalid signature")
        
        # Parse webhook data
        webhook_data = json.loads(payload)
        tx_ref = webhook_data.get('tx_ref')
        status = webhook_data.get('status', '').lower()
        
        if not tx_ref:
            logger.error("Webhook missing tx_ref")
            webhook_log.processing_error = "Missing tx_ref"
            webhook_log.save()
            return HttpResponseBadRequest("Missing tx_ref")
        
        # Find and update transaction
        try:
            transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref)
            webhook_log.transaction = transaction
            
            # Update transaction status
            if status == 'success':
                transaction.status = 'success'
                transaction.paid_at = timezone.now()

                # Send receipt email for successful payment
                try:
                    from users.email_service import email_service
                    order_payment = transaction.purchase_order_payment if hasattr(transaction, 'purchase_order_payment') else None
                    email_result = email_service.send_purchase_order_receipt_email(transaction, order_payment)

                    if email_result[0]:  # Success
                        logger.info(f"Receipt email sent successfully for POST webhook transaction {tx_ref}")
                    else:
                        logger.error(f"Failed to send receipt email for POST webhook transaction {tx_ref}: {email_result[1]}")

                except Exception as e:
                    logger.error(f"Error sending receipt email for POST webhook transaction {tx_ref}: {str(e)}")

            elif status in ['failed', 'cancelled']:
                transaction.status = 'failed'
            else:
                transaction.status = 'pending'

            transaction.webhook_data = webhook_data
            transaction.save()

            # Update related purchase order payment
            if hasattr(transaction, 'purchase_order_payment'):
                transaction.purchase_order_payment.update_status_from_payment()
            
            webhook_log.processed = True
            webhook_log.processed_at = timezone.now()
            webhook_log.save()
            
            logger.info(f"Webhook processed successfully: {tx_ref} - {status}")
            return HttpResponse("OK")
            
        except ChapaTransaction.DoesNotExist:
            logger.error(f"Transaction not found for webhook: {tx_ref}")
            webhook_log.processing_error = f"Transaction not found: {tx_ref}"
            webhook_log.save()
            return HttpResponseBadRequest("Transaction not found")
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        if 'webhook_log' in locals():
            webhook_log.processing_error = str(e)
            webhook_log.save()
        return HttpResponseBadRequest("Webhook processing error")


@login_required
@user_passes_test(is_head_manager)
def payment_history(request):
    """
    Show payment history for the user with filtering and pagination
    """
    try:
        from django.core.paginator import Paginator
        from django.utils import timezone
        from datetime import datetime

        # Get filter parameters
        status_filter = request.GET.get('status', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        # Start with user's transactions
        transactions = ChapaTransaction.objects.filter(user=request.user)

        # Apply filters
        if status_filter:
            transactions = transactions.filter(status=status_filter)

        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                transactions = transactions.filter(created_at__date__gte=date_from_obj)
            except ValueError:
                pass

        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                transactions = transactions.filter(created_at__date__lte=date_to_obj)
            except ValueError:
                pass

        # Order by most recent first
        transactions = transactions.order_by('-created_at')

        # Pagination
        paginator = Paginator(transactions, 10)  # Show 10 transactions per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'transactions': page_obj,
            'status_filter': status_filter,
            'date_from': date_from,
            'date_to': date_to,
            'is_success_selected': status_filter == 'success',
            'is_pending_selected': status_filter == 'pending',
            'is_failed_selected': status_filter == 'failed',
        }

        return render(request, 'payments/payment_history.html', context)

    except Exception as e:
        # If database tables don't exist yet, show empty state
        messages.info(request, 'Payment history is not available yet. Database tables are being set up.')
        context = {
            'transactions': [],
            'status_filter': '',
            'date_from': '',
            'date_to': '',
            'is_success_selected': False,
            'is_pending_selected': False,
            'is_failed_selected': False,
        }
        return render(request, 'payments/payment_history.html', context)
