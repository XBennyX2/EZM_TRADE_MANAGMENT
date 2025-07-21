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

# SendGrid imports (optional)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

logger = logging.getLogger(__name__)

class EZMEmailService:
    """Enhanced email service with comprehensive error handling and logging"""

    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.company_name = "EZM Trade Management"
        self.sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.use_sendgrid_api = SENDGRID_AVAILABLE and self.sendgrid_api_key

        if self.use_sendgrid_api:
            self.sendgrid_client = SendGridAPIClient(api_key=self.sendgrid_api_key)
            logger.info("SendGrid API client initialized")
        else:
            logger.info("Using Django SMTP backend for email")

    def _send_email_via_sendgrid_api(self, to_email: str, subject: str, plain_content: str, html_content: str = None) -> Tuple[bool, str]:
        """Send email using SendGrid API directly"""
        try:
            from_email = From(self.from_email, self.company_name)
            to_email_obj = To(to_email)
            subject_obj = Subject(subject)
            plain_text_content = PlainTextContent(plain_content)

            # Create mail object
            if html_content:
                html_content_obj = HtmlContent(html_content)
                mail = Mail(from_email, to_email_obj, subject_obj, plain_text_content, html_content_obj)
            else:
                mail = Mail(from_email, to_email_obj, subject_obj, plain_text_content)

            # Send email
            response = self.sendgrid_client.send(mail)

            if response.status_code in [200, 201, 202]:
                logger.info(f"SendGrid API email sent successfully to {to_email} (status: {response.status_code})")
                return True, f"Email sent successfully via SendGrid API"
            else:
                logger.error(f"SendGrid API error: {response.status_code} - {response.body}")
                return False, f"SendGrid API error: {response.status_code}"

        except Exception as e:
            logger.error(f"SendGrid API exception: {e}")
            return False, f"SendGrid API exception: {e}"

    def _send_email_via_smtp(self, to_email: str, subject: str, plain_content: str, html_content: str = None) -> Tuple[bool, str]:
        """Send email using Django SMTP backend with network error handling"""
        try:
            if html_content:
                # Send HTML email with plain text fallback
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_content,
                    from_email=self.from_email,
                    to=[to_email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else:
                # Send plain text email
                send_mail(
                    subject=subject,
                    message=plain_content,
                    from_email=self.from_email,
                    recipient_list=[to_email],
                    fail_silently=False
                )

            logger.info(f"SMTP email sent successfully to {to_email}")
            return True, f"Email sent successfully via SMTP"

        except ConnectionError as e:
            logger.error(f"SMTP connection error: {e}")
            return False, f"Network connection error: {e}"
        except OSError as e:
            if "Network is unreachable" in str(e):
                logger.error(f"Network unreachable: {e}")
                return False, f"Network unreachable - check internet connection"
            else:
                logger.error(f"SMTP OS error: {e}")
                return False, f"SMTP OS error: {e}"
        except Exception as e:
            logger.error(f"SMTP email exception: {e}")
            return False, f"SMTP email exception: {e}"

    def send_email(self, to_email: str, subject: str, plain_content: str, html_content: str = None) -> Tuple[bool, str]:
        """Universal email sending method that tries SendGrid API first, then falls back to SMTP"""
        if self.use_sendgrid_api:
            success, message = self._send_email_via_sendgrid_api(to_email, subject, plain_content, html_content)
            if success:
                return success, message
            else:
                logger.warning(f"SendGrid API failed, falling back to SMTP: {message}")

        # Fallback to SMTP
        return self._send_email_via_smtp(to_email, subject, plain_content, html_content)

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
            
            # Send email using universal method
            success, message_result = self.send_email(user.email, subject, message, html_content)

            if success:
                logger.info(f"User creation email sent successfully to {user.email} for user {user.username}")
                return True, f"Welcome email sent to {user.email}"
            else:
                return False, message_result
            
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

            # Send email using universal method
            success, message_result = self.send_email(user.email, subject, message, html_content)

            if success:
                logger.info(f"Account reset email sent successfully to {user.email}")
                return True, f"Account reset email sent to {user.email}"
            else:
                return False, message_result

        except Exception as e:
            logger.error(f"Failed to send account reset email to {user.email}: {e}")
            return False, f"Failed to send account reset email: {e}"

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
