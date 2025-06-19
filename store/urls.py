from django.urls import path
from . import views

urlpatterns = [
    # ... other URL patterns
    path('process_sale/', views.process_sale, name='process_sale'),
    path('get_product_price/<int:product_id>/', views.get_product_price, name='get_product_price'),
]