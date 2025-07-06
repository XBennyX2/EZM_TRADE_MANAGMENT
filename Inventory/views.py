from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db import models
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.db import models

from .models import Product, Stock, Supplier, WarehouseProduct, Warehouse, PurchaseOrder, PurchaseOrderItem, SETTINGS_CHOICES
from .forms import (
    ProductForm, StockCreateForm, StockUpdateForm, SupplierForm, WarehouseProductForm,
    WarehouseForm, PurchaseOrderForm, PurchaseOrderItemForm, PurchaseOrderItemFormSet
)

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


# --- Supplier Management Views ---

class SupplierListView(LoginRequiredMixin, StoreOwnerMixin, ListView):
    model = Supplier
    template_name = 'inventory/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Supplier.objects.all().order_by('name')
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class SupplierCreateView(LoginRequiredMixin, StoreOwnerMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('supplier_list')

    def form_valid(self, form):
        messages.success(self.request, f"Supplier '{form.instance.name}' created successfully!")
        return super().form_valid(form)


class SupplierUpdateView(LoginRequiredMixin, StoreOwnerMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'inventory/supplier_form.html'
    success_url = reverse_lazy('supplier_list')

    def form_valid(self, form):
        messages.success(self.request, f"Supplier '{form.instance.name}' updated successfully!")
        return super().form_valid(form)


class SupplierDeleteView(LoginRequiredMixin, StoreOwnerMixin, DeleteView):
    model = Supplier
    template_name = 'inventory/supplier_confirm_delete.html'
    success_url = reverse_lazy('supplier_list')

    def delete(self, request, *args, **kwargs):
        supplier = self.get_object()
        messages.success(request, f"Supplier '{supplier.name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)


# --- Warehouse Management Views ---

class WarehouseListView(LoginRequiredMixin, StoreOwnerMixin, ListView):
    model = WarehouseProduct
    template_name = 'inventory/warehouse_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = WarehouseProduct.objects.select_related('warehouse', 'supplier').all()

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(product_name__icontains=search) |
                models.Q(product_id__icontains=search) |
                models.Q(category__icontains=search) |
                models.Q(sku__icontains=search) |
                models.Q(warehouse__name__icontains=search)
            )

        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Warehouse filter
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)

        # Stock status filter
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low':
            queryset = queryset.filter(quantity_in_stock__lte=models.F('minimum_stock_level'))
        elif stock_status == 'out':
            queryset = queryset.filter(quantity_in_stock=0)
        elif stock_status == 'normal':
            queryset = queryset.filter(quantity_in_stock__gt=models.F('minimum_stock_level'))

        return queryset.order_by('warehouse__name', 'product_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all products for statistics
        all_products = WarehouseProduct.objects.all()

        context['total_products'] = all_products.count()
        context['total_quantity'] = all_products.aggregate(
            total=models.Sum('quantity_in_stock')
        )['total'] or 0
        context['low_stock_count'] = all_products.filter(
            quantity_in_stock__lte=models.F('minimum_stock_level')
        ).count()
        context['out_of_stock_count'] = all_products.filter(quantity_in_stock=0).count()

        # Get categories and warehouses for filters
        context['categories'] = [choice[0] for choice in SETTINGS_CHOICES]
        context['warehouses'] = Warehouse.objects.filter(is_active=True)

        return context


class WarehouseCreateView(LoginRequiredMixin, StoreOwnerMixin, CreateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse_form.html'
    success_url = reverse_lazy('warehouse_list')

    def form_valid(self, form):
        messages.success(self.request, f"Warehouse '{form.instance.name}' created successfully!")
        return super().form_valid(form)


class WarehouseUpdateView(LoginRequiredMixin, StoreOwnerMixin, UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse_form.html'
    success_url = reverse_lazy('warehouse_list')

    def form_valid(self, form):
        messages.success(self.request, f"Warehouse '{form.instance.name}' updated successfully!")
        return super().form_valid(form)


class WarehouseDetailView(LoginRequiredMixin, StoreOwnerMixin, DetailView):
    model = Warehouse
    template_name = 'inventory/warehouse_detail.html'
    context_object_name = 'warehouse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warehouse = self.get_object()

        # Get all products in this warehouse
        products = WarehouseProduct.objects.filter(warehouse=warehouse)

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            products = products.filter(
                models.Q(product_name__icontains=search) |
                models.Q(product_id__icontains=search) |
                models.Q(category__icontains=search) |
                models.Q(sku__icontains=search)
            )

        # Category filter
        category = self.request.GET.get('category')
        if category:
            products = products.filter(category=category)

        # Stock status filter
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low':
            products = products.filter(quantity_in_stock__lte=models.F('minimum_stock_level'))
        elif stock_status == 'out':
            products = products.filter(quantity_in_stock=0)
        elif stock_status == 'normal':
            products = products.filter(quantity_in_stock__gt=models.F('minimum_stock_level'))

        context['products'] = products.order_by('product_name')
        context['total_products'] = products.count()
        context['total_quantity'] = products.aggregate(
            total=models.Sum('quantity_in_stock')
        )['total'] or 0
        context['low_stock_count'] = products.filter(
            quantity_in_stock__lte=models.F('minimum_stock_level')
        ).count()
        context['out_of_stock_count'] = products.filter(quantity_in_stock=0).count()
        context['categories'] = [choice[0] for choice in SETTINGS_CHOICES]

        return context


class WarehouseDeleteView(LoginRequiredMixin, StoreOwnerMixin, DeleteView):
    model = Warehouse
    template_name = 'inventory/warehouse_confirm_delete.html'
    success_url = reverse_lazy('warehouse_list')

    def delete(self, request, *args, **kwargs):
        warehouse = self.get_object()
        messages.success(request, f"Warehouse '{warehouse.name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)


# --- Supplier Product Views ---

class SupplierProductListView(LoginRequiredMixin, StoreOwnerMixin, ListView):
    model = WarehouseProduct
    template_name = 'inventory/supplier_products.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        self.supplier = get_object_or_404(Supplier, pk=self.kwargs['supplier_id'])
        queryset = WarehouseProduct.objects.filter(supplier=self.supplier).order_by('product_name')

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(product_name__icontains=search)

        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier'] = self.supplier
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['categories'] = SETTINGS_CHOICES
        context['total_products'] = self.get_queryset().count()
        context['low_stock_products'] = self.get_queryset().filter(
            quantity_in_stock__lte=models.F('minimum_stock_level')
        ).count()
        return context


class WarehouseProductCreateView(LoginRequiredMixin, StoreOwnerMixin, CreateView):
    model = WarehouseProduct
    form_class = WarehouseProductForm
    template_name = 'inventory/warehouse_product_form.html'

    def get_initial(self):
        initial = super().get_initial()
        supplier_id = self.kwargs.get('supplier_id')
        if supplier_id:
            initial['supplier'] = supplier_id
        return initial

    def get_success_url(self):
        supplier_id = self.kwargs.get('supplier_id')
        if supplier_id:
            return reverse_lazy('supplier_products', kwargs={'supplier_id': supplier_id})
        return reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, f"Product '{form.instance.product_name}' added successfully!")
        return super().form_valid(form)


class WarehouseProductUpdateView(LoginRequiredMixin, StoreOwnerMixin, UpdateView):
    model = WarehouseProduct
    form_class = WarehouseProductForm
    template_name = 'inventory/warehouse_product_form.html'

    def get_success_url(self):
        return reverse_lazy('supplier_products', kwargs={'supplier_id': self.object.supplier.pk})

    def form_valid(self, form):
        messages.success(self.request, f"Product '{form.instance.product_name}' updated successfully!")
        return super().form_valid(form)


class WarehouseProductDeleteView(LoginRequiredMixin, StoreOwnerMixin, DeleteView):
    model = WarehouseProduct
    template_name = 'inventory/confirm_delete_template.html'
    success_url = reverse_lazy('warehouse_list')

    def form_valid(self, form):
        product = self.get_object()
        try:
            messages.success(self.request, f"Product '{product.product_name}' deleted successfully!")
            return super().form_valid(form)
        except ProtectedError as e:
            # Handle the case where the product cannot be deleted due to foreign key constraints
            messages.error(
                self.request,
                f"Cannot delete '{product.product_name}' because it is referenced in purchase orders. "
                "Please remove or update the related purchase order items first."
            )
            return redirect('warehouse_list')


# --- Purchase Order Views ---

class PurchaseOrderListView(LoginRequiredMixin, StoreOwnerMixin, ListView):
    model = PurchaseOrder
    template_name = 'inventory/purchase_order_list.html'
    context_object_name = 'purchase_orders'
    paginate_by = 20

    def get_queryset(self):
        queryset = PurchaseOrder.objects.all().select_related('supplier').order_by('-created_date')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by supplier
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = PurchaseOrder.STATUS_CHOICES
        context['suppliers'] = Supplier.objects.filter(is_active=True)
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_supplier'] = self.request.GET.get('supplier', '')

        # Statistics
        context['total_orders'] = PurchaseOrder.objects.count()
        context['pending_orders'] = PurchaseOrder.objects.filter(status='pending').count()
        context['approved_orders'] = PurchaseOrder.objects.filter(status='approved').count()

        return context


class PurchaseOrderCreateView(LoginRequiredMixin, StoreOwnerMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'inventory/purchase_order_form.html'
    success_url = reverse_lazy('purchase_order_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = PurchaseOrderItemFormSet(self.request.POST)
        else:
            context['formset'] = PurchaseOrderItemFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            form.instance.created_by = self.request.user
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            # Calculate total amount
            self.object.calculate_total()

            messages.success(self.request, f"Purchase Order #{self.object.order_number} created successfully!")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class PurchaseOrderDetailView(LoginRequiredMixin, StoreOwnerMixin, DetailView):
    model = PurchaseOrder
    template_name = 'inventory/purchase_order_detail.html'
    context_object_name = 'purchase_order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all().select_related('warehouse_product')
        return context


class PurchaseOrderUpdateView(LoginRequiredMixin, StoreOwnerMixin, UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'inventory/purchase_order_form.html'

    def get_success_url(self):
        return reverse_lazy('purchase_order_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = PurchaseOrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = PurchaseOrderItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            # Recalculate total amount
            self.object.calculate_total()

            messages.success(self.request, f"Purchase Order #{self.object.order_number} updated successfully!")
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))