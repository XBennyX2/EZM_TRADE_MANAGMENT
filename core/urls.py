from django.contrib import admin
from django.urls import path, include
import logging
logger = logging.getLogger(__name__)
try:
    from users.views import login_view
except ImportError as e:
    logger.error(f"Could not import users.templatetags.users_utils: {e}")
    raise

urlpatterns = [
    path('', login_view, name='login'),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('stores/', include('store.urls')),
    path('inventory/', include('Inventory.urls')),
]
