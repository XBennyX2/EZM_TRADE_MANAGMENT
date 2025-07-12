import logging
from django.utils import timezone
from .models import ChapaTransaction, PaymentWebhookLog
from .services import ChapaPaymentService

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Utility class for processing Chapa webhooks
    """
    
    def __init__(self):
        self.payment_service = ChapaPaymentService()
    
    def process_webhook_data(self, webhook_data, signature=None):
        """
        Process webhook data and update transaction status
        
        Args:
            webhook_data (dict): Webhook payload data
            signature (str): Webhook signature for verification
        
        Returns:
            dict: Processing result
        """
        try:
            # Extract transaction reference
            tx_ref = webhook_data.get('tx_ref')
            status = webhook_data.get('status', '').lower()
            
            if not tx_ref:
                return {
                    'success': False,
                    'error': 'Missing transaction reference in webhook data'
                }
            
            # Find transaction
            try:
                transaction = ChapaTransaction.objects.get(chapa_tx_ref=tx_ref)
            except ChapaTransaction.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Transaction not found: {tx_ref}'
                }
            
            # Update transaction status based on webhook
            old_status = transaction.status
            
            if status == 'success':
                transaction.status = 'success'
                if not transaction.paid_at:
                    transaction.paid_at = timezone.now()
            elif status in ['failed', 'cancelled']:
                transaction.status = 'failed'
            elif status == 'pending':
                transaction.status = 'pending'
            else:
                logger.warning(f"Unknown status in webhook: {status}")
                transaction.status = 'pending'
            
            # Update webhook data
            transaction.webhook_data = webhook_data
            transaction.save()
            
            # Update related purchase order payment
            if hasattr(transaction, 'purchase_order_payment'):
                transaction.purchase_order_payment.update_status_from_payment()
            
            logger.info(
                f"Webhook processed: {tx_ref} - Status changed from {old_status} to {transaction.status}"
            )
            
            return {
                'success': True,
                'transaction': transaction,
                'old_status': old_status,
                'new_status': transaction.status,
                'message': f'Transaction {tx_ref} updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reprocess_failed_webhooks(self, limit=100):
        """
        Reprocess failed webhook logs
        
        Args:
            limit (int): Maximum number of webhooks to reprocess
        
        Returns:
            dict: Reprocessing results
        """
        failed_webhooks = PaymentWebhookLog.objects.filter(
            processed=False,
            processing_error__isnull=False
        ).order_by('created_at')[:limit]
        
        results = {
            'processed': 0,
            'failed': 0,
            'errors': []
        }
        
        for webhook_log in failed_webhooks:
            try:
                # Attempt to reprocess
                result = self.process_webhook_data(webhook_log.webhook_data)
                
                if result['success']:
                    webhook_log.processed = True
                    webhook_log.processed_at = timezone.now()
                    webhook_log.processing_error = None
                    webhook_log.save()
                    results['processed'] += 1
                    logger.info(f"Reprocessed webhook {webhook_log.id} successfully")
                else:
                    webhook_log.processing_error = result['error']
                    webhook_log.save()
                    results['failed'] += 1
                    results['errors'].append(f"Webhook {webhook_log.id}: {result['error']}")
                    
            except Exception as e:
                error_msg = f"Error reprocessing webhook {webhook_log.id}: {str(e)}"
                webhook_log.processing_error = error_msg
                webhook_log.save()
                results['failed'] += 1
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        return results
    
    def verify_transaction_status(self, tx_ref):
        """
        Verify transaction status directly with Chapa API
        
        Args:
            tx_ref (str): Transaction reference
        
        Returns:
            dict: Verification result
        """
        return self.payment_service.verify_payment(tx_ref)
    
    def sync_pending_transactions(self, hours_old=1):
        """
        Sync pending transactions that are older than specified hours
        
        Args:
            hours_old (int): Minimum age in hours for transactions to sync
        
        Returns:
            dict: Sync results
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=hours_old)
        
        pending_transactions = ChapaTransaction.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        results = {
            'synced': 0,
            'failed': 0,
            'errors': []
        }
        
        for transaction in pending_transactions:
            try:
                verification_result = self.verify_transaction_status(transaction.chapa_tx_ref)
                
                if verification_result['success']:
                    results['synced'] += 1
                    logger.info(f"Synced transaction {transaction.chapa_tx_ref}")
                else:
                    results['failed'] += 1
                    error_msg = f"Failed to sync {transaction.chapa_tx_ref}: {verification_result.get('error')}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                error_msg = f"Error syncing transaction {transaction.chapa_tx_ref}: {str(e)}"
                results['failed'] += 1
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        return results


def create_webhook_log(webhook_data, signature=None, transaction=None):
    """
    Create a webhook log entry
    
    Args:
        webhook_data (dict): Webhook payload
        signature (str): Webhook signature
        transaction (ChapaTransaction): Related transaction if found
    
    Returns:
        PaymentWebhookLog: Created webhook log
    """
    return PaymentWebhookLog.objects.create(
        webhook_data=webhook_data,
        signature=signature,
        transaction=transaction
    )


def get_webhook_stats():
    """
    Get webhook processing statistics
    
    Returns:
        dict: Webhook statistics
    """
    total_webhooks = PaymentWebhookLog.objects.count()
    processed_webhooks = PaymentWebhookLog.objects.filter(processed=True).count()
    failed_webhooks = PaymentWebhookLog.objects.filter(
        processed=False, 
        processing_error__isnull=False
    ).count()
    pending_webhooks = PaymentWebhookLog.objects.filter(
        processed=False, 
        processing_error__isnull=True
    ).count()
    
    return {
        'total': total_webhooks,
        'processed': processed_webhooks,
        'failed': failed_webhooks,
        'pending': pending_webhooks,
        'success_rate': (processed_webhooks / total_webhooks * 100) if total_webhooks > 0 else 0
    }
