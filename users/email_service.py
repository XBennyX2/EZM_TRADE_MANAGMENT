"""
Enhanced Email Service for EZM Trade Management System

This module provides improved email functionality with better error handling,
logging, and template management for user-related emails.
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class EZMEmailService:
    """Enhanced email service with comprehensive error handling and logging"""

    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.company_name = getattr(settings, 'COMPANY_NAME', 'EZM Trade Management System')
        self.company_email = getattr(settings, 'COMPANY_EMAIL', settings.EMAIL_HOST_USER)
        
    def send_user_creation_email(self, user, password: str) -> Tuple[bool, str]:
        """
        Send welcome email to newly created user with login credentials
        
        Args:
            user: User instance
            password: Temporary password for the user
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            subject = f"Welcome to {self.company_name} - Account Created"
            
            # Prepare context for email template
            context = {
                'user': user,
                'password': password,
                'company_name': self.company_name,
                'login_url': 'http://127.0.0.1:8000/users/login/',
                'role_display': user.get_role_display(),
            }
            
            # Create plain text message
            message = f"""Dear {user.first_name} {user.last_name},

Your account has been created for {self.company_name}.

Login Details:
- Username: {user.username}
- Temporary Password: {password}
- Role: {user.get_role_display()}

Please login at: http://127.0.0.1:8000/users/login/

IMPORTANT: You will be required to change your password on first login for security purposes.

If you have any questions, please contact your administrator.

Best regards,
{self.company_name} Team"""

            # Try to render HTML template if it exists
            html_content = None
            try:
                html_content = render_to_string('users/emails/user_creation.html', context)
            except Exception as template_error:
                logger.warning(f"HTML template not found for user creation email: {template_error}")
            
            # Send email
            if html_content:
                # Send HTML email with plain text fallback
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=self.from_email,
                    to=[user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else:
                # Send plain text email
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.from_email,
                    recipient_list=[user.email],
                    fail_silently=False
                )
            
            logger.info(f"User creation email sent successfully to {user.email} for user {user.username}")
            return True, f"Welcome email sent to {user.email}"
            
        except Exception as e:
            error_msg = f"Failed to send user creation email to {user.email}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_password_reset_email(self, user, reset_link: str) -> Tuple[bool, str]:
        """
        Send password reset email to user
        
        Args:
            user: User instance
            reset_link: Password reset link
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            subject = f"{self.company_name} - Password Reset Request"
            
            context = {
                'user': user,
                'reset_link': reset_link,
                'company_name': self.company_name,
            }
            
            message = f"""Dear {user.first_name} {user.last_name},

You have requested to reset your password for your {self.company_name} account.

Please click the following link to reset your password:
{reset_link}

This link will expire in 24 hours for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
{self.company_name} Team"""

            # Try to render HTML template
            html_content = None
            try:
                html_content = render_to_string('templates/users/password_reset_email.html', context)
            except Exception as template_error:
                logger.warning(f"HTML template not found for password reset email: {template_error}")
            
            # Send email
            if html_content:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=self.from_email,
                    to=[user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.from_email,
                    recipient_list=[user.email],
                    fail_silently=False
                )
            
            logger.info(f"Password reset email sent successfully to {user.email}")
            return True, f"Password reset email sent to {user.email}"
            
        except Exception as e:
            error_msg = f"Failed to send password reset email to {user.email}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_otp_email(self, user, otp_code: str) -> Tuple[bool, str]:
        """
        Send OTP verification email to user
        
        Args:
            user: User instance
            otp_code: OTP code for verification
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            subject = f"{self.company_name} - Email Verification Code"
            
            context = {
                'user': user,
                'username': user.username,
                'otp': otp_code,
                'company_name': self.company_name,
            }
            
            message = f"""Hello {user.username},

Your OTP code for email verification is: {otp_code}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

Best regards,
{self.company_name} Team"""

            # Try to render HTML template
            html_content = None
            try:
                html_content = render_to_string('users/email_otp.html', context)
            except Exception as template_error:
                logger.warning(f"HTML template not found for OTP email: {template_error}")
            
            # Send email
            if html_content:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=self.from_email,
                    to=[user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.from_email,
                    recipient_list=[user.email],
                    fail_silently=False
                )
            
            logger.info(f"OTP email sent successfully to {user.email}")
            return True, f"OTP email sent to {user.email}"
            
        except Exception as e:
            error_msg = f"Failed to send OTP email to {user.email}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_role_change_notification(self, user, old_role: str, new_role: str) -> Tuple[bool, str]:
        """
        Send notification when user role is changed
        
        Args:
            user: User instance
            old_role: Previous role
            new_role: New role
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            subject = f"{self.company_name} - Role Change Notification"
            
            message = f"""Dear {user.first_name} {user.last_name},

