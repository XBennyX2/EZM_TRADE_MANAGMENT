from django.urls import path
from .views import StoreListView, StoreCreateView, StoreUpdateView, StoreDeleteView

urlpatterns = [
    path('', StoreListView.as_view(), name='store_list'),
    path('new/', StoreCreateView.as_view(), name='store_create'),
    path('<int:pk>/edit/', StoreUpdateView.as_view(), name='store_update'),
    path('<int:pk>/delete/', StoreDeleteView.as_view(), name='store_delete'),
]