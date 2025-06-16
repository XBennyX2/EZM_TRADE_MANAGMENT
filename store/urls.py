from django.urls import path
from . import views

urlpatterns = [
    path('create-store/', views.create_store, name='create_store'),
    path('manage/<int:store_id>/', views.manage_store, name='manage_store'),
    
    path('assign-cashier/<int:store_id>/', views.assign_cashier, name='assign_cashier'),
    path('revoke-cashier/<int:store_id>/<int:cashier_id>/', views.revoke_cashier, name='revoke_cashier'),
]