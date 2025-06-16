from django.db import models
from django.conf import settings

class Store(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'store_manager'}
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
    