Your role in {self.company_name} has been updated.

Role Change Details:
- Previous Role: {old_role}
- New Role: {new_role}
- Effective Date: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}

Please login to your account to access your new role features.

If you have any questions about this change, please contact your administrator.

Best regards,
{self.company_name} Team"""

            send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[user.email],
                fail_silently=False
            )
            
            logger.info(f"Role change notification sent to {user.email} (from {old_role} to {new_role})")
            return True, f"Role change notification sent to {user.email}"
            
        except Exception as e:
            error_msg = f"Failed to send role change notification to {user.email}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_account_reset_email(self, user, temporary_password: str, old_email: str, reset_by_user) -> Tuple[bool, str]:
        """
        Send account reset notification email with new temporary credentials

        Args:
            user: User instance whose account was reset
            temporary_password: New temporary password
            old_email: Previous email address
            reset_by_user: Admin user who performed the reset

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            subject = f"Account Reset - {self.company_name}"

            # Prepare context for email template
            context = {
                'user': user,
                'temporary_password': temporary_password,
                'old_email': old_email,
                'reset_by_user': reset_by_user,
                'company_name': self.company_name,
                'login_url': 'http://127.0.0.1:8000/users/login/',
                'role_display': user.get_role_display(),
            }

            # Create plain text message
            message = f"""Dear {user.first_name} {user.last_name},

Your account in {self.company_name} has been reset by an administrator.

Account Reset Details:
- Reset by: {reset_by_user.first_name} {reset_by_user.last_name} ({reset_by_user.username})
- Previous email: {old_email}
- New temporary email: {user.email}
- Temporary password: {temporary_password}
- Your role: {user.get_role_display()}

IMPORTANT SECURITY NOTICE:
1. This is a temporary password that must be changed on your first login
2. You will be required to set a new password before accessing the system
3. Please keep these credentials secure and do not share them

To access your account:
1. Go to: {context['login_url']}
2. Login with your new temporary email and password
3. You will be prompted to change your password immediately

If you have any questions or did not expect this account reset, please contact your system administrator immediately.

Best regards,
{self.company_name} Team"""

            # Try to render HTML template if it exists
            html_content = None
            try:
                html_content = render_to_string('users/emails/account_reset.html', context)
            except Exception as template_error:
                logger.warning(f"HTML template not found for account reset email: {template_error}")

            # Send email to the new temporary email
            if html_content:
                # Send HTML email with plain text fallback
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=self.from_email,
                    to=[user.email]  # Send to new temporary email
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else:
                # Send plain text email
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.from_email,
                    recipient_list=[user.email],  # Send to new temporary email
                    fail_silently=False
                )

            logger.info(f"Account reset email sent successfully to {user.email}")
            return True, f"Account reset email sent to {user.email}"

        except Exception as e:
            logger.error(f"Failed to send account reset email to {user.email}: {e}")
            return False, f"Failed to send account reset email: {e}"

    def send_purchase_order_receipt_email(self, transaction, order_payment=None) -> Tuple[bool, str]:
        """
        Send purchase order receipt email to customer after successful payment

        Args:
            transaction: ChapaTransaction instance
            order_payment: PurchaseOrderPayment instance (optional)

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            user = transaction.user
            supplier = transaction.supplier

            # Prepare context for email template
            context = {
                'user': user,
                'transaction': transaction,
                'order_payment': order_payment,
                'supplier': supplier,
                'company_name': self.company_name,
                'payment_amount': transaction.amount,
                'currency': transaction.currency,
                'transaction_ref': transaction.chapa_tx_ref,
                'payment_date': transaction.paid_at or transaction.created_at,
                'order_items': order_payment.order_items if order_payment else [],
                'customer_name': f"{transaction.customer_first_name} {transaction.customer_last_name}".strip(),
                'customer_email': transaction.customer_email,
                'customer_phone': transaction.customer_phone or 'Not provided',
            }

            subject = f"Purchase Order Receipt - {self.company_name}"

            # Create plain text message
            message = f"""Dear {context['customer_name']},

