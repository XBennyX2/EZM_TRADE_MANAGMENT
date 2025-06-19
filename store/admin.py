from django.contrib import admin

from .models import *  # or the other user-related model

admin.site.register(Store)
# admin.site.register(StoreManager)
# admin.site.register(StoreCashier)
