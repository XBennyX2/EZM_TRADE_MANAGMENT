from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.db import models

from .models import Product, Stock
from .forms import ProductForm, StockCreateForm, StockUpdateForm

# --- Custom Permission Mixins ---

class StoreOwnerMixin(UserPassesTestMixin):
    """Limits access to Store Owners only."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'head_manager'

class ManagerAndOwnerMixin(UserPassesTestMixin):
    """Limits access to Store Owners and Store Managers."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['head_manager', 'store_manager']

class ManagerOnlyMixin(UserPassesTestMixin):
    """Limits access to Store Managers only."""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'store_manager'

class ObjectManagerRequiredMixin(UserPassesTestMixin):
    """
    Limits access to the Store Owner or the specific Store Manager of the object.
    Used for updating a specific stock item.
    """
    def test_func(self):
        user = self.request.user
        if user.role == 'head_manager':
            return True  # Head manager can edit any stock
        
        obj = self.get_object() # Gets the Stock instance
        
        if user.role == 'store_manager' and hasattr(obj, 'store'):
            return obj.store.manager == user # Is the user the manager of this stock's store?
        return False

# --- Product Views (Catalog Management) ---

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'

class ProductCreateView(LoginRequiredMixin, ManagerAndOwnerMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    extra_context = {'title': 'Create New Product'}
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, f'Product "{form.instance.name}" has been created successfully.')
        return super().form_valid(form)

class ProductUpdateView(LoginRequiredMixin, ManagerAndOwnerMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    extra_context = {'title': 'Edit Product'}
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, f'Product "{form.instance.name}" has been updated successfully.')
        return super().form_valid(form)

class ProductDeleteView(LoginRequiredMixin, StoreOwnerMixin, DeleteView):
    model = Product
    template_name = 'inventory/confirm_delete_template.html'
    extra_context = {'title': 'Delete Product'}
    success_url = reverse_lazy('product_list')


# --- Stock Views (Inventory Management) ---

class StockListView(LoginRequiredMixin, ListView):
    model = Stock
    template_name = 'inventory/stock_list.html'
    context_object_name = 'stock_levels'

    def get_queryset(self):
        """
        Overrides the default queryset to filter stock based on user role and the correct models.
        """
        user = self.request.user
        
        if user.role == 'head_manager':
            return Stock.objects.all().select_related('product', 'store')
        
        elif user.role == 'store_manager':
            # Get the store manager's store - handle both relationship patterns
            user_store = None

            # Try the OneToOneField relationship first (store_manager -> managed_store)
            if hasattr(user, 'managed_store') and user.managed_store:
                user_store = user.managed_store
            # Fallback to ForeignKey relationship (user -> store)
            elif hasattr(user, 'store') and user.store:
                user_store = user.store

            if user_store:
                return Stock.objects.filter(store=user_store).select_related('product', 'store')

        elif user.role == 'cashier':
            # For cashiers, use the ForeignKey relationship (user -> store)
            if hasattr(user, 'store') and user.store:
                return Stock.objects.filter(store=user.store).select_related('product', 'store')
        
        # Return an empty list if the user has no role or assigned store
        return Stock.objects.none()
    
    # Low stock alerts
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        low_stock_items = self.get_queryset().filter(quantity__lt=models.F('low_stock_threshold'))

        if self.request.user.role == 'store_manager':
            context['low_stock_alerts'] = low_stock_items
            if low_stock_items.exists():
                messages.warning(self.request, f" You have {low_stock_items.count()} product(s) below the low stock threshold!")

        return context

class StockCreateView(LoginRequiredMixin, ManagerOnlyMixin, CreateView):
    model = Stock
    form_class = StockCreateForm
    template_name = 'inventory/form_template.html'
    extra_context = {'title': 'Add New Stock Item'}
    success_url = reverse_lazy('stock_list')

    def form_valid(self, form):
        # Get the store manager's store - handle both relationship patterns
        user_store = None

        # Try the OneToOneField relationship first (store_manager -> managed_store)
        if hasattr(self.request.user, 'managed_store') and self.request.user.managed_store:
            user_store = self.request.user.managed_store
        # Fallback to ForeignKey relationship (user -> store)
        elif hasattr(self.request.user, 'store') and self.request.user.store:
            user_store = self.request.user.store

        if not user_store:
            messages.error(self.request, "You are not assigned to any store. Contact your administrator.")
            return redirect('stock_list')

        # Assign the stock to the manager's store automatically before saving.
        form.instance.store = user_store

        # Prevent creating a duplicate stock item
        product = form.cleaned_data.get('product')
        if Stock.objects.filter(store=user_store, product=product).exists():
            messages.error(self.request, f"{product.name} is already stocked in your store. Please update the existing record instead.")
            return redirect('stock_list')

        messages.success(self.request, f"Successfully added {product.name} to your store's inventory.")
        return super().form_valid(form)

class StockUpdateView(LoginRequiredMixin, ObjectManagerRequiredMixin, UpdateView):
    model = Stock
    form_class = StockUpdateForm
    template_name = 'inventory/form_template.html'
    extra_context = {'title': 'Update Stock'}
    success_url = reverse_lazy('stock_list')

class StockDeleteView(LoginRequiredMixin, StoreOwnerMixin, DeleteView):
    model = Stock
    template_name = 'inventory/confirm_delete_template.html'
    extra_context = {'title': 'Delete Stock Record'}
    success_url = reverse_lazy('stock_list')