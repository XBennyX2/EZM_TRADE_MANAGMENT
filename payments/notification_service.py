"""
Supplier notification service for payment-related events
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal

logger = logging.getLogger(__name__)


class SupplierNotificationService:
    """
    Service for sending email notifications to suppliers about payment events
    """
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ezmtrade.com')
        self.company_name = "EZM Trade Management"
    
    def send_payment_confirmation_notification(self, transaction, order_payment=None):
        """
        Send notification to supplier when payment is confirmed
        
        Args:
            transaction: ChapaTransaction instance
            order_payment: PurchaseOrderPayment instance (optional)
        """
        try:
            supplier = transaction.supplier
            user = transaction.user
            
            # Prepare context for email template
            context = {
                'supplier': supplier,
                'customer': user,
                'transaction': transaction,
                'order_payment': order_payment,
                'company_name': self.company_name,
                'payment_amount': transaction.amount,
                'currency': transaction.currency,
                'transaction_ref': transaction.chapa_tx_ref,
                'payment_date': transaction.paid_at or transaction.created_at,
                'order_items': order_payment.order_items if order_payment else [],
                'estimated_delivery': self._calculate_estimated_delivery(),
            }
            
            # Render email templates
            subject = f"Payment Confirmed - Order from {user.get_full_name() or user.username}"
            
            # HTML email
            html_content = render_to_string(
                'payments/emails/supplier_payment_confirmation.html',
                context
            )
            
            # Plain text email
            text_content = render_to_string(
                'payments/emails/supplier_payment_confirmation.txt',
                context
            )
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[supplier.email],
                cc=[user.email] if user.email else []
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Payment confirmation email sent to supplier {supplier.name} ({supplier.email})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment confirmation email to supplier {supplier.name}: {str(e)}")
            return False
    
    def send_purchase_order_notification(self, purchase_order):
        """
        Send notification to supplier when purchase order is created
        
        Args:
            purchase_order: PurchaseOrder instance
        """
        try:
            supplier = purchase_order.supplier
            user = purchase_order.user
            
            context = {
                'supplier': supplier,
                'customer': user,
                'purchase_order': purchase_order,
                'company_name': self.company_name,
                'order_date': purchase_order.created_at,
                'order_status': purchase_order.get_status_display(),
                'total_amount': purchase_order.total_amount,
                'estimated_delivery': self._calculate_estimated_delivery(),
                'order_items': self._get_order_items_from_purchase_order(purchase_order),
            }
            
            subject = f"New Purchase Order #{purchase_order.id} from {user.get_full_name() or user.username}"
            
            # HTML email
            html_content = render_to_string(
                'payments/emails/supplier_purchase_order.html',
                context
            )
            
            # Plain text email
            text_content = render_to_string(
                'payments/emails/supplier_purchase_order.txt',
                context
            )
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[supplier.email],
                cc=[user.email] if user.email else []
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Purchase order notification email sent to supplier {supplier.name} ({supplier.email})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send purchase order email to supplier {supplier.name}: {str(e)}")
            return False
    
    def send_payment_status_change_notification(self, transaction, old_status, new_status):
        """
        Send notification when payment status changes
        
        Args:
            transaction: ChapaTransaction instance
            old_status: Previous payment status
            new_status: New payment status
        """
        try:
            supplier = transaction.supplier
            user = transaction.user
            
            # Only send notifications for significant status changes
            significant_changes = [
                ('pending', 'success'),
                ('pending', 'failed'),
                ('success', 'failed'),  # Rare but possible
            ]
            
            if (old_status, new_status) not in significant_changes:
                return True
            
            context = {
                'supplier': supplier,
                'customer': user,
                'transaction': transaction,
                'company_name': self.company_name,
                'old_status': old_status,
                'new_status': new_status,
                'status_display': transaction.get_status_display(),
                'transaction_ref': transaction.chapa_tx_ref,
                'payment_amount': transaction.amount,
                'currency': transaction.currency,
                'status_change_date': timezone.now(),
            }
            
            subject = f"Payment Status Update - {transaction.chapa_tx_ref}"
            
            # HTML email
            html_content = render_to_string(
                'payments/emails/supplier_payment_status_change.html',
                context
            )
            
            # Plain text email
            text_content = render_to_string(
                'payments/emails/supplier_payment_status_change.txt',
                context
            )
            
            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[supplier.email],
                cc=[user.email] if user.email else []
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Payment status change email sent to supplier {supplier.name} ({supplier.email})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment status change email to supplier {supplier.name}: {str(e)}")
            return False
    
    def _calculate_estimated_delivery(self):
        """
        Calculate estimated delivery date (business logic can be customized)
        """
        from datetime import timedelta
        return timezone.now().date() + timedelta(days=7)  # Default 7 days
    
    def _get_order_items_from_purchase_order(self, purchase_order):
        """
        Extract order items from purchase order
        """
        # This would depend on how order items are stored in the purchase order
        # For now, return empty list - this should be customized based on your model structure
        return []
    
    def send_bulk_notification(self, transactions, notification_type='payment_confirmation'):
        """
        Send bulk notifications for multiple transactions
        
        Args:
            transactions: List of ChapaTransaction instances
            notification_type: Type of notification to send
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for transaction in transactions:
            try:
                if notification_type == 'payment_confirmation':
                    success = self.send_payment_confirmation_notification(transaction)
                elif notification_type == 'status_change':
                    # This would need additional parameters for status change
                    success = True  # Placeholder
                else:
                    success = False
                
                if success:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Transaction {transaction.chapa_tx_ref}: {str(e)}")
        
        return results

    def send_delivery_confirmation_notification(self, delivery_confirmation):
        """
        Send notification when delivery is confirmed by Head Manager
        """
        try:
            purchase_order = delivery_confirmation.purchase_order
            supplier = purchase_order.supplier

            # Email context
            context = {
                'supplier': supplier,
                'purchase_order': purchase_order,
                'delivery_confirmation': delivery_confirmation,
                'confirmed_by': delivery_confirmation.confirmed_by,
                'company_name': self.company_name,
                'delivery_date': delivery_confirmation.confirmed_at,
                'delivery_condition': delivery_confirmation.get_delivery_condition_display(),
                'all_items_received': delivery_confirmation.all_items_received,
                'delivery_notes': delivery_confirmation.delivery_notes,
            }

            subject = f"Delivery Confirmed - Order #{purchase_order.order_number}"

            # HTML email
            html_content = render_to_string(
                'payments/emails/delivery_confirmed.html',
                context
            )

            # Plain text email
            text_content = render_to_string(
                'payments/emails/delivery_confirmed.txt',
                context
            )

            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[supplier.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            logger.info(f"Delivery confirmation notification sent to {supplier.email} for order {purchase_order.order_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send delivery confirmation notification: {str(e)}")
            return False

    def send_delivery_issue_notification(self, issue_report):
        """
        Send notification when delivery issues are reported by Head Manager
        """
        try:
            purchase_order = issue_report.purchase_order
            supplier = purchase_order.supplier

            # Email context
            context = {
                'supplier': supplier,
                'purchase_order': purchase_order,
                'issue_report': issue_report,
                'reported_by': issue_report.reported_by,
                'company_name': self.company_name,
                'issue_type': issue_report.get_issue_type_display(),
                'severity': issue_report.get_severity_display(),
                'issue_title': issue_report.title,
                'issue_description': issue_report.description,
                'reported_date': issue_report.reported_at,
                'affected_items': issue_report.affected_items.all(),
            }

            subject = f"URGENT: Delivery Issue Reported - Order #{purchase_order.order_number}"

            # HTML email
            html_content = render_to_string(
                'payments/emails/delivery_issue_reported.html',
                context
            )

            # Plain text email
            text_content = render_to_string(
                'payments/emails/delivery_issue_reported.txt',
                context
            )

            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[supplier.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            logger.info(f"Delivery issue notification sent to {supplier.email} for order {purchase_order.order_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send delivery issue notification: {str(e)}")
            return False

    def send_order_status_change_notification(self, purchase_order, previous_status, new_status, changed_by):
        """
        Send notification when order status changes (e.g., payment confirmed -> in transit)
        """
        try:
            supplier = purchase_order.supplier

            # Email context
            context = {
                'supplier': supplier,
                'purchase_order': purchase_order,
                'previous_status': previous_status,
                'new_status': new_status,
                'changed_by': changed_by,
                'company_name': self.company_name,
                'change_date': timezone.now(),
            }

            subject = f"Order Status Update - #{purchase_order.order_number} is now {new_status.title()}"

            # HTML email
            html_content = render_to_string(
                'payments/emails/order_status_changed.html',
                context
            )

            # Plain text email
            text_content = render_to_string(
                'payments/emails/order_status_changed.txt',
                context
            )

            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[supplier.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            logger.info(f"Order status change notification sent to {supplier.email} for order {purchase_order.order_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send order status change notification: {str(e)}")
            return False


# Global instance for easy access
supplier_notification_service = SupplierNotificationService()
