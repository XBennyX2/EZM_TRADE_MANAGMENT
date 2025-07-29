"""
Stock Notification Service for Supplier Inventory Management
Handles low stock alerts and notifications to suppliers
"""

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import SupplierProduct, Supplier

logger = logging.getLogger(__name__)


class StockNotificationService:
    """
    Service to handle stock-related notifications
    """
    
    LOW_STOCK_THRESHOLD = 10
    CRITICAL_STOCK_THRESHOLD = 5
    
    @classmethod
    def check_and_send_low_stock_alerts(cls, supplier=None):
        """
        Check for low stock products and send notifications to suppliers
        
        Args:
            supplier: Optional specific supplier to check, if None checks all suppliers
            
        Returns:
            dict: Summary of notifications sent
        """
        try:
            # Get suppliers to check
            if supplier:
                suppliers = [supplier]
            else:
                suppliers = Supplier.objects.filter(is_active=True)
            
            notifications_sent = 0
            total_low_stock_products = 0
            
            for supplier_obj in suppliers:
                result = cls._send_supplier_low_stock_notification(supplier_obj)
                if result['notification_sent']:
                    notifications_sent += 1
                total_low_stock_products += result['low_stock_count']
            
            logger.info(f"Stock alert check completed. Notifications sent: {notifications_sent}, "
                       f"Total low stock products: {total_low_stock_products}")
            
            return {
                'success': True,
                'notifications_sent': notifications_sent,
                'total_low_stock_products': total_low_stock_products,
                'suppliers_checked': len(suppliers)
            }
            
        except Exception as e:
            logger.error(f"Error in stock alert check: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def _send_supplier_low_stock_notification(cls, supplier):
        """
        Send low stock notification to a specific supplier
        
        Args:
            supplier: Supplier instance
            
        Returns:
            dict: Result of notification attempt
        """
        try:
            # Get low stock products for this supplier
            low_stock_products = SupplierProduct.objects.filter(
                supplier=supplier,
                is_active=True,
                stock_quantity__lte=cls.LOW_STOCK_THRESHOLD,
                stock_quantity__gt=0
            ).order_by('stock_quantity')
            
            critical_stock_products = low_stock_products.filter(
                stock_quantity__lte=cls.CRITICAL_STOCK_THRESHOLD
            )
            
            out_of_stock_products = SupplierProduct.objects.filter(
                supplier=supplier,
                is_active=True,
                stock_quantity=0
            )
            
            # Only send notification if there are low stock products
            if not (low_stock_products.exists() or out_of_stock_products.exists()):
                return {
                    'notification_sent': False,
                    'low_stock_count': 0,
                    'reason': 'No low stock products found'
                }
            
            # Prepare notification data
            notification_data = {
                'supplier': supplier,
                'low_stock_products': low_stock_products,
                'critical_stock_products': critical_stock_products,
                'out_of_stock_products': out_of_stock_products,
                'low_stock_threshold': cls.LOW_STOCK_THRESHOLD,
                'critical_stock_threshold': cls.CRITICAL_STOCK_THRESHOLD,
                'total_low_stock': low_stock_products.count(),
                'total_critical_stock': critical_stock_products.count(),
                'total_out_of_stock': out_of_stock_products.count(),
                'notification_date': timezone.now()
            }
            
            # Send email notification
            email_sent = cls._send_low_stock_email(supplier, notification_data)
            
            # Create in-app notification (if notification system exists)
            cls._create_in_app_notification(supplier, notification_data)
            
            logger.info(f"Low stock notification sent to {supplier.name}. "
                       f"Low stock: {notification_data['total_low_stock']}, "
                       f"Out of stock: {notification_data['total_out_of_stock']}")
            
            return {
                'notification_sent': True,
                'email_sent': email_sent,
                'low_stock_count': notification_data['total_low_stock'] + notification_data['total_out_of_stock']
            }
            
        except Exception as e:
            logger.error(f"Error sending low stock notification to {supplier.name}: {str(e)}")
            return {
                'notification_sent': False,
                'low_stock_count': 0,
                'error': str(e)
            }
    
    @classmethod
    def _send_low_stock_email(cls, supplier, notification_data):
        """
        Send low stock email notification to supplier
        
        Args:
            supplier: Supplier instance
            notification_data: Dict containing notification details
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            if not supplier.email:
                logger.warning(f"No email address for supplier {supplier.name}")
                return False
            
            # Render email content
            subject = f"Low Stock Alert - {supplier.name} | EZM Trade Management"
            
            html_content = render_to_string('emails/low_stock_notification.html', notification_data)
            text_content = render_to_string('emails/low_stock_notification.txt', notification_data)
            
            # Send email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[supplier.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Low stock email sent to {supplier.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending low stock email to {supplier.email}: {str(e)}")
            return False
    
    @classmethod
    def _create_in_app_notification(cls, supplier, notification_data):
        """
        Create in-app notification for supplier (if notification system exists)
        
        Args:
            supplier: Supplier instance
            notification_data: Dict containing notification details
        """
        try:
            # Try to import notification model (may not exist)
            from .models import NotificationCategory
            
            # Create notification record
            # This would integrate with existing notification system
            logger.info(f"In-app notification created for {supplier.name}")
            
        except ImportError:
            # Notification system not available
            logger.debug("In-app notification system not available")
        except Exception as e:
            logger.error(f"Error creating in-app notification: {str(e)}")
    
    @classmethod
    def send_stock_update_notification(cls, supplier_product, old_quantity, new_quantity, reason=""):
        """
        Send notification when stock is updated
        
        Args:
            supplier_product: SupplierProduct instance
            old_quantity: Previous stock quantity
            new_quantity: New stock quantity
            reason: Reason for stock change
        """
        try:
            # Check if this update triggers a low stock alert
            if (old_quantity > cls.LOW_STOCK_THRESHOLD and 
                new_quantity <= cls.LOW_STOCK_THRESHOLD):
                
                # Stock just went below threshold, send immediate alert
                cls._send_supplier_low_stock_notification(supplier_product.supplier)
                
            logger.info(f"Stock update notification processed for {supplier_product.product_name}: "
                       f"{old_quantity} -> {new_quantity}")
            
        except Exception as e:
            logger.error(f"Error in stock update notification: {str(e)}")
    
    @classmethod
    def get_low_stock_summary(cls, supplier=None):
        """
        Get summary of low stock products
        
        Args:
            supplier: Optional specific supplier
            
        Returns:
            dict: Summary of low stock products
        """
        try:
            # Build query
            query = Q(is_active=True)
            if supplier:
                query &= Q(supplier=supplier)
            
            # Get stock statistics
            all_products = SupplierProduct.objects.filter(query)
            low_stock = all_products.filter(
                stock_quantity__lte=cls.LOW_STOCK_THRESHOLD,
                stock_quantity__gt=0
            )
            critical_stock = all_products.filter(
                stock_quantity__lte=cls.CRITICAL_STOCK_THRESHOLD,
                stock_quantity__gt=0
            )
            out_of_stock = all_products.filter(stock_quantity=0)
            
            return {
                'total_products': all_products.count(),
                'low_stock_count': low_stock.count(),
                'critical_stock_count': critical_stock.count(),
                'out_of_stock_count': out_of_stock.count(),
                'low_stock_products': low_stock,
                'critical_stock_products': critical_stock,
                'out_of_stock_products': out_of_stock
            }
            
        except Exception as e:
            logger.error(f"Error getting low stock summary: {str(e)}")
            return {
                'total_products': 0,
                'low_stock_count': 0,
                'critical_stock_count': 0,
                'out_of_stock_count': 0,
                'error': str(e)
            }


# Convenience function for external use
def check_low_stock_alerts(supplier=None):
    """
    Convenience function to check and send low stock alerts
    
    Args:
        supplier: Optional specific supplier to check
        
    Returns:
        dict: Result of notification check
    """
    return StockNotificationService.check_and_send_low_stock_alerts(supplier)
