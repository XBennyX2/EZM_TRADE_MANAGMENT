from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from Inventory.models import Product, Stock
from transactions.models import Transaction
from .models import Order, FinancialRecord
from users.models import CustomUser
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML  # Make sure you have WeasyPrint installed

@login_required
def process_sale(request):
    products = Product.objects.all()
    if request.method == 'POST':
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')
        discount = float(request.POST.get('discount'))
        taxable = request.POST.get('taxable') == 'on'
        payment_type = request.POST.get('payment_type')

        total = 0
        order_items = []

        try:
            with transaction.atomic():
                # Create Order
                order = Order.objects.create(
                    customer=request.user,  # Assuming the logged-in user is the customer
                    total_amount=0 # Initialize total amount to 0
                )

                # Reduce product stock and calculate item totals
                for product_id, quantity in zip(product_ids, quantities):
                    product = get_object_or_404(Product, pk=product_id)
                    quantity = int(quantity)

                    # Reduce product stock
                    try:
                        stock = Stock.objects.get(product=product, store=request.user.store)
                    except Stock.DoesNotExist:
                        raise ValueError(f"{product.name} not in stock")
                    if stock.quantity < quantity:
                        raise ValueError(f"Not enough stock for {product.name}")
                    stock.quantity -= quantity
                    stock.save()

                    # Calculate item total
                    item_total = product.price * quantity
                    order_items.append((product, quantity, item_total))
                    total += item_total

                # Calculate totals
                discount_amount = total * (discount / 100)
                total -= discount_amount
                tax = total * 0.05 if taxable else 0
                total += tax

                order.total_amount = total
                order.save()

                # Create Transaction
                transaction_obj = Transaction.objects.create(
                    sale_type='POS',
                    quantity=sum(int(q) for q in quantities),
                    user=request.user,
                    total_amount=total,
                    store=request.user.store
                )

                order.transaction = transaction_obj # Associate the transaction with the order
                order.save()

                # Create Financial Record
                FinancialRecord.objects.create(
                    store=request.user.store,
                    cashier=request.user,
                    amount=total,
                    record_type='revenue'
                )

                # Generate Receipt (basic HTML)
                receipt_html = render_to_string('store/receipt_template.html', {'order': order, 'total': total, 'tax': tax, 'discount': discount_amount, 'payment_type': payment_type, 'order_items': order_items})
                # Generate PDF
                # html = HTML(string=receipt_html)
                # pdf_file = html.write_pdf()
                # response = HttpResponse(pdf_file, content_type='application/pdf')
                # response['Content-Disposition'] = 'filename="receipt.pdf"'
                # return HttpResponse(receipt_html)

        except ValueError as e:
            return render(request, 'store/process_sale.html', {'products': products, 'error': str(e)})

    return render(request, 'store/process_sale.html', {'products': products})

