"""
Django management command to test email functionality

Usage:
    python manage.py test_email
    python manage.py test_email --email your@email.com
    python manage.py test_email --type user_creation
    python manage.py test_email --type otp
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.email_service import email_service
import random
import string

User = get_user_model()

class Command(BaseCommand):
    help = 'Test email functionality for EZM Trade Management System'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email address to send test emails to (default: test@example.com)'
        )
        
        parser.add_argument(
            '--type',
            type=str,
            choices=['all', 'config', 'user_creation', 'otp', 'password_reset'],
            default='all',
            help='Type of email test to run (default: all)'
        )

    def handle(self, *args, **options):
        email_address = options['email']
        test_type = options['type']
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🧪 Testing email functionality for EZM Trade Management System'
            )
        )
        self.stdout.write(f'📧 Test email address: {email_address}')
        self.stdout.write(f'🔧 Test type: {test_type}')
        self.stdout.write('')
        
        if test_type in ['all', 'config']:
            self.test_email_configuration()
        
        if test_type in ['all', 'user_creation']:
            self.test_user_creation_email(email_address)
        
        if test_type in ['all', 'otp']:
            self.test_otp_email(email_address)
        
        if test_type in ['all', 'password_reset']:
            self.test_password_reset_email(email_address)
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('✅ Email functionality testing completed!')
        )

    def test_email_configuration(self):
        """Test basic email configuration"""
        self.stdout.write('🔧 Testing email configuration...')
        
        success, message = email_service.test_email_configuration()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ {message}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'   ❌ {message}')
            )

    def test_user_creation_email(self, email_address):
        """Test user creation email"""
        self.stdout.write('👤 Testing user creation email...')
        
        # Create a mock user object for testing
        class MockUser:
            def __init__(self):
                self.username = f'testuser_{self.generate_random_string(6)}'
                self.first_name = 'Test'
                self.last_name = 'User'
                self.email = email_address
                self.role = 'store_manager'
            
            def get_role_display(self):
                return 'Store Manager'
        
        mock_user = MockUser()
        test_password = 'TempPass123!'
        
        success, message = email_service.send_user_creation_email(mock_user, test_password)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ {message}')
            )
            self.stdout.write(f'   📝 Test credentials: {mock_user.username} / {test_password}')
        else:
            self.stdout.write(
                self.style.ERROR(f'   ❌ {message}')
            )

    def test_otp_email(self, email_address):
        """Test OTP email"""
        self.stdout.write('🔐 Testing OTP email...')
        
        # Create a mock user object for testing
        class MockUser:
            def __init__(self):
                self.username = f'testuser_{self.generate_random_string(6)}'
                self.email = email_address
        
        mock_user = MockUser()
        test_otp = ''.join(random.choices(string.digits, k=6))
        
        success, message = email_service.send_otp_email(mock_user, test_otp)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ {message}')
            )
            self.stdout.write(f'   🔢 Test OTP: {test_otp}')
        else:
            self.stdout.write(
                self.style.ERROR(f'   ❌ {message}')
            )

    def test_password_reset_email(self, email_address):
        """Test password reset email"""
        self.stdout.write('🔑 Testing password reset email...')
        
        # Create a mock user object for testing
        class MockUser:
            def __init__(self):
                self.username = f'testuser_{self.generate_random_string(6)}'
                self.first_name = 'Test'
                self.last_name = 'User'
                self.email = email_address
        
        mock_user = MockUser()
        test_reset_link = 'http://127.0.0.1:8000/users/password-reset/confirm/abc123/'
        
        success, message = email_service.send_password_reset_email(mock_user, test_reset_link)
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ {message}')
            )
            self.stdout.write(f'   🔗 Test reset link: {test_reset_link}')
        else:
            self.stdout.write(
                self.style.ERROR(f'   ❌ {message}')
            )

    def generate_random_string(self, length):
        """Generate a random string of specified length"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
