from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from Inventory.models import Product, Stock
from transactions.models import Transaction, Receipt, Order as TransactionOrder
from .models import Order, FinancialRecord, Store, StoreCashier
from users.models import CustomUser
from django.template.loader import render_to_string
from django.http import HttpResponse
try:
    from weasyprint import HTML  # Make sure you have WeasyPrint installed
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False
    HTML = None
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.db import models
import json
from webfront.models import CustomerTicket, CustomerTicketItem

@login_required
def process_sale(request):
    if request.user.role != 'cashier':
        return HttpResponse("Unauthorized", status=403)
    
    products = Product.objects.all()
    
    if request.method == 'POST':
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')
        discount = float(request.POST.get('discount', 0))
        taxable = request.POST.get('taxable') == 'on'
        payment_type = request.POST.get('payment_type', 'cash')

        total = 0
        order_items = []

        try:
            with transaction.atomic():
                # Loop through selected products
                for pid, qty in zip(product_ids, quantities):
                    product = get_object_or_404(Product, pk=pid)
                    qty = int(qty)

                    stock = Stock.objects.get(product=product, store=request.user.store)
                    if stock.quantity < qty:
                        raise ValueError(f"Not enough {product.name} in stock.")
                    stock.quantity -= qty
                    stock.save()

                    item_total = product.price * qty
                    order_items.append((product, qty, item_total))
                    total += item_total

                discount_amt = total * (discount / 100)
                total -= discount_amt
                tax = total * 0.05 if taxable else 0
                total += tax

                # Create Transaction
                transaction_obj = Transaction.objects.create(
                    transaction_type='sale',
                    quantity=sum(int(q) for q in quantities),
                    total_amount=total,
                    store=request.user.store,
                    payment_type=payment_type
                )

                # Create Order entries for each product
                for product, qty, item_total in order_items:
                    Order.objects.create(
                        quantity=qty,
                        price_at_time_of_sale=product.price,
                        transaction=transaction_obj
                    )

                # Create Financial Record
                FinancialRecord.objects.create(
                    store=request.user.store,
                    cashier=request.user,
                    amount=total,
                    record_type='revenue',
                    description=f"POS Sale via {payment_type}"
                )

                # Create Receipt
                receipt = Receipt.objects.create(
                    transaction=transaction_obj,
                    total_amount=total
                )

                # Optional: Generate and return a receipt PDF
                receipt_html = render_to_string('store/receipt_template.html', {
                    'transaction': transaction_obj,
                    'receipt': receipt,
                    'tax': tax,
                    'discount': discount_amt,
                    'payment_type': payment_type,
                    'order_items': order_items,
                })

                pdf = HTML(string=receipt_html).write_pdf()
                return HttpResponse(pdf, content_type='application/pdf')

        except ValueError as e:
            return render(request, 'store/process_sale.html', {
                'products': products,
                'error': str(e)
            })

    return render(request, 'store/process_sale.html', {'products': products})


