from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.db import models
from django.db.models import ProtectedError, Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import (
    Product, Stock, Supplier, WarehouseProduct, Warehouse, PurchaseOrder, PurchaseOrderItem, SETTINGS_CHOICES,
    SupplierProfile, SupplierProduct, PurchaseRequest, PurchaseRequestItem
)
from .forms import (
    ProductForm, StockCreateForm, StockUpdateForm, SupplierForm, WarehouseProductForm,
    WarehouseForm, PurchaseOrderForm, PurchaseOrderItemForm, PurchaseOrderItemFormSet,
    PurchaseRequestForm
)
from transactions.models import SupplierAccount
from django.contrib.auth import get_user_model
from transactions.models import SupplierAccount

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
        queryset = Supplier.objects.select_related('profile').prefetch_related('catalog_products').all().order_by('name')

        # Get filter parameters
        search = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        onboarding_filter = self.request.GET.get('onboarding')
        category_filter = self.request.GET.get('category')

        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(contact_person__icontains=search)
            )

        # Apply status filter
        if status_filter:
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(is_active=False)

        # Apply onboarding filter
        if onboarding_filter:
            if onboarding_filter == 'complete':
                queryset = queryset.filter(profile__is_onboarding_complete=True)
            elif onboarding_filter == 'incomplete':
                queryset = queryset.filter(
                    Q(profile__isnull=True) | Q(profile__is_onboarding_complete=False)
                )

        # Apply category filter
        if category_filter:
            queryset = queryset.filter(profile__product_categories__icontains=category_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter parameters to context
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['onboarding_filter'] = self.request.GET.get('onboarding', '')
        context['category_filter'] = self.request.GET.get('category', '')

        # Get all product categories for filter dropdown
        categories = set()
        for supplier in Supplier.objects.filter(profile__isnull=False):
            if hasattr(supplier, 'profile') and supplier.profile.product_categories:
                supplier_categories = supplier.profile.get_product_categories_list()
                categories.update(supplier_categories)
        context['available_categories'] = sorted(list(categories))

        # Add statistics
        context['total_suppliers'] = Supplier.objects.count()
        context['active_suppliers'] = Supplier.objects.filter(is_active=True).count()
        context['onboarded_suppliers'] = Supplier.objects.filter(profile__is_onboarding_complete=True).count()

        # Add supplier data with enhanced information
        enhanced_suppliers = []
        for supplier in context['suppliers']:
            supplier_data = {
                'supplier': supplier,
                'has_profile': hasattr(supplier, 'profile') and supplier.profile is not None,
                'onboarding_complete': hasattr(supplier, 'profile') and supplier.profile and supplier.profile.is_onboarding_complete,
                'product_count': supplier.catalog_products.count(),
                'active_product_count': supplier.catalog_products.filter(is_active=True).count(),
            }

            # Add account status
            try:
                supplier_account = SupplierAccount.objects.get(supplier=supplier)
                supplier_data['has_account'] = True
                supplier_data['account_active'] = supplier_account.is_active
            except SupplierAccount.DoesNotExist:
                supplier_data['has_account'] = False
                supplier_data['account_active'] = False

            enhanced_suppliers.append(supplier_data)

        context['enhanced_suppliers'] = enhanced_suppliers

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


# --- Supplier Account Management ---

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role in ['admin', 'head_manager'])
def activate_supplier_account(request, supplier_id):
    """
    Activate a supplier account by creating a SupplierAccount if it doesn't exist.
    This function is used by Head Managers and Admins to set up supplier accounts.
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == 'POST':
        try:
            # Check if SupplierAccount already exists
            supplier_account, created = SupplierAccount.objects.get_or_create(
                supplier=supplier,
                defaults={
                    'payment_terms': request.POST.get('payment_terms', 'net_30'),
                    'credit_limit': request.POST.get('credit_limit', '0.00'),
                    'is_active': True
                }
            )

            if created:
                messages.success(request, f"Supplier account activated successfully for {supplier.name}!")
            else:
                # Update existing account if needed
                supplier_account.payment_terms = request.POST.get('payment_terms', supplier_account.payment_terms)
                supplier_account.credit_limit = request.POST.get('credit_limit', supplier_account.credit_limit)
                supplier_account.is_active = True
                supplier_account.save()
                messages.success(request, f"Supplier account updated for {supplier.name}!")

        except Exception as e:
            messages.error(request, f"Error activating supplier account: {str(e)}")

    return redirect('supplier_list')


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role in ['admin', 'head_manager'])
def supplier_account_status(request, supplier_id):
    """
    Check the account status of a supplier (AJAX endpoint)
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)

    try:
        supplier_account = SupplierAccount.objects.get(supplier=supplier)
        has_account = True
        account_data = {
            'account_number': supplier_account.account_number,
            'current_balance': str(supplier_account.current_balance),
            'payment_terms': supplier_account.get_payment_terms_display(),
            'credit_limit': str(supplier_account.credit_limit),
            'is_active': supplier_account.is_active,
        }
    except SupplierAccount.DoesNotExist:
        has_account = False
        account_data = None

    # Check if there's a user account with this email
    User = get_user_model()
    user_account = None
    if supplier.email:
        try:
            user_account = User.objects.get(email=supplier.email, role='supplier')
            user_data = {
                'username': user_account.username,
                'full_name': user_account.get_full_name(),
                'is_active': user_account.is_active,
                'last_login': user_account.last_login.isoformat() if user_account.last_login else None,
            }
        except User.DoesNotExist:
            user_data = None
    else:
        user_data = None

    return JsonResponse({
        'supplier_name': supplier.name,
        'supplier_email': supplier.email,
        'supplier_active': supplier.is_active,
        'has_account': has_account,
        'account_data': account_data,
        'has_user': user_data is not None,
        'user_data': user_data,
        'setup_complete': has_account and user_data is not None,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role in ['admin', 'head_manager'])
def supplier_profile_view(request, supplier_id):
    """
    View detailed supplier profile information for Head Managers
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)

    try:
        supplier_profile = SupplierProfile.objects.get(supplier=supplier)
    except SupplierProfile.DoesNotExist:
        supplier_profile = None

    try:
        supplier_account = SupplierAccount.objects.get(supplier=supplier)
    except SupplierAccount.DoesNotExist:
        supplier_account = None

    # Get supplier products
    products = SupplierProduct.objects.filter(supplier=supplier).order_by('-created_date')[:10]

    # Get user account
    User = get_user_model()
    user_account = None
    if supplier.email:
        try:
            user_account = User.objects.get(email=supplier.email, role='supplier')
        except User.DoesNotExist:
            pass

    context = {
        'supplier': supplier,
        'supplier_profile': supplier_profile,
        'supplier_account': supplier_account,
        'user_account': user_account,
        'recent_products': products,
        'total_products': SupplierProduct.objects.filter(supplier=supplier).count(),
        'active_products': SupplierProduct.objects.filter(supplier=supplier, is_active=True).count(),
    }

    return render(request, 'inventory/supplier_profile_view.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role in ['admin', 'head_manager'])
def supplier_product_catalog_view(request, supplier_id):
    """
    View supplier's product catalog for Head Managers
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)

    # Get filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')

    # Get supplier products
    products = SupplierProduct.objects.filter(supplier=supplier)

    # Apply filters
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(product_code__icontains=search_query)
        )

    if category_filter:
        products = products.filter(category__icontains=category_filter)

    if status_filter:
        if status_filter == 'active':
            products = products.filter(is_active=True)
        elif status_filter == 'inactive':
            products = products.filter(is_active=False)
        else:
            products = products.filter(availability_status=status_filter)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products.order_by('-created_date'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for filter dropdown
    categories = SupplierProduct.objects.filter(supplier=supplier).values_list('category', flat=True).distinct()

    context = {
        'supplier': supplier,
        'products': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories': categories,
        'total_products': products.count(),
    }

    return render(request, 'inventory/supplier_product_catalog_view.html', context)


# --- Purchase Request System ---

@login_required
@user_passes_test(lambda u: u.is_superuser or u.role in ['admin', 'head_manager'])
def purchase_request_list(request):
    """
    List all purchase requests for Head Managers
    """
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    supplier_filter = request.GET.get('supplier', '')

    # Get purchase requests
    requests = PurchaseRequest.objects.select_related('supplier', 'requested_by').all()

    # Apply filters
    if search_query:
        requests = requests.filter(
            Q(request_number__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )

    if status_filter:
        requests = requests.filter(status=status_filter)

    if supplier_filter:
        requests = requests.filter(supplier_id=supplier_filter)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(requests.order_by('-created_date'), 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get suppliers for filter dropdown
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')

    context = {
        'requests': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'supplier_filter': supplier_filter,
        'suppliers': suppliers,
        'status_choices': PurchaseRequest.STATUS_CHOICES,
        'total_requests': requests.count(),
    }

    return render(request, 'inventory/purchase_request_list.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role in ['admin', 'head_manager'])
def purchase_request_create(request):
    """
    Create a new purchase request
    """
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            purchase_request = form.save(commit=False)
            purchase_request.requested_by = request.user
            purchase_request.save()

            messages.success(request, f"Purchase request '{purchase_request.request_number}' created successfully!")
            return redirect('purchase_request_detail', pk=purchase_request.pk)
    else:
        form = PurchaseRequestForm()

    context = {
        'form': form,
        'action': 'Create',
    }

    return render(request, 'inventory/purchase_request_form.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role in ['admin', 'head_manager'])
def purchase_request_detail(request, pk):
    """
    View purchase request details
    """
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk)
    items = purchase_request.items.select_related('supplier_product').all()

    context = {
        'purchase_request': purchase_request,
        'items': items,
    }

    return render(request, 'inventory/purchase_request_detail.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role in ['admin', 'head_manager'])
def purchase_request_from_catalog(request, supplier_id):
    """
    Create purchase request from supplier catalog
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == 'POST':
        # Handle form submission
        form = PurchaseRequestForm(request.POST)
        selected_products = request.POST.getlist('selected_products')
        quantities = request.POST.getlist('quantities')

        if form.is_valid() and selected_products:
            purchase_request = form.save(commit=False)
            purchase_request.supplier = supplier
            purchase_request.requested_by = request.user
            purchase_request.save()

            # Create purchase request items
            total_estimated = 0
            for i, product_id in enumerate(selected_products):
                if i < len(quantities) and quantities[i]:
                    try:
                        product = SupplierProduct.objects.get(id=product_id, supplier=supplier)
                        quantity = int(quantities[i])

                        PurchaseRequestItem.objects.create(
                            purchase_request=purchase_request,
                            supplier_product=product,
                            requested_quantity=quantity,
                            unit_price=product.unit_price,
                            total_price=product.unit_price * quantity
                        )

                        total_estimated += product.unit_price * quantity
                    except (SupplierProduct.DoesNotExist, ValueError):
                        continue

            # Update estimated total
            purchase_request.estimated_total = total_estimated
            purchase_request.save()

            messages.success(request, f"Purchase request '{purchase_request.request_number}' created successfully!")
            return redirect('purchase_request_detail', pk=purchase_request.pk)
    else:
        form = PurchaseRequestForm()

    # Get supplier products
    products = SupplierProduct.objects.filter(supplier=supplier, is_active=True).order_by('category', 'product_name')

    context = {
        'form': form,
        'supplier': supplier,
        'products': products,
        'action': 'Create from Catalog',
    }

    return render(request, 'inventory/purchase_request_from_catalog.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.role in ['admin', 'head_manager'])
def convert_request_to_order(request, pk):
    """
    Convert a purchase request to a purchase order
    """
    purchase_request = get_object_or_404(PurchaseRequest, pk=pk)

    # Check if request can be converted
    if purchase_request.status not in ['quoted', 'approved']:
        messages.error(request, "Only quoted or approved purchase requests can be converted to orders.")
        return redirect('purchase_request_detail', pk=purchase_request.pk)

    if request.method == 'POST':
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            supplier=purchase_request.supplier,
            order_date=timezone.now().date(),
            expected_delivery_date=purchase_request.required_delivery_date,
            delivery_address=purchase_request.delivery_address,
            status='pending',
            notes=f"Converted from Purchase Request #{purchase_request.request_number}\n\n{purchase_request.internal_notes}",
            created_by=request.user
        )

        # Create purchase order items
        total_amount = 0
        for request_item in purchase_request.items.all():
            # Use quoted price if available, otherwise use requested price
            unit_price = request_item.quoted_unit_price or request_item.unit_price
            quantity = request_item.requested_quantity

            # Create warehouse product if it doesn't exist
            try:
                warehouse_product = WarehouseProduct.objects.get(
                    product_id=f"SP-{request_item.supplier_product.id}"
                )
            except WarehouseProduct.DoesNotExist:
                # Create new warehouse product from supplier product
                supplier_product = request_item.supplier_product
                warehouse_product = WarehouseProduct.objects.create(
                    product_id=f"SP-{supplier_product.id}",
                    product_name=supplier_product.product_name,
                    category=supplier_product.category,
                    description=supplier_product.description,
                    unit_price=supplier_product.unit_price,
                    supplier=supplier_product.supplier
                )

            # Create purchase order item
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                product=warehouse_product,
                quantity=quantity,
                unit_price=unit_price,
                total_price=unit_price * quantity
            )

            total_amount += unit_price * quantity

        # Update purchase order total
        purchase_order.total_amount = total_amount
        purchase_order.save()

        # Update purchase request status
        purchase_request.status = 'converted'
        purchase_request.save()

        messages.success(request, f"Purchase request converted to order #{purchase_order.order_number} successfully!")
        return redirect('purchase_order_detail', pk=purchase_order.pk)

    context = {
        'purchase_request': purchase_request,
        'items': purchase_request.items.all(),
    }

    return render(request, 'inventory/convert_request_to_order.html', context)