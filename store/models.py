from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Store(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_stores',
        limit_choices_to={'role': 'store_owner'}
    )
    cashier = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='cashier_of_store',
    limit_choices_to={'role': 'cashier'}
    )

    def __str__(self):
        return self.name


class StoreManager(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='manager_assignment')
    manager = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='managed_store'
    )
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.manager.role != 'store_manager':
            raise ValidationError('Assigned manager user must have role "store_manager".')

        # Only one active manager per store
        if StoreManager.objects.filter(store=self.store, is_active=True).exclude(pk=self.pk).exists():
            raise ValidationError(f"{self.store.name} already has an active manager.")

        # Only one active store per manager
        if StoreManager.objects.filter(manager=self.manager, is_active=True).exclude(pk=self.pk).exists():
            raise ValidationError(f"{self.manager.username} is already an active manager for another store.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.manager.role != 'store_manager':
            self.manager.role = 'store_manager'
            self.manager.save(update_fields=['role'])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.manager.username} (Manager) @ {self.store.name}"


class StoreCashier(models.Model):
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='cashier_assignment')
    cashier = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cashier_store'
    )
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.cashier.role != 'cashier':
            raise ValidationError('Assigned cashier user must have role "cashier".')

        if StoreCashier.objects.filter(store=self.store, is_active=True).exclude(pk=self.pk).exists():
            raise ValidationError(f"{self.store.name} already has an active cashier.")

        if StoreCashier.objects.filter(cashier=self.cashier, is_active=True).exclude(pk=self.pk).exists():
            raise ValidationError(f"{self.cashier.username} is already an active cashier for another store.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.cashier.role != 'cashier':
            self.cashier.role = 'cashier'
            self.cashier.save(update_fields=['role'])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cashier.username} (Cashier) @ {self.store.name}"
