# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('store_owner', 'Store Owner'),
        ('store_manager', 'Store Manager'),
        ('cashier', 'Cashier'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    store = models.ForeignKey('store.Store', on_delete=models.SET_NULL, null=True, blank=True) # Add this line
    is_first_login = models.BooleanField(default=True)
    full_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
