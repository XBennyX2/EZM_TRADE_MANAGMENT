from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Category, Product, Stock
from .forms import CategoryForm, ProductForm

class ManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is an admin or store manager."""
    def test_func(self):
        return self.request.user.role in ['admin', 'store_manager']

# --- Category Views ---

class CategoryListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = Category
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'

class CategoryCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/form_template.html'
    extra_context = {'title': 'Create New Category'}
    success_url = reverse_lazy('category_list')

class CategoryUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'inventory/form_template.html'
    extra_context = {'title': 'Edit Category'}
    success_url = reverse_lazy('category_list')

class CategoryDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = Category
    template_name = 'inventory/confirm_delete_template.html'
    extra_context = {'title': 'Delete Category'}
    success_url = reverse_lazy('category_list')


# --- Product Views ---

class ProductListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'

class ProductCreateView(LoginRequiredMixin, ManagerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/form_template.html'
    extra_context = {'title': 'Create New Product'}
    success_url = reverse_lazy('product_list')

class ProductUpdateView(LoginRequiredMixin, ManagerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/form_template.html'
    extra_context = {'title': 'Edit Product'}
    success_url = reverse_lazy('product_list')

class ProductDeleteView(LoginRequiredMixin, ManagerRequiredMixin, DeleteView):
    model = Product
    template_name = 'inventory/confirm_delete_template.html'
    extra_context = {'title': 'Delete Product'}
    success_url = reverse_lazy('product_list')


# --- Stock View ---

class StockListView(LoginRequiredMixin, ListView):
    model = Stock
    template_name = 'inventory/stock_list.html'
    context_object_name = 'stock_levels'

    def get_queryset(self):
        # Users should only see stock relevant to them
        user = self.request.user
        if user.role == 'admin':
            return Stock.objects.all()
        elif user.role == 'store_manager':
            # A manager should see stock for the store they manage
            return Stock.objects.filter(store__manager=user)
        # Add more logic for other roles if needed
        return Stock.objects.none()