def get_product_price(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return JsonResponse({'price': product.price})

from django.shortcuts import render

from .forms import StoreForm, AssignCashierForm

def create_store(request):
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save()
            return redirect('head_manager_page')  # Redirect to haed manager page after successful creation
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
        # Check if this is an unassign request
        if request.POST.get('unassign_manager'):
            if store.store_manager:
                old_manager = store.store_manager
                logger.info(f"Unassigning manager {old_manager.username} from store {store.name}")

                # Unassign the manager
                store.store_manager = None
                store.save()
                old_manager.store = None
                old_manager.save()

                logger.info(f"Successfully unassigned manager {old_manager.username} from store {store.name}")
                from django.contrib import messages
                messages.success(request, f"Successfully removed {old_manager.username} from {store.name}")
            else:
                from django.contrib import messages
                messages.warning(request, "No manager is currently assigned to this store.")
            return redirect('manage_store', store_id=store.id)

        # Handle regular manager assignment
        form = AssignManagerForm(request.POST)
        if form.is_valid():
            manager = form.cleaned_data['manager']
            old_manager = store.store_manager

            logger.info(f"Assigning manager {manager.username} to store {store.name}")

            # Unassign old manager if exists
            if old_manager and old_manager != manager:
                old_manager.store = None
                old_manager.save()
                logger.info(f"Unassigned previous manager {old_manager.username}")

            # Assign new manager
            store.store_manager = manager
            store.save()
            manager.store = store
            manager.save()

            logger.info(f"Successfully assigned manager {manager.username} to store {store.name}")
            from django.contrib import messages
            if old_manager and old_manager != manager:
                messages.success(request, f"Successfully updated manager from {old_manager.username} to {manager.username} for {store.name}")
            else:
                messages.success(request, f"Successfully assigned {manager.username} to {store.name}")
            return redirect('manage_store', store_id=store.id)
            messages.success(request, f"Successfully assigned {manager.username} to {store.name}")
            return redirect('store_owner_page')
        else:
            logger.warning(f"Invalid form data: {form.errors}")
            from django.contrib import messages
            messages.error(request, "Please correct the errors below.")
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
# ============ CASHIER ORDER SYSTEM ============

@login_required
def cashier_dashboard(request):
    """
    Enhanced cashier dashboard with FIFO-ordered products for optimal inventory rotation
    """
    if request.user.role != 'cashier':
        messages.error(request, "Access denied. Cashier role required.")
        return redirect('login')

    if not request.user.store:
        messages.error(request, "You are not assigned to any store. Contact your manager.")
        return redirect('cashier_page')

    from django.utils import timezone
    from collections import defaultdict

    current_date = timezone.now().date()

    # FIFO Implementation: Get all stock including expired items (as per requirement)
    # Sort by: expiry_date (ascending), batch_number (ascending), product name
    # Note: Advanced FIFO fields will be added in future migration
    all_stock = Stock.objects.select_related('product').filter(
        store=request.user.store,
        quantity__gt=0  # Only show items in stock
    ).order_by(
        'product__expiry_date',  # Expiring items first (nulls last)
        'product__batch_number',  # Batch order
        'product__name'  # Product name for consistency
    )

    # Categorize products for display
    fifo_products = []
    sell_first_products = []  # Expiring within 30 days
    regular_products = []

    for stock in all_stock:
        # Add FIFO metadata to stock object
        stock.is_expired = False
        stock.days_until_expiry = None
        stock.fifo_priority = 'normal'

        # Add basic FIFO-specific attributes (without database fields)
        stock.days_in_stock = 0  # Will be calculated when FIFO fields are available
        stock.is_aging = False
        stock.effective_received_date = None

        if stock.product.expiry_date:
            days_until_expiry = (stock.product.expiry_date - current_date).days
            stock.days_until_expiry = days_until_expiry

            if days_until_expiry <= 0:
                stock.fifo_priority = 'expired'
                stock.is_expired = True
            elif days_until_expiry <= 30:
                stock.fifo_priority = 'sell_first'
                sell_first_products.append(stock)
            else:
                stock.fifo_priority = 'normal'
                regular_products.append(stock)
        else:
            regular_products.append(stock)

        fifo_products.append(stock)

    # Group products by batch for organized display
    products_by_batch = defaultdict(list)
    for stock in fifo_products:
        batch_key = stock.product.batch_number or 'No Batch'
        products_by_batch[batch_key].append(stock)

    # Get recent transactions for this cashier
    recent_transactions = Transaction.objects.filter(
        store=request.user.store,
        transaction_type='sale'
    ).order_by('-timestamp')[:5]

    # Get tickets data for the tickets tab
    from webfront.models import CustomerTicket, CustomerTicketItem
    from django.core.paginator import Paginator
    from django.db.models import Q

    # Get search parameters
    phone_search = request.GET.get('phone', '').strip()
    status_filter = request.GET.get('status', '').strip()
    sort_order = request.GET.get('sort', 'newest')
    page_number = request.GET.get('page', 1)

    # Get store for tickets (use same logic as API)
    store = None
    try:
        cashier = StoreCashier.objects.get(cashier=request.user, is_active=True)
        store = cashier.store
    except StoreCashier.DoesNotExist:
        if hasattr(request.user, 'store') and request.user.store:
            store = request.user.store
        else:
            store = Store.objects.first()

    # Get tickets for this store
    tickets = CustomerTicket.objects.filter(store=store).select_related('store').prefetch_related('items__product')

    # Apply search filters
    if phone_search:
        # Clean the phone search input - remove spaces, dashes, parentheses, plus signs
        cleaned_phone = ''.join(char for char in phone_search if char.isdigit())

        if cleaned_phone:
            # For database-agnostic partial phone number search
            # Get all tickets and filter in Python for better compatibility
            all_tickets_for_search = tickets.values_list('id', 'customer_phone')
            matching_ids = []

            for ticket_id, phone in all_tickets_for_search:
                if phone:
                    # Remove all non-digit characters from stored phone
                    phone_digits = ''.join(char for char in phone if char.isdigit())
                    # Check if search digits are contained in phone digits
                    if cleaned_phone in phone_digits:
                        matching_ids.append(ticket_id)

            # Filter tickets by matching IDs
            if matching_ids:
                tickets = tickets.filter(id__in=matching_ids)
            else:
                # No matches found, return empty queryset
                tickets = tickets.none()
        else:
            # If no digits found, search in the original phone field (for special characters)
            tickets = tickets.filter(customer_phone__icontains=phone_search)

    if status_filter:
        tickets = tickets.filter(status=status_filter)

    # Apply sorting
    if sort_order == 'oldest':
        tickets = tickets.order_by('created_at')
    elif sort_order == 'status':
        tickets = tickets.order_by('status', '-created_at')
    elif sort_order == 'amount':
        tickets = tickets.order_by('-total_amount', '-created_at')
    else:  # newest (default)
        tickets = tickets.order_by('-created_at')

    # Paginate tickets
    paginator = Paginator(tickets, 12)  # 12 tickets per page
    tickets_page = paginator.get_page(page_number)

    # Count pending tickets for badge
    pending_count = CustomerTicket.objects.filter(
        store=store,
        status__in=['pending', 'confirmed']
    ).count()

    # Helper functions for status display
    def get_status_color(status):
        status_colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'preparing': 'primary',
            'ready': 'success',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return status_colors.get(status, 'secondary')

    def get_status_icon(status):
        status_icons = {
            'pending': 'bi-clock',
            'confirmed': 'bi-check',
            'preparing': 'bi-gear',
            'ready': 'bi-check-circle',
            'completed': 'bi-check-all',
            'cancelled': 'bi-x-circle'
        }
        return status_icons.get(status, 'bi-question')

    # Enhance tickets with additional data
    enhanced_tickets = []
    for ticket in tickets_page:
        # Calculate total quantity
        total_quantity = sum(item.quantity for item in ticket.items.all())

        # Get items preview (first 2 items)
        items_preview = []
        for item in ticket.items.all()[:2]:
            items_preview.append({
                'quantity': item.quantity,
                'product_name': item.product.name
            })

        enhanced_ticket = {
            'ticket': ticket,
            'total_quantity': total_quantity,
            'items_count': ticket.items.count(),
            'items_preview': items_preview,
            'has_more_items': ticket.items.count() > 2,
            'status_color': get_status_color(ticket.status),
            'status_icon': get_status_icon(ticket.status)
        }
        enhanced_tickets.append(enhanced_ticket)

    # Statistics for dashboard
    total_stock_items = Stock.objects.filter(store=request.user.store).count()
    out_of_stock_items = Stock.objects.filter(store=request.user.store, quantity=0).count()
    expired_items = Stock.objects.filter(
        store=request.user.store,
        product__expiry_date__lte=current_date
    ).exclude(quantity=0).count()

    context = {
        'fifo_products': fifo_products,
        'sell_first_products': sell_first_products,
        'regular_products': regular_products,
        'products_by_batch': dict(products_by_batch),
        'recent_transactions': recent_transactions,
        'store': request.user.store,
        'current_date': current_date,
        # Tickets data
        'tickets': enhanced_tickets,
        'tickets_page': tickets_page,
        'pending_count': pending_count,
        'phone_search': phone_search,
        'status_filter': status_filter,
        'sort_order': sort_order,
        'status_choices': [
            ('', 'All Statuses'),
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('preparing', 'Preparing'),
            ('ready', 'Ready'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        'sort_choices': [
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First'),
            ('status', 'By Status'),
            ('amount', 'By Amount'),
        ],
        'debug_stats': {
            'total_stock_items': total_stock_items,
            'available_products_count': len(fifo_products),
            'out_of_stock_items': out_of_stock_items,
            'expired_items': expired_items,
            'sell_first_count': len(sell_first_products),
        }
    }

    return render(request, 'store/cashier_dashboard.html', context)





@login_required
def process_single_sale(request):
    """
    Process a single product sale with customer information
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    if request.user.role != 'cashier':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    if not request.user.store:
        return JsonResponse({'success': False, 'error': 'No store assigned'})

    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 0))
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        payment_type = request.POST.get('payment_type', 'cash')

        # Validate inputs
        if not all([product_id, quantity > 0, customer_name, customer_phone]):
            return JsonResponse({'success': False, 'error': 'All fields are required'})

        # Validate customer name (only letters and spaces)
        import re
        if not re.match(r'^[A-Za-z\s]+$', customer_name):
            return JsonResponse({'success': False, 'error': 'Customer name should only contain letters and spaces'})

        # Validate phone number (only numbers, +, spaces, hyphens, parentheses)
        if not re.match(r'^[\+]?[0-9\s\-\(\)]+$', customer_phone):
            return JsonResponse({'success': False, 'error': 'Phone number should only contain numbers and + symbol'})

        # Get product and stock
        try:
            stock = Stock.objects.select_related('product').get(
                product_id=product_id,
                store=request.user.store
            )
        except Stock.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found in store'})

        # Check stock availability
        if stock.quantity < quantity:
            return JsonResponse({'success': False, 'error': f'Only {stock.quantity} items available'})

        # Check if product is expired
        if stock.product.expiry_date:
            from django.utils import timezone
            if stock.product.expiry_date <= timezone.now().date():
                return JsonResponse({'success': False, 'error': 'Product has expired'})

        # Calculate total
        total_amount = stock.selling_price * quantity

        with transaction.atomic():
            # Create Transaction
            transaction_obj = Transaction.objects.create(
                transaction_type='sale',
                quantity=quantity,
                total_amount=total_amount,
                store=request.user.store,
                payment_type=payment_type
            )

            # Create Receipt
            receipt = Receipt.objects.create(
                transaction=transaction_obj,
                total_amount=total_amount,
                customer_name=customer_name,
                customer_phone=customer_phone
            )

            # Create Transaction Order
            TransactionOrder.objects.create(
                receipt=receipt,
                transaction=transaction_obj,
                product=stock.product,
                quantity=quantity,
                price_at_time_of_sale=stock.selling_price
            )

            # Update stock
            stock.quantity -= quantity
            stock.save()

            # Create Financial Record
            FinancialRecord.objects.create(
                store=request.user.store,
                cashier=request.user,
                amount=total_amount,
                record_type='revenue'
            )

        return JsonResponse({
            'success': True,
            'receipt_id': receipt.id,
            'total_amount': float(total_amount),
            'message': 'Sale processed successfully'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def initiate_order(request):
    """
    Cashier initiates a new order - creates a shopping cart session
    """
    if request.user.role != 'cashier':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if not request.user.store:
        return JsonResponse({'error': 'No store assigned'}, status=400)

    # Initialize or get existing cart from session
    if 'cart' not in request.session:
        request.session['cart'] = {
            'items': [],
            'total': 0,
            'created_at': timezone.now().isoformat(),
            'cashier_id': request.user.id,
            'store_id': request.user.store.id
        }
        request.session.modified = True

    # Get available products for this store
    available_products = Stock.objects.filter(
        store=request.user.store,
        quantity__gt=0
    ).select_related('product').values(
        'product__id', 'product__name', 'product__price',
        'quantity', 'selling_price'
    )

    # Get ticket information if this order is from a ticket
    ticket_info = request.session.get('ticket_info', {})

    context = {
        'available_products': list(available_products),
        'cart': request.session.get('cart', {}),
        'store': request.user.store,
        'ticket_info': ticket_info,
    }

    return render(request, 'store/initiate_order.html', context)


@login_required
def add_to_cart(request):
    """
    Add product to cart (AJAX endpoint)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    if request.user.role != 'cashier':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        # Validate product and stock
        stock = Stock.objects.get(
            product_id=product_id,
            store=request.user.store
        )

        if stock.quantity < quantity:
            return JsonResponse({
                'error': f'Insufficient stock. Available: {stock.quantity}'
            }, status=400)

        # Initialize cart if not exists
        if 'cart' not in request.session:
            request.session['cart'] = {
                'items': [],
                'total': 0,
                'created_at': timezone.now().isoformat(),
                'cashier_id': request.user.id,
                'store_id': request.user.store.id
            }

        cart = request.session['cart']

        # Check if product already in cart
        existing_item = None
        for item in cart['items']:
            if item['product_id'] == product_id:
                existing_item = item
                break

        if existing_item:
            # Update quantity
            new_quantity = existing_item['quantity'] + quantity
            if stock.quantity < new_quantity:
                return JsonResponse({
                    'error': f'Total quantity exceeds stock. Available: {stock.quantity}'
                }, status=400)
            existing_item['quantity'] = new_quantity
            existing_item['subtotal'] = float(Decimal(str(stock.selling_price)) * new_quantity)
        else:
            # Add new item
            cart['items'].append({
                'product_id': product_id,
                'product_name': stock.product.name,
                'price': float(stock.selling_price),
                'quantity': quantity,
                'subtotal': float(Decimal(str(stock.selling_price)) * quantity)
            })

        # Recalculate total
        cart['total'] = sum(item['subtotal'] for item in cart['items'])
        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'cart': cart,
            'message': f'Added {quantity} x {stock.product.name} to cart'
        })

    except Stock.DoesNotExist:
        return JsonResponse({'error': 'Product not found in store'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def remove_from_cart(request):
    """
    Remove product from cart (AJAX endpoint)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        cart = request.session.get('cart', {'items': [], 'total': 0})
        cart['items'] = [item for item in cart['items'] if item['product_id'] != product_id]
        cart['total'] = sum(item['subtotal'] for item in cart['items'])

        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'cart': cart,
            'message': 'Item removed from cart'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def complete_order(request):
    """
    Complete the order - create transaction, receipt, and clear cart
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    if request.user.role != 'cashier':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        payment_type = data.get('payment_type', 'cash')
        discount_percent = max(0, min(100, float(data.get('discount', 0))))  # Ensure discount is between 0-100
        is_taxable = data.get('taxable', False)
        customer_name = data.get('customer_name', 'Walk-in Customer')
        customer_phone = data.get('customer_phone', '')

        cart = request.session.get('cart')
        if not cart or not cart.get('items'):
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        with transaction.atomic():
            # Calculate totals - convert all to Decimal for consistency
            try:
                subtotal = Decimal(str(sum(item['subtotal'] for item in cart['items'])))
                discount_amount = subtotal * (Decimal(str(discount_percent)) / Decimal('100'))
                taxable_amount = subtotal - discount_amount
                tax_amount = taxable_amount * Decimal('0.05') if is_taxable else Decimal('0')
                total_amount = taxable_amount + tax_amount
            except (ValueError, TypeError, KeyError) as calc_error:
                return JsonResponse({'error': f'Calculation error: {str(calc_error)}'}, status=400)

            # Create main transaction
            transaction_obj = Transaction.objects.create(
                transaction_type='sale',
                quantity=sum(item['quantity'] for item in cart['items']),
                total_amount=total_amount,
                store=request.user.store,
                payment_type=payment_type
            )

            # Create receipt
            receipt = Receipt.objects.create(
                transaction=transaction_obj,
                total_amount=total_amount,
                customer_name=customer_name,
                customer_phone=customer_phone,
                subtotal=subtotal,
                discount_amount=discount_amount,
                discount_percent=Decimal(str(discount_percent)),
                tax_amount=tax_amount
            )

            # Create order entries and update stock
            order_items = []
            for item in cart['items']:
                # Get stock and update quantity
                stock = Stock.objects.select_for_update().get(
                    product_id=item['product_id'],
                    store=request.user.store
                )

                if stock.quantity < item['quantity']:
                    raise ValueError(f"Insufficient stock for {item['product_name']}")

                stock.quantity -= item['quantity']
                stock.save()

                # Create transaction order
                order = TransactionOrder.objects.create(
                    receipt=receipt,
                    transaction=transaction_obj,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price_at_time_of_sale=Decimal(str(item['price']))
                )

                order_items.append({
                    'product_name': item['product_name'],
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'subtotal': item['subtotal']
                })

            # Create financial record
            FinancialRecord.objects.create(
                store=request.user.store,
                cashier=request.user,
                amount=total_amount,
                record_type='revenue'
            )

            # Update ticket status if this order was from a ticket
            ticket_info = request.session.get('ticket_info', {})
            if ticket_info.get('from_ticket') and ticket_info.get('ticket_number'):
                try:
                    ticket = CustomerTicket.objects.get(
                        ticket_number=ticket_info['ticket_number'],
                        store=request.user.store
                    )
                    ticket.status = 'completed'
                    ticket.completed_at = timezone.now()
                    ticket.confirmed_by = request.user
                    ticket.save()
                except CustomerTicket.DoesNotExist:
                    pass  # Ticket not found, continue without error

            # Clear cart and ticket info
            if 'cart' in request.session:
                del request.session['cart']
                request.session.modified = True
            if 'ticket_info' in request.session:
                del request.session['ticket_info']
                request.session.modified = True

            return JsonResponse({
                'success': True,
                'transaction_id': transaction_obj.id,
                'receipt_id': receipt.id,
                'total_amount': float(total_amount),
                'order_items': order_items,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'payment_type': payment_type,
                'discount_amount': float(discount_amount),
                'discount_percent': discount_percent,
                'tax_amount': float(tax_amount),
                'subtotal': float(subtotal),
                'message': 'Order completed successfully',
                'receipt_url': f'/stores/receipt/{receipt.id}/',
                'receipt_pdf_url': f'/stores/receipt/{receipt.id}/pdf/',
            })

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Order completion failed: {str(e)}'}, status=500)


@login_required
def generate_receipt_pdf(request, receipt_id):
    """
    Generate and download receipt as PDF
    """
    if request.user.role != 'cashier':
        return HttpResponse("Unauthorized", status=403)

    try:
        receipt = get_object_or_404(Receipt, id=receipt_id)
        transaction_obj = receipt.transaction

        # Verify cashier has access to this receipt
        if transaction_obj.store != request.user.store:
            return HttpResponse("Access denied", status=403)

        # Get order items
        order_items = TransactionOrder.objects.filter(
            transaction=transaction_obj
        ).select_related('receipt', 'product')

        # Calculate breakdown
        subtotal_before_tax = sum(item.quantity * item.price_at_time_of_sale for item in order_items)

        # Calculate tax (5% of total) - convert to Decimal for proper calculation
        from decimal import Decimal
        tax_rate = Decimal('0.05')
        tax_divisor = Decimal('1.05')
        tax_amount = receipt.total_amount * tax_rate / tax_divisor  # Reverse calculate tax from total
        subtotal = receipt.total_amount - tax_amount

        # Add subtotal to each item for template
        for item in order_items:
            item.subtotal = item.quantity * item.price_at_time_of_sale

        context = {
            'receipt': receipt,
            'transaction': transaction_obj,
            'order_items': order_items,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'store': transaction_obj.store,
            'cashier': request.user,
            'timestamp': transaction_obj.timestamp,
            'customer_name': receipt.customer_name,
            'customer_phone': receipt.customer_phone,
            'payment_method': transaction_obj.payment_type,
        }

        # Render HTML template
        receipt_html = render_to_string('store/receipt_pdf_template.html', context)

        # Generate PDF using weasyprint with error handling
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration

            # Create font configuration for better PDF rendering
            font_config = FontConfiguration()

            # Add basic CSS for better PDF formatting
            css = CSS(string='''
                @page {
                    size: A4;
                    margin: 1cm;
                }
                body {
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    line-height: 1.4;
                }
                .header {
                    text-align: center;
                    margin-bottom: 20px;
                }
                .store-name {
                    font-size: 18px;
                    font-weight: bold;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                .total-line {
                    font-weight: bold;
                }
            ''', font_config=font_config)

            # Generate PDF
            html_doc = HTML(string=receipt_html)
            pdf = html_doc.write_pdf(stylesheets=[css], font_config=font_config)

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="receipt_{receipt_id}.pdf"'
            return response

        except ImportError:
            # Fallback: If weasyprint is not available, return HTML view
            messages.warning(request, "PDF generation not available. Showing receipt in browser.")
            return HttpResponse(receipt_html, content_type='text/html')

        except Exception as pdf_error:
            print(f"PDF Generation Error: {str(pdf_error)}")
            # Fallback: Return HTML view if PDF generation fails
            messages.warning(request, f"PDF generation failed: {str(pdf_error)}. Showing receipt in browser.")
            return HttpResponse(receipt_html, content_type='text/html')

    except Exception as e:
        print(f"Receipt Generation Error: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full traceback
        messages.error(request, f"Error generating receipt: {str(e)}")
        return redirect('cashier_dashboard')


@login_required
def view_receipt(request, receipt_id):
    """
    View receipt details in browser
    """
    if request.user.role != 'cashier':
        messages.error(request, "Access denied")
        return redirect('login')

    try:
        receipt = get_object_or_404(Receipt, id=receipt_id)
        transaction_obj = receipt.transaction

        # Verify access
        if transaction_obj.store != request.user.store:
            messages.error(request, "Access denied to this receipt")
            return redirect('cashier_dashboard')

        # Get order items
        order_items = TransactionOrder.objects.filter(
            transaction=transaction_obj
        ).select_related('receipt', 'product')

        # Add subtotal to each item for template
        for item in order_items:
            item.subtotal = item.quantity * item.price_at_time_of_sale

        context = {
            'receipt': receipt,
            'transaction': transaction_obj,
            'order_items': order_items,
            'store': transaction_obj.store,
            'customer_name': receipt.customer_name,
            'customer_phone': receipt.customer_phone,
        }

        return render(request, 'store/view_receipt.html', context)
    except Exception as e:
        messages.error(request, f"Error viewing receipt: {str(e)}")
        return redirect('cashier_dashboard')


@login_required
def approve_store_transfer_request(request, request_id):
    """
    Handle transfer request approval by store manager for incoming requests.
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_transfer_requests')

    if request.method == 'POST':
        from Inventory.models import StoreStockTransferRequest, Stock
        from django.utils import timezone
        import json

        try:
            # Get the transfer request - must be FROM this store (source)
            transfer_request = StoreStockTransferRequest.objects.get(
                id=request_id,
                from_store=store,  # This store is the source
                status='pending'
            )

            # Parse data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                approved_quantity = int(data.get('approved_quantity', transfer_request.requested_quantity))
                review_notes = data.get('review_notes', '').strip()
            else:
                approved_quantity = int(request.POST.get('approved_quantity', transfer_request.requested_quantity))
                review_notes = request.POST.get('review_notes', '').strip()

            # Validation
            if approved_quantity <= 0:
                error_msg = "Approved quantity must be greater than 0."
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('store_manager_transfer_requests')

            # Check if source store has sufficient stock
            source_stock = Stock.objects.filter(
                store=store,  # This store (source)
                product=transfer_request.product
            ).first()

            if not source_stock or source_stock.quantity < approved_quantity:
                error_msg = f"Insufficient stock. Available: {source_stock.quantity if source_stock else 0}, Requested: {approved_quantity}"
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('store_manager_transfer_requests')

            # Update transfer request
            transfer_request.status = 'approved'
            transfer_request.approved_quantity = approved_quantity
            transfer_request.reviewed_by = request.user
            transfer_request.reviewed_date = timezone.now()
            transfer_request.review_notes = review_notes
            transfer_request.save()

            # Transfer stock
            # Reduce stock from source store (this store)
            source_stock.quantity -= approved_quantity
            source_stock.last_updated = timezone.now()
            source_stock.save()

            # Add stock to destination store
            dest_stock, _ = Stock.objects.get_or_create(
                store=transfer_request.to_store,
                product=transfer_request.product,
                defaults={
                    'quantity': 0,
                    'low_stock_threshold': 10,
                    'selling_price': source_stock.selling_price,
                    'last_updated': timezone.now()
                }
            )
            dest_stock.quantity += approved_quantity
            dest_stock.last_updated = timezone.now()
            dest_stock.save()

            success_msg = f"Transfer request #{transfer_request.request_number} approved. {approved_quantity} units transferred to {transfer_request.to_store.name}."

            if request.content_type == 'application/json':
                return JsonResponse({'success': True, 'message': success_msg})

            messages.success(request, success_msg)

        except StoreStockTransferRequest.DoesNotExist:
            error_msg = "Transfer request not found or already processed."
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
        except (ValueError, json.JSONDecodeError) as e:
            error_msg = "Invalid quantity or data format."
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)

    return redirect('store_manager_transfer_requests')


@login_required
def decline_store_transfer_request(request, request_id):
    """
    Handle transfer request decline by store manager for incoming requests.
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_transfer_requests')

    if request.method == 'POST':
        from Inventory.models import StoreStockTransferRequest
        from django.utils import timezone
        import json

        try:
            # Get the transfer request - must be FROM this store (source)
            transfer_request = StoreStockTransferRequest.objects.get(
                id=request_id,
                from_store=store,  # This store is the source
                status='pending'
            )

            # Parse data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                review_notes = data.get('reason', '').strip()
            else:
                review_notes = request.POST.get('reason', '').strip()

            # Require a reason for declining
            if not review_notes:
                error_msg = "Please provide a reason for declining this transfer request."
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('store_manager_transfer_requests')

            # Update transfer request
            transfer_request.status = 'rejected'
            transfer_request.reviewed_by = request.user
            transfer_request.reviewed_date = timezone.now()
            transfer_request.review_notes = review_notes
            transfer_request.save()

            success_msg = f"Transfer request #{transfer_request.request_number} declined."

            if request.content_type == 'application/json':
                return JsonResponse({'success': True, 'message': success_msg})

            messages.success(request, success_msg)

        except StoreStockTransferRequest.DoesNotExist:
            error_msg = "Transfer request not found or already processed."
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)

    return redirect('store_manager_transfer_requests')


@login_required
def complete_store_transfer_request(request, request_id):
    """
    Handle marking approved transfer requests as completed by the receiving store manager.
    Only the receiving store manager (to_store) can mark approved requests as completed.
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_transfer_requests')

    if request.method == 'POST':
        from Inventory.models import StoreStockTransferRequest
        from django.utils import timezone
        import json

        try:
            # Get the transfer request - must be TO this store (destination) and approved
            transfer_request = StoreStockTransferRequest.objects.get(
                id=request_id,
                to_store=store,  # This store is the destination (receiving store)
                status='approved'
            )

            # Parse data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                completion_notes = data.get('completion_notes', '').strip()
            else:
                completion_notes = request.POST.get('completion_notes', '').strip()

            # Update request status to completed
            transfer_request.status = 'completed'
            transfer_request.review_notes = completion_notes or f"Transfer completed by {request.user.get_full_name() or request.user.username}"
            transfer_request.reviewed_by = request.user
            transfer_request.reviewed_date = timezone.now()
            transfer_request.save()

            # Success response
            success_msg = f"Transfer request {transfer_request.request_number} marked as completed successfully."

            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'request_number': transfer_request.request_number,
                    'status': transfer_request.status
                })

            messages.success(request, success_msg)

        except StoreStockTransferRequest.DoesNotExist:
            error_msg = "Transfer request not found, not approved, or you don't have permission to complete it."
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)

        except Exception as e:
            error_msg = f"Error completing transfer request: {str(e)}"
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)

        return redirect('store_manager_transfer_requests')

    return redirect('store_manager_transfer_requests')


@login_required
def get_cart_status(request):
    """
    Get current cart status (AJAX endpoint)
    """
    cart = request.session.get('cart', {'items': [], 'total': 0})
    return JsonResponse({'cart': cart})


@login_required
def email_receipt(request, receipt_id):
    """
    Email receipt to customer
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    if request.user.role != 'cashier':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        customer_email = data.get('email', '').strip()

        if not customer_email:
            return JsonResponse({'error': 'Email address is required'}, status=400)

        # Validate email format
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(customer_email)
        except ValidationError:
            return JsonResponse({'error': 'Invalid email address'}, status=400)

        receipt = get_object_or_404(Receipt, id=receipt_id)
        transaction_obj = receipt.transaction

        # Verify cashier has access to this receipt
        if transaction_obj.store != request.user.store:
            return JsonResponse({'error': 'Access denied'}, status=403)

        # Get order items
        order_items = TransactionOrder.objects.filter(
            transaction=transaction_obj
        ).select_related('receipt', 'product')

        # Calculate breakdown
        subtotal = sum(item.quantity * item.price_at_time_of_sale for item in order_items)

        # Add subtotal to each item for template
        for item in order_items:
            item.subtotal = item.quantity * item.price_at_time_of_sale

        context = {
            'receipt': receipt,
            'transaction': transaction_obj,
            'order_items': order_items,
            'subtotal': receipt.subtotal,
            'store': transaction_obj.store,
            'cashier': request.user,
            'timestamp': transaction_obj.timestamp,
            'customer_name': receipt.customer_name,
            'customer_phone': receipt.customer_phone,
            'discount_amount': receipt.discount_amount,
            'discount_percent': receipt.discount_percent,
            'tax_amount': receipt.tax_amount,
            'payment_method': transaction_obj.payment_type,
        }

        # Generate PDF with error handling
        receipt_html = render_to_string('store/receipt_pdf_template.html', context)
        pdf = None

        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration

            # Create font configuration for better PDF rendering
            font_config = FontConfiguration()

            # Add basic CSS for email PDF
            css = CSS(string='''
                @page {
                    size: A4;
                    margin: 1cm;
                }
                body {
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    line-height: 1.4;
                }
                .header {
                    text-align: center;
                    margin-bottom: 20px;
                }
                .store-name {
                    font-size: 18px;
                    font-weight: bold;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                .total-line {
                    font-weight: bold;
                }
            ''', font_config=font_config)

            # Generate PDF
            html_doc = HTML(string=receipt_html)
            pdf = html_doc.write_pdf(stylesheets=[css], font_config=font_config)

        except ImportError:
            print("WeasyPrint not available for PDF generation")
            pdf = None
        except Exception as pdf_error:
            print(f"PDF generation failed: {pdf_error}")
            pdf = None

        # Send email
        from django.core.mail import EmailMessage
        from django.conf import settings

        subject = f'Receipt from {transaction_obj.store.name} - #{receipt.id}'
        message = f"""
Dear Customer,

Thank you for your purchase at {transaction_obj.store.name}!

Please find your receipt attached to this email.

Transaction Details:
- Receipt #: {receipt.id}
- Date: {transaction_obj.timestamp.strftime('%B %d, %Y at %I:%M %p')}
- Total Amount: ${receipt.total_amount}
- Payment Method: {transaction_obj.get_payment_type_display()}

We appreciate your business and look forward to serving you again.

Best regards,
{transaction_obj.store.name}
Phone: {transaction_obj.store.phone_number}
        """.strip()

        # Create email message
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@store.com'),
            to=[customer_email],
        )

        # Attach PDF if available, otherwise send HTML receipt
        if pdf:
            email.attach(
                f'receipt_{receipt.id}.pdf',
                pdf,
                'application/pdf'
            )
        else:
            # Fallback: attach HTML receipt if PDF generation failed
            email.attach(
                f'receipt_{receipt.id}.html',
                receipt_html.encode('utf-8'),
                'text/html'
            )

        # Send email with comprehensive error handling
        email_sent = False
        error_message = None

        try:
            # Check if email backend is configured
            if not hasattr(settings, 'EMAIL_BACKEND') or not settings.EMAIL_BACKEND:
                # Use console backend for development
                from django.core.mail import get_connection
                connection = get_connection('django.core.mail.backends.console.EmailBackend')
                email.connection = connection

            # Send email synchronously for better error handling
            email.send()
            email_sent = True

        except Exception as email_error:
            error_message = str(email_error)
            print(f"Failed to send email: {email_error}")

            # Try alternative: save email content to session for manual sending
            request.session[f'pending_email_{receipt.id}'] = {
                'to': customer_email,
                'subject': subject,
                'body': message,
                'receipt_html': receipt_html,
                'timestamp': transaction_obj.timestamp.isoformat()
            }

        if email_sent:
            return JsonResponse({
                'success': True,
                'message': f'Receipt has been sent to {customer_email}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'Email could not be sent: {error_message}. Receipt saved for manual sending.',
                'fallback': True
            })

    except Exception as e:
        return JsonResponse({'error': f'Failed to send email: {str(e)}'}, status=500)


# ============ STORE MANAGER CASHIER ASSIGNMENT ============

@login_required
def assign_cashier(request, store_id=None):
    """
    Store manager assigns a cashier to their store
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store manager role required.")
        return redirect('login')

    # Get the store managed by this user
    try:
        if store_id:
            store = get_object_or_404(Store, id=store_id, store_manager=request.user)
        else:
            store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    if request.method == 'POST':
        form = AssignCashierForm(request.POST)
        if form.is_valid():
            cashier = form.cleaned_data['cashier']

            # Assign cashier to store
            cashier.store = store
            cashier.save()

            # Create or update StoreCashier record
            store_cashier, created = StoreCashier.objects.get_or_create(
                store=store,
                cashier=cashier,
                defaults={'is_active': True}
            )
            if not created:
                store_cashier.is_active = True
                store_cashier.save()

            messages.success(request, f"Successfully assigned {cashier.get_full_name() or cashier.username} as cashier for {store.name}")
            return redirect('store_manager_page')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AssignCashierForm()

    # Get currently assigned cashiers
    assigned_cashiers = CustomUser.objects.filter(
        store=store,
        role='cashier',
        is_active=True
    )

    context = {
        'form': form,
        'store': store,
        'assigned_cashiers': assigned_cashiers,
    }

    return render(request, 'store/assign_cashier.html', context)


@login_required
def remove_cashier(request, cashier_id):
    """
    Store manager removes a cashier from their store
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
        cashier = get_object_or_404(CustomUser, id=cashier_id, store=store, role='cashier')

        # Remove cashier from store
        cashier.store = None
        cashier.save()

        # Deactivate StoreCashier record
        StoreCashier.objects.filter(store=store, cashier=cashier).update(is_active=False)

        messages.success(request, f"Successfully removed {cashier.get_full_name() or cashier.username} from {store.name}")

    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
    except Exception as e:
        messages.error(request, f"Error removing cashier: {str(e)}")

    return redirect('store_manager_page')


@login_required
def manage_cashiers(request):
    """
    Store manager view to manage all cashiers for their store
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    # Get assigned cashiers
    assigned_cashiers = CustomUser.objects.filter(
        store=store,
        role='cashier',
        is_active=True
    )

    # Get available cashiers (not assigned to any store)
    available_cashiers = CustomUser.objects.filter(
        role='cashier',
        is_active=True,
        store__isnull=True
    )

    context = {
        'store': store,
        'assigned_cashiers': assigned_cashiers,
        'available_cashiers': available_cashiers,
    }

    return render(request, 'store/manage_cashiers.html', context)


@login_required
def store_product_list(request):
    """
    List products available in the specific store manager's store with search functionality.
    """
    # Ensure user is a store manager
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        # Get the store managed by the current user
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    # Get search term from request
    search_term = request.GET.get('search', '').strip()

    # Get stock items for this specific store
    from Inventory.models import Stock
    stock_queryset = Stock.objects.filter(store=store).select_related('product')

    # Apply search filter if provided
    if search_term:
        stock_queryset = stock_queryset.filter(
            models.Q(product__name__icontains=search_term) |
            models.Q(product__category__icontains=search_term) |
            models.Q(product__description__icontains=search_term) |
            models.Q(product__batch_number__icontains=search_term)
        )

    # Order by product name for consistent display
    stock_queryset = stock_queryset.order_by('product__name')

    # Prepare product data with stock information
    product_data = []
    for stock in stock_queryset:
        product_data.append({
            'product': stock.product,
            'quantity': stock.quantity,
            'selling_price': stock.selling_price,
            'low_stock_threshold': stock.low_stock_threshold,
            'is_low_stock': stock.quantity <= stock.low_stock_threshold,
            'stock_id': stock.id
        })

    context = {
        'product_data': product_data,
        'search_term': search_term,
        'store': store,
        'total_products': len(product_data)
    }
    return render(request, 'store/product_list.html', context)


# --- Ticket Management API Views ---

def api_tickets_list(request):
    """
    API endpoint to get tickets for the current store with search and filtering
    """
    print(f"API tickets list called - Method: {request.method}")

    # Temporarily disable auth for debugging
    # if request.user.role != 'cashier':
    #     return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        # Simplified store resolution for debugging
        store = Store.objects.first()
        print(f"Found store: {store}")

        if not store:
            return JsonResponse({
                'success': False,
                'error': 'No stores available in the system'
            }, status=400)

        # Start with all tickets for this store
        tickets = CustomerTicket.objects.filter(store=store).select_related('store').prefetch_related('items__product')
        print(f"Found {tickets.count()} tickets for store {store.name}")

        # Apply search filters
        phone_search = request.GET.get('phone', '').strip()
        status_filter = request.GET.get('status', '').strip()
        print(f"Search filters - phone: '{phone_search}', status: '{status_filter}'")

        if phone_search:
            # Clean the phone search input - remove spaces, dashes, parentheses, plus signs
            cleaned_phone = ''.join(char for char in phone_search if char.isdigit())

            if cleaned_phone:
                # For database-agnostic partial phone number search
                all_tickets_for_search = tickets.values_list('id', 'customer_phone')
                matching_ids = []

                for ticket_id, phone in all_tickets_for_search:
                    if phone:
                        # Remove all non-digit characters from stored phone
                        phone_digits = ''.join(char for char in phone if char.isdigit())
                        # Check if search digits are contained in phone digits
                        if cleaned_phone in phone_digits:
                            matching_ids.append(ticket_id)

                # Filter tickets by matching IDs
                if matching_ids:
                    tickets = tickets.filter(id__in=matching_ids)
                else:
                    # No matches found, return empty queryset
                    tickets = tickets.none()
            else:
                # If no digits found, search in the original phone field (for special characters)
                tickets = tickets.filter(customer_phone__icontains=phone_search)

        if status_filter:
            tickets = tickets.filter(status=status_filter)

        # Order by creation date (newest first by default)
        tickets = tickets.order_by('-created_at')
        print(f"Final ticket count after filters: {tickets.count()}")

        # Count pending tickets (for badge)
        all_tickets = CustomerTicket.objects.filter(store=store)
        pending_count = all_tickets.filter(status__in=['pending', 'confirmed']).count()
        print(f"Pending tickets count: {pending_count}")

        # Serialize tickets with detailed information
        tickets_data = []
        for ticket in tickets:
            # Get ticket items with product details
            items_data = []
            for item in ticket.items.select_related('product').all():
                items_data.append({
                    'id': item.id,
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'product_code': getattr(item.product, 'code', ''),
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'total_price': str(item.total_price),
                    'created_at': item.created_at.isoformat() if hasattr(item, 'created_at') else ''
                })

            # Calculate summary information
            total_quantity = sum(item.quantity for item in ticket.items.all())

            tickets_data.append({
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'customer_name': ticket.customer_name or '',
                'customer_phone': ticket.customer_phone,
                'total_amount': str(ticket.total_amount),
                'total_items': ticket.total_items,
                'total_quantity': total_quantity,
                'status': ticket.status,
                'notes': ticket.notes or '',
                'store_name': ticket.store.name,
                'store_id': ticket.store.id,
                'created_at': ticket.created_at.isoformat(),
                'updated_at': ticket.updated_at.isoformat(),
                'confirmed_at': ticket.confirmed_at.isoformat() if ticket.confirmed_at else None,
                'ready_at': ticket.ready_at.isoformat() if ticket.ready_at else None,
                'completed_at': ticket.completed_at.isoformat() if ticket.completed_at else None,
                'confirmed_by': ticket.confirmed_by.get_full_name() if ticket.confirmed_by else None,
                'items': items_data,
                'items_count': len(items_data)
            })

        response_data = {
            'success': True,
            'tickets': tickets_data,
            'pending_count': pending_count
        }
        print(f"Returning response with {len(tickets_data)} tickets")
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Error in api_tickets_list: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def api_ticket_detail(request, ticket_number):
    """
    API endpoint to get detailed ticket information
    """
    if request.user.role != 'cashier':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        # Get cashier's store - try multiple approaches
        store = None

        try:
            cashier = StoreCashier.objects.get(cashier=request.user, is_active=True)
            store = cashier.store
        except StoreCashier.DoesNotExist:
            if hasattr(request.user, 'store') and request.user.store:
                store = request.user.store
            else:
                store = Store.objects.first()

        if not store:
            return JsonResponse({'success': False, 'error': 'Cashier not assigned to any store'}, status=400)

        # Get ticket
        ticket = CustomerTicket.objects.select_related('store').prefetch_related('items__product').get(
            ticket_number=ticket_number,
            store=store
        )

        # Serialize ticket items with detailed information
        items_data = []
        for item in ticket.items.select_related('product').all():
            items_data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_code': getattr(item.product, 'code', ''),
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'total_price': str(item.total_price),
                'created_at': item.created_at.isoformat() if hasattr(item, 'created_at') else ''
            })

        # Calculate summary information
        total_quantity = sum(item.quantity for item in ticket.items.all())

        ticket_data = {
            'id': ticket.id,
            'ticket_number': ticket.ticket_number,
            'customer_name': ticket.customer_name or '',
            'customer_phone': ticket.customer_phone,
            'total_amount': str(ticket.total_amount),
            'total_items': ticket.total_items,
            'total_quantity': total_quantity,
            'status': ticket.status,
            'notes': ticket.notes or '',
            'store_name': ticket.store.name,
            'store_id': ticket.store.id,
            'created_at': ticket.created_at.isoformat(),
            'updated_at': ticket.updated_at.isoformat(),
            'confirmed_at': ticket.confirmed_at.isoformat() if ticket.confirmed_at else None,
            'ready_at': ticket.ready_at.isoformat() if ticket.ready_at else None,
            'completed_at': ticket.completed_at.isoformat() if ticket.completed_at else None,
            'confirmed_by': ticket.confirmed_by.get_full_name() if ticket.confirmed_by else None,
            'items': items_data,
            'items_count': len(items_data)
        }

        return JsonResponse({
            'success': True,
            'ticket': ticket_data
        })

    except CustomerTicket.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_ticket_update_status(request, ticket_number):
    """
    API endpoint to update ticket status
    """
    if request.user.role != 'cashier':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        notes = data.get('notes', '')

        if not new_status:
            return JsonResponse({'success': False, 'error': 'Status is required'}, status=400)

        # Validate status
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

        # Get cashier's store
        store = None
        try:
            cashier = StoreCashier.objects.get(cashier=request.user, is_active=True)
            store = cashier.store
        except StoreCashier.DoesNotExist:
            if hasattr(request.user, 'store') and request.user.store:
                store = request.user.store
            else:
                store = Store.objects.first()

        if not store:
            return JsonResponse({'success': False, 'error': 'Cashier not assigned to any store'}, status=400)

        # Get and update ticket
        ticket = CustomerTicket.objects.get(ticket_number=ticket_number, store=store)

        old_status = ticket.status
        ticket.status = new_status

        # Set timestamps based on status
        if new_status == 'confirmed' and old_status == 'pending':
            ticket.confirmed_at = timezone.now()
            ticket.confirmed_by = request.user
        elif new_status == 'ready':
            ticket.ready_at = timezone.now()
        elif new_status == 'completed':
            ticket.completed_at = timezone.now()

        ticket.save()

        return JsonResponse({
            'success': True,
            'message': f'Ticket status updated to {new_status}'
        })

    except CustomerTicket.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ticket not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_ticket_process(request, ticket_number):
    """
    API endpoint to process ticket as POS sale
    """
    if request.user.role != 'cashier':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        # Get cashier's store
        store = None
        try:
            cashier = StoreCashier.objects.get(cashier=request.user, is_active=True)
            store = cashier.store
        except StoreCashier.DoesNotExist:
            if hasattr(request.user, 'store') and request.user.store:
                store = request.user.store
            else:
                store = Store.objects.first()

        if not store:
            return JsonResponse({'success': False, 'error': 'Cashier not assigned to any store'}, status=400)

        # Get ticket
        ticket = CustomerTicket.objects.select_related('store').prefetch_related('items__product', 'items__stock').get(
            ticket_number=ticket_number,
            store=store
        )

        # Check if ticket can be processed
        if ticket.status not in ['pending', 'confirmed']:
            return JsonResponse({'success': False, 'error': 'Ticket cannot be processed in current status'}, status=400)

        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                cashier=request.user,
                store=store,
                customer_phone=ticket.customer_phone,
                customer_name=ticket.customer_name,
                total_amount=ticket.total_amount,
                notes=f"Processed from ticket #{ticket.ticket_number}. Original notes: {ticket.notes}"
            )

            # Process each item
            for ticket_item in ticket.items.all():
                # Get current stock
                try:
                    stock = Stock.objects.get(product=ticket_item.product, store=store)

                    # Check if enough stock is available
                    if stock.quantity < ticket_item.quantity:
                        return JsonResponse({
                            'success': False,
                            'error': f'Insufficient stock for {ticket_item.product.name}. Available: {stock.quantity}, Required: {ticket_item.quantity}'
                        }, status=400)

                    # Update stock
                    stock.quantity -= ticket_item.quantity
                    stock.save()

                    # Create transaction record
                    Transaction.objects.create(
                        product=ticket_item.product,
                        store=store,
                        transaction_type='sale',
                        quantity=ticket_item.quantity,
                        unit_price=ticket_item.unit_price,
                        total_amount=ticket_item.total_price,
                        performed_by=request.user,
                        notes=f"POS sale from ticket #{ticket.ticket_number}"
                    )

                except Stock.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Product {ticket_item.product.name} not available in store stock'
                    }, status=400)

            # Update ticket status
            ticket.status = 'completed'
            ticket.completed_at = timezone.now()
            ticket.confirmed_by = request.user
            ticket.save()

            # Create receipt
            receipt = Receipt.objects.create(
                order=order,
                receipt_number=f"R{order.id:06d}",
                total_amount=order.total_amount,
                payment_method='cash',  # Default to cash for ticket processing
                issued_by=request.user
            )

        return JsonResponse({
            'success': True,
            'message': 'Ticket processed successfully',
            'sale_id': order.id,
            'receipt_id': receipt.id
        })

    except CustomerTicket.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ticket not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def process_ticket_to_order(request, ticket_number):
    """
    Process a ticket by loading its data into the cart and redirecting to initiate-order
    """
    if request.user.role != 'cashier':
        messages.error(request, 'Unauthorized access.')
        return redirect('cashier_dashboard')

    try:
        # Get store for tickets
        store = None
        try:
            cashier = StoreCashier.objects.get(cashier=request.user, is_active=True)
            store = cashier.store
        except StoreCashier.DoesNotExist:
            if hasattr(request.user, 'store') and request.user.store:
                store = request.user.store
            else:
                store = Store.objects.first()

        if not store:
            messages.error(request, 'Cashier not assigned to any store.')
            return redirect('cashier_dashboard')

        # Get ticket
        ticket = CustomerTicket.objects.select_related('store').prefetch_related('items__product').get(
            ticket_number=ticket_number,
            store=store
        )

        # Check if ticket can be processed
        if ticket.status in ['completed', 'cancelled']:
            messages.warning(request, f'Ticket #{ticket_number} cannot be processed as it is already {ticket.status}.')
            return redirect('cashier_dashboard')

        # Build cart data from ticket
        cart_items = []
        for item in ticket.items.all():
            # Check if product exists in current store stock
            try:
                stock = Stock.objects.get(product=item.product, store=store)
                if stock.quantity >= item.quantity:
                    cart_items.append({
                        'product_id': item.product.id,
                        'product_name': item.product.name,
                        'price': float(item.unit_price),
                        'quantity': item.quantity,
                        'subtotal': float(item.total_price),
                        'stock_available': stock.quantity
                    })
                else:
                    messages.warning(request, f'Insufficient stock for {item.product.name}. Available: {stock.quantity}, Required: {item.quantity}')
            except Stock.DoesNotExist:
                messages.warning(request, f'Product {item.product.name} not available in current store.')

        # Store cart data and ticket info in session
        request.session['cart'] = {
            'items': cart_items,
            'total': sum(item['subtotal'] for item in cart_items)
        }

        # Store ticket information for order completion
        request.session['ticket_info'] = {
            'ticket_number': ticket.ticket_number,
            'customer_name': ticket.customer_name or '',
            'customer_phone': ticket.customer_phone or '',
            'notes': ticket.notes or '',
            'from_ticket': True
        }

        # Add success message
        messages.success(request, f'Ticket #{ticket_number} loaded into cart. Complete the order to process the ticket.')

        # Redirect to initiate-order page
        return redirect('initiate_order')

    except CustomerTicket.DoesNotExist:
        messages.error(request, f'Ticket #{ticket_number} not found.')
        return redirect('cashier_dashboard')
    except Exception as e:
        messages.error(request, f'Error processing ticket: {str(e)}')
        return redirect('cashier_dashboard')
