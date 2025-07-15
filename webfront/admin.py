from django.contrib import admin
from Inventory.models import Stock, Product
from store.models import Store

# Since webfront doesn't have its own models, we can customize existing model admin here if needed
# This is just for reference - the actual admin configurations are in their respective apps
