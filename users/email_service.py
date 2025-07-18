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
        self.company_name = "EZM Trade Management"
        
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
                html_content = render_to_string('users/emails/password_reset.html', context)
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