Thank you for your purchase! Your payment has been successfully processed.

Receipt Details:
- Transaction ID: {transaction.chapa_tx_ref}
- Payment Date: {context['payment_date'].strftime('%B %d, %Y at %I:%M %p')}
- Amount: {transaction.currency} {transaction.amount:,.2f}
- Supplier: {supplier.name}
- Payment Method: Chapa Payment Gateway

Customer Information:
- Name: {context['customer_name']}
- Email: {context['customer_email']}
- Phone: {context['customer_phone']}

Order Items:"""

            # Add order items to the message
            if context['order_items']:
                for item in context['order_items']:
                    # Handle price formatting safely
                    try:
                        price = float(item.get('price', 0))
                        total_price = float(item.get('total_price', 0))
                        message += f"""
- {item.get('product_name', 'N/A')}: Qty {item.get('quantity', 0)} @ {transaction.currency} {price:,.2f} each = {transaction.currency} {total_price:,.2f}"""
                    except (ValueError, TypeError):
                        message += f"""
- {item.get('product_name', 'N/A')}: Qty {item.get('quantity', 0)} @ {transaction.currency} {item.get('price', 0)} each = {transaction.currency} {item.get('total_price', 0)}"""
            else:
                message += "\n- Order details will be provided separately"

            message += f"""

Total Amount: {transaction.currency} {transaction.amount:,.2f}

Your order is now being processed and you will receive updates on delivery status.

You can download a detailed PDF receipt from your Payment History in the system.

If you have any questions about your order, please contact us.

Best regards,
{self.company_name} Team"""

            # Try to render HTML template if it exists
            html_content = None
            try:
                html_content = render_to_string('users/emails/purchase_order_receipt.html', context)
            except Exception as template_error:
                logger.warning(f"HTML template not found for purchase order receipt email: {template_error}")

            # Send email
            if html_content:
                # Send HTML email with plain text fallback
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=self.from_email,
                    to=[transaction.customer_email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else:
                # Send plain text email
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.from_email,
                    recipient_list=[transaction.customer_email],
                    fail_silently=False
                )

            logger.info(f"Purchase order receipt email sent successfully to {transaction.customer_email} for transaction {transaction.chapa_tx_ref}")
            return True, f"Receipt email sent to {transaction.customer_email}"

        except Exception as e:
            error_msg = f"Failed to send purchase order receipt email to {transaction.customer_email}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def test_email_configuration(self) -> Tuple[bool, str]:
        """
        Test email configuration by sending a test email

        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            test_subject = f"{self.company_name} - Email Configuration Test"
            test_message = f"""This is a test email to verify that the email configuration for {self.company_name} is working correctly.

Test Details:
- Timestamp: {timezone.now()}
- Email Backend: {settings.EMAIL_BACKEND}
- SMTP Host: {settings.EMAIL_HOST}
- From Email: {self.from_email}

If you receive this email, the email system is functioning properly.

Best regards,
{self.company_name} System"""

            result = send_mail(
                subject=test_subject,
                message=test_message,
                from_email=self.from_email,
                recipient_list=['test@example.com'],
                fail_silently=False
            )

            if result == 1:
                logger.info("Email configuration test successful")
                return True, "Email configuration test successful"
            else:
                logger.error("Email configuration test failed - no emails sent")
                return False, "Email configuration test failed"

        except Exception as e:
            error_msg = f"Email configuration test failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


# Global instance for easy access
email_service = EZMEmailService()