def get_product_price(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return JsonResponse({'price': product.price})

from django.shortcuts import render

from .forms import StoreForm

def create_store(request):
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save()
            return redirect('head_manager_page')  # Redirect to store owner page after successful creation
    else:
        form = StoreForm()
    return render(request, 'store/create_store.html', {'form': form})

from django.shortcuts import render, get_object_or_404
from .models import Store

import logging
from .forms import AssignManagerForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import models

logger = logging.getLogger(__name__)


# --- Custom Permission Mixins ---
class StoreOwnerMixin(UserPassesTestMixin):
    """
    Mixin to ensure only head managers can access store management views.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'head_manager'

@login_required
def manage_store(request, store_id):
    store = get_object_or_404(Store, pk=store_id)
    if request.method == 'POST':
        form = AssignManagerForm(request.POST)
        if form.is_valid():
            manager = form.cleaned_data['manager']
            logger.info(f"Assigning manager {manager.username} to store {store.name}")
            store.store_manager = manager
            store.save()
            manager.store = store
            manager.save()
            logger.info(f"Successfully assigned manager {manager.username} to store {store.name}")
            from django.contrib import messages
            messages.success(request, f"Successfully assigned {manager.username} to {store.name}")
            return redirect('head_manager_page')
        else:
            logger.warning(f"Invalid form data: {form.errors}")
    else:
        form = AssignManagerForm()
    return render(request, 'store/manage_store.html', {'store': store, 'form': form})


# --- Showroom Management Views ---

class ShowroomListView(LoginRequiredMixin, StoreOwnerMixin, ListView):
    """
    List all stores (showrooms) for head manager.
    """
    model = Store
    template_name = 'store/showroom_list.html'
    context_object_name = 'stores'
    paginate_by = 12

    def get_queryset(self):
        queryset = Store.objects.all().select_related('store_manager')

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(address__icontains=search) |
                models.Q(phone_number__icontains=search)
            )

        # Manager filter
        manager_filter = self.request.GET.get('manager')
        if manager_filter == 'assigned':
            queryset = queryset.filter(store_manager__isnull=False)
        elif manager_filter == 'unassigned':
            queryset = queryset.filter(store_manager__isnull=True)

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stores = Store.objects.all()

        context['total_stores'] = stores.count()
        context['stores_with_managers'] = stores.filter(store_manager__isnull=False).count()
        context['stores_without_managers'] = stores.filter(store_manager__isnull=True).count()

        # Get available managers for assignment
        from users.models import CustomUser
        context['available_managers'] = CustomUser.objects.filter(
            role='store_manager',
            is_active=True,
            store__isnull=True
        )

        return context


class ShowroomDetailView(LoginRequiredMixin, StoreOwnerMixin, DetailView):
    """
    Detailed view of a specific store/showroom.
    """
    model = Store
    template_name = 'store/showroom_detail.html'
    context_object_name = 'store'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.get_object()

        # Get store statistics
        from Inventory.models import Stock
        from transactions.models import Transaction

        context['total_products'] = Stock.objects.filter(store=store).count()
        context['low_stock_items'] = Stock.objects.filter(
            store=store,
            quantity__lte=models.F('low_stock_threshold')
        ).count()

        # Recent transactions
        context['recent_transactions'] = Transaction.objects.filter(
            store=store
        ).order_by('-timestamp')[:5]

        # Monthly sales
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_ago = timezone.now() - timedelta(days=30)
        context['monthly_sales'] = Transaction.objects.filter(
            store=store,
            timestamp__gte=thirty_days_ago
        ).aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0

        # Available managers for assignment
        from users.models import CustomUser
        context['available_managers'] = CustomUser.objects.filter(
            role='store_manager',
            is_active=True,
            store__isnull=True
        )

        return context


class ShowroomCreateView(LoginRequiredMixin, StoreOwnerMixin, CreateView):
    """
    Create a new store/showroom.
    """
    model = Store
    template_name = 'store/showroom_form.html'
    fields = ['name', 'address', 'phone_number']
    success_url = reverse_lazy('showroom_list')

    def form_valid(self, form):
        messages.success(self.request, f"Store '{form.instance.name}' created successfully!")
        return super().form_valid(form)


class ShowroomUpdateView(LoginRequiredMixin, StoreOwnerMixin, UpdateView):
    """
    Update store/showroom information.
    """
    model = Store
    template_name = 'store/showroom_form.html'
    fields = ['name', 'address', 'phone_number', 'store_manager']
    success_url = reverse_lazy('showroom_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit manager choices to available store managers
        from users.models import CustomUser
        form.fields['store_manager'].queryset = CustomUser.objects.filter(
            role='store_manager',
            is_active=True
        )
        form.fields['store_manager'].required = False
        return form

    def form_valid(self, form):
        # Handle manager assignment/unassignment
        old_manager = Store.objects.get(pk=self.object.pk).store_manager
        new_manager = form.cleaned_data.get('store_manager')

        if old_manager != new_manager:
            # Unassign old manager
            if old_manager:
                old_manager.store = None
                old_manager.save()

            # Assign new manager
            if new_manager:
                new_manager.store = form.instance
                new_manager.save()

        messages.success(self.request, f"Store '{form.instance.name}' updated successfully!")
        return super().form_valid(form)


class ShowroomDeleteView(LoginRequiredMixin, StoreOwnerMixin, DeleteView):
    """
    Delete a store/showroom.
    """
    model = Store
    template_name = 'store/showroom_confirm_delete.html'
    success_url = reverse_lazy('showroom_list')

    def delete(self, request, *args, **kwargs):
        store = self.get_object()
        # Unassign manager if exists
        if store.store_manager:
            store.store_manager.store = None
            store.store_manager.save()

        messages.success(request, f"Store '{store.name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)
