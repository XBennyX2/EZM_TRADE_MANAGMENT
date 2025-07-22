# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('head_manager', 'Head Manager'),
        ('store_manager', 'Store Manager'),
        ('cashier', 'Cashier'),
        ('supplier', 'Supplier'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    store = models.ForeignKey('store.Store', on_delete=models.SET_NULL, null=True, blank=True) # Add this line
    is_first_login = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(unique=True)  # Make email unique


class LoginLog(models.Model):
    """Model to track user login activities for admin audit purposes"""

    LOGIN_STATUS_CHOICES = [
        ('success', 'Successful'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True,
                           help_text="User who attempted login (null for failed attempts with invalid username)")
    username_attempted = models.CharField(max_length=150, help_text="Username/email attempted during login")
    login_timestamp = models.DateTimeField(default=timezone.now)
    login_status = models.CharField(max_length=10, choices=LOGIN_STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, help_text="Browser/device information")
    user_role = models.CharField(max_length=20, blank=True, help_text="User role at time of login")
    failure_reason = models.CharField(max_length=100, blank=True, help_text="Reason for failed login")

    class Meta:
        ordering = ['-login_timestamp']
        verbose_name = "Login Log"
        verbose_name_plural = "Login Logs"

    def __str__(self):
        status_icon = "✓" if self.login_status == 'success' else "✗"
        return f"{status_icon} {self.username_attempted} - {self.login_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class AccountReset(models.Model):
    """Model to track admin account reset activities"""

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reset_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='account_resets_performed')
    reset_timestamp = models.DateTimeField(default=timezone.now)
    old_email = models.EmailField(help_text="Previous email before reset")
    new_email = models.EmailField(help_text="New temporary email after reset")
    temporary_password = models.CharField(max_length=128, help_text="Temporary password (hashed)")
    reset_reason = models.TextField(blank=True, help_text="Reason for account reset")

    class Meta:
        ordering = ['-reset_timestamp']
        verbose_name = "Account Reset"
        verbose_name_plural = "Account Resets"

    def __str__(self):
        return f"Reset: {self.user.username} by {self.reset_by.username} - {self.reset_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
