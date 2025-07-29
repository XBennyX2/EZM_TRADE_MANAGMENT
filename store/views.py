from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from Inventory.models import Product, Stock
from transactions.models import Transaction, Receipt, Order as TransactionOrder, FinancialRecord
from .models import Order, Store, StoreCashier
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
        discount = 0  # No discount allowed
        taxable = True  # Always apply tax (15%)
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
                tax = total * 0.15 if taxable else 0
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

# Cashier dashboard removed - cashiers go directly to initiate_order



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
    Cashier Point of Sale interface - focused on order processing only
    """
    if request.user.role != 'cashier':
        messages.error(request, "Access denied. Cashier role required.")
        return redirect('login')

    if not request.user.store:
        messages.error(request, "You are not assigned to any store. Contact your manager.")
        return redirect('cashier_page')

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

    cart = request.session.get('cart', {})
    print(f"DEBUG: initiate_order view - cart from session: {cart}")

    context = {
        'available_products': list(available_products),
        'cart': cart,
        'store': request.user.store,
        'ticket_info': ticket_info,
    }

    return render(request, 'store/initiate_order.html', context)


@login_required
def ticket_management(request):
    """
    Dedicated ticket management interface for cashiers
    """
    if request.user.role != 'cashier':
        messages.error(request, "Access denied. Cashier role required.")
        return redirect('login')

    if not request.user.store:
        messages.error(request, "You are not assigned to any store. Contact your manager.")
        return redirect('cashier_page')

    # Customer Tickets functionality
    from webfront.models import CustomerTicket

    # Get search parameters
    search_query = request.GET.get('search', '').strip()  # Combined search for phone and ticket number
    phone_search = request.GET.get('phone', '').strip()  # Keep for backward compatibility
    status_filter = request.GET.get('status', '')  # Show all statuses by default
    sort_order = request.GET.get('sort', 'newest')

    # Use search_query if provided, otherwise fall back to phone_search
    if search_query:
        phone_search = search_query

    # Base queryset for tickets - only show pending and completed tickets
    tickets_queryset = CustomerTicket.objects.filter(
        store=request.user.store,
        status__in=['pending', 'completed']
    ).select_related('store', 'confirmed_by').prefetch_related('items__product')

    # Apply search filter - enhanced to search both phone and ticket number
    if phone_search:
        # Check if search looks like a ticket number (starts with CT and contains letters/numbers)
        if phone_search.upper().startswith('CT') and len(phone_search) > 2:
            # Search by ticket number
            tickets_queryset = tickets_queryset.filter(ticket_number__icontains=phone_search.upper())
        else:
            # Search by phone number
            # Remove any non-digit characters for flexible search
            phone_digits = ''.join(filter(str.isdigit, phone_search))
            if phone_digits:
                tickets_queryset = tickets_queryset.filter(
                    customer_phone__icontains=phone_digits
                )
            else:
                # If no digits found, search in both phone and ticket number fields
                tickets_queryset = tickets_queryset.filter(
                    models.Q(customer_phone__icontains=phone_search) |
                    models.Q(ticket_number__icontains=phone_search.upper())
                )

    # Apply status filter
    if status_filter:
        tickets_queryset = tickets_queryset.filter(status=status_filter)

    # Apply sorting
    if sort_order == 'oldest':
        tickets_queryset = tickets_queryset.order_by('created_at')
    elif sort_order == 'status':
        tickets_queryset = tickets_queryset.order_by('status', '-created_at')
    elif sort_order == 'amount':
        tickets_queryset = tickets_queryset.order_by('-total_amount', '-created_at')
    else:  # newest (default)
        tickets_queryset = tickets_queryset.order_by('-created_at')

    # Get tickets with enhanced data
    tickets = []
    for ticket in tickets_queryset[:20]:  # Limit to 20 tickets for performance
        # Get ticket items
        items = list(ticket.items.all())

        # Calculate totals
        total_quantity = sum(item.quantity for item in items)
        items_count = len(items)

        # Get items preview (first 2 items)
        items_preview = items[:2]
        has_more_items = items_count > 2

        # Status styling
        status_colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'preparing': 'primary',
            'ready': 'success',
            'completed': 'success',
            'cancelled': 'secondary'
        }

        status_icons = {
            'pending': 'bi-clock',
            'confirmed': 'bi-check-circle',
            'preparing': 'bi-gear',
            'ready': 'bi-check2-circle',
            'completed': 'bi-check-circle-fill',
            'cancelled': 'bi-x-circle'
        }

        tickets.append({
            'ticket': ticket,
            'total_quantity': total_quantity,
            'items_count': items_count,
            'items_preview': items_preview,
            'has_more_items': has_more_items,
            'status_color': status_colors.get(ticket.status, 'secondary'),
            'status_icon': status_icons.get(ticket.status, 'bi-question-circle')
        })

    # Count tickets by status (only pending and completed)
    pending_count = CustomerTicket.objects.filter(
        store=request.user.store,
        status='pending'
    ).count()

    completed_count = CustomerTicket.objects.filter(
        store=request.user.store,
        status='completed'
    ).count()

    total_count = pending_count + completed_count

    context = {
        'tickets': tickets,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'total_count': total_count,
        'search_query': search_query,  # New combined search field
        'phone_search': phone_search,  # Keep for backward compatibility
        'status_filter': status_filter,
        'sort_order': sort_order,
        'status_choices': CustomerTicket.STATUS_CHOICES,
        'sort_choices': [
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First'),
            ('status', 'By Status'),
            ('amount', 'By Amount'),
        ],
        'store': request.user.store,
    }

    return render(request, 'store/ticket_management.html', context)


@login_required
def process_ticket(request, ticket_id):
    """
    Process a ticket by loading its data into the cart and redirecting to initiate-order
    """
    if request.user.role != 'cashier':
        messages.error(request, 'Unauthorized access.')
        return redirect('ticket_management')

    if not request.user.store:
        messages.error(request, 'You are not assigned to any store.')
        return redirect('ticket_management')

    try:
        from webfront.models import CustomerTicket

        # Get the ticket by ID
        ticket = CustomerTicket.objects.get(
            id=ticket_id,
            store=request.user.store
        )

        # Check if ticket can be processed
        if ticket.status in ['completed', 'cancelled']:
            messages.warning(request, f'Ticket #{ticket.ticket_number} cannot be processed as it is already {ticket.status}.')
            return redirect('ticket_management')

        # Clear existing cart
        request.session['cart'] = {
            'items': [],
            'total': 0,
            'created_at': timezone.now().isoformat(),
            'cashier_id': request.user.id,
            'store_id': request.user.store.id
        }

        # Load ticket items into cart
        cart_items = []
        cart_total = 0

        for ticket_item in ticket.items.all():
            # Get current stock for this product
            try:
                stock = Stock.objects.get(
                    product=ticket_item.product,
                    store=request.user.store
                )

                # Check if we have enough stock
                if stock.quantity >= ticket_item.quantity:
                    cart_item = {
                        'product_id': ticket_item.product.id,
                        'product_name': ticket_item.product.name,
                        'quantity': ticket_item.quantity,
                        'price': float(ticket_item.unit_price),  # JavaScript expects 'price' not 'unit_price'
                        'subtotal': float(ticket_item.total_price),  # JavaScript expects 'subtotal' not 'total_price'
                        'added_at': timezone.now().isoformat()
                    }
                    cart_items.append(cart_item)
                    cart_total += float(ticket_item.total_price)
                else:
                    messages.warning(request, f'Insufficient stock for {ticket_item.product.name}. Available: {stock.quantity}, Required: {ticket_item.quantity}')
            except Stock.DoesNotExist:
                messages.warning(request, f'Product {ticket_item.product.name} is not available in this store.')

        # Update cart in session
        request.session['cart']['items'] = cart_items
        request.session['cart']['total'] = cart_total
        request.session.modified = True

        # Store ticket information for order completion
        request.session['ticket_info'] = {
            'from_ticket': True,
            'ticket_id': ticket.id,
            'ticket_number': ticket.ticket_number,
            'customer_name': ticket.customer_name,
            'customer_phone': ticket.customer_phone
        }
        request.session.modified = True

        # Debug: Print cart contents
        print(f"DEBUG: Cart loaded with {len(cart_items)} items, total: {cart_total}")
        for item in cart_items:
            print(f"DEBUG: Item - {item['product_name']}: {item['quantity']}x @ {item['price']} = {item['subtotal']}")

        messages.success(request, f'Ticket #{ticket.ticket_number} loaded into cart. {len(cart_items)} items added.')
        return redirect('initiate_order')

    except CustomerTicket.DoesNotExist:
        messages.error(request, f'Ticket not found.')
        return redirect('ticket_management')
    except Exception as e:
        messages.error(request, f'Error processing ticket: {str(e)}')
        return redirect('ticket_management')


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

        # Convert to int to ensure proper comparison
        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid product ID'}, status=400)

        cart = request.session.get('cart', {'items': [], 'total': 0})

        # Debug logging
        print(f"DEBUG: Removing product_id {product_id} from cart")
        print(f"DEBUG: Cart before removal: {cart}")

        # Count items before removal
        items_before = len(cart['items'])

        # Remove item with proper type comparison
        cart['items'] = [item for item in cart['items'] if int(item['product_id']) != product_id]

        # Count items after removal
        items_after = len(cart['items'])

        print(f"DEBUG: Items before: {items_before}, Items after: {items_after}")

        # Recalculate total
        cart['total'] = sum(item['subtotal'] for item in cart['items'])

        request.session['cart'] = cart
        request.session.modified = True

        print(f"DEBUG: Cart after removal: {cart}")

        return JsonResponse({
            'success': True,
            'cart': cart,
            'message': f'Item removed from cart (removed {items_before - items_after} items)'
        })

    except Exception as e:
        print(f"DEBUG: Error in remove_from_cart: {str(e)}")
        import traceback
        traceback.print_exc()
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
        discount_percent = 0  # No discount allowed
        is_taxable = True  # Always apply tax (15%)
        customer_name = data.get('customer_name', 'Walk-in Customer')
        customer_phone = data.get('customer_phone', '')

        cart = request.session.get('cart')
        print(f"DEBUG - Cart data from session: {cart}")  # Debug log
        print(f"DEBUG - Session keys: {list(request.session.keys())}")  # Debug log

        if not cart:
            print("DEBUG - No cart found in session")
            return JsonResponse({'error': 'Cart not found in session'}, status=400)

        if not cart.get('items'):
            print("DEBUG - Cart has no items")
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        print(f"DEBUG - Cart has {len(cart['items'])} items")

        # Validate cart items structure
        for i, item in enumerate(cart['items']):
            print(f"DEBUG - Item {i}: {item}")  # Debug log
            if not all(key in item for key in ['product_id', 'quantity']):
                return JsonResponse({'error': f'Invalid cart item structure at index {i}'}, status=400)

        with transaction.atomic():
            # Calculate totals - convert all to Decimal for consistency
            try:
                # Handle different cart item structures (subtotal vs total_price)
                cart_subtotal = 0
                for item in cart['items']:
                    # Try different field combinations
                    if 'subtotal' in item:
                        item_total = float(item['subtotal'])
                    elif 'total_price' in item:
                        item_total = float(item['total_price'])
                    else:
                        # Calculate from price and quantity
                        price = float(item.get('price', 0) or item.get('unit_price', 0))
                        quantity = int(item.get('quantity', 0))
                        item_total = price * quantity

                    cart_subtotal += item_total
                    print(f"DEBUG - Item total: {item_total}, Running subtotal: {cart_subtotal}")  # Debug log

                subtotal = Decimal(str(cart_subtotal))
                discount_amount = subtotal * (Decimal(str(discount_percent)) / Decimal('100'))
                taxable_amount = subtotal - discount_amount
                tax_amount = taxable_amount * Decimal('0.15') if is_taxable else Decimal('0')
                total_amount = taxable_amount + tax_amount

                print(f"DEBUG - Final calculations: subtotal={subtotal}, total={total_amount}")  # Debug log
            except (ValueError, TypeError, KeyError) as calc_error:
                print(f"DEBUG - Calculation error details: {calc_error}")  # Debug log
                print(f"DEBUG - Cart items causing error: {cart['items']}")  # Debug log
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
            for i, item in enumerate(cart['items']):
                try:
                    print(f"DEBUG - Processing item {i}: {item}")  # Debug log

                    # Validate required fields
                    product_id = item.get('product_id')
                    quantity = int(item.get('quantity', 0))

                    if not product_id or quantity <= 0:
                        raise ValueError(f"Invalid product_id or quantity for item {i}")

                    # Get stock and update quantity
                    stock = Stock.objects.select_for_update().get(
                        product_id=product_id,
                        store=request.user.store
                    )

                    if stock.quantity < quantity:
                        product_name = item.get('product_name', stock.product.name)
                        raise ValueError(f"Insufficient stock for {product_name}. Available: {stock.quantity}, Requested: {quantity}")

                    stock.quantity -= quantity
                    stock.save()

                    # Handle different price field names
                    item_price = float(item.get('price', 0) or item.get('unit_price', 0))
                    if item_price <= 0:
                        # Fallback to product price if not in cart
                        item_price = float(stock.product.price)

                    item_subtotal = item.get('subtotal') or item.get('total_price') or (item_price * quantity)

                    # Create transaction order
                    order = TransactionOrder.objects.create(
                        receipt=receipt,
                        transaction=transaction_obj,
                        product_id=product_id,
                        quantity=quantity,
                        price_at_time_of_sale=Decimal(str(item_price))
                    )

                    order_items.append({
                        'product_name': item.get('product_name', stock.product.name),
                        'quantity': quantity,
                        'price': item_price,
                        'subtotal': float(item_subtotal)
                    })

                    print(f"DEBUG - Successfully processed item {i}")  # Debug log

                except Exception as item_error:
                    print(f"DEBUG - Error processing item {i}: {item_error}")  # Debug log
                    print(f"DEBUG - Item data: {item}")  # Debug log
                    raise ValueError(f"Error processing item {i}: {str(item_error)}")

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

            # Prepare receipt data for frontend
            receipt_data = {
                'id': receipt.id,
                'receipt_number': f"R{receipt.id:06d}",
                'created_at': receipt.timestamp.isoformat(),
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'cashier_name': request.user.get_full_name() or request.user.username,
                'store_name': request.user.store.name,
                'total_amount': float(total_amount),
                'subtotal': float(subtotal),
                'discount_amount': float(discount_amount),
                'discount_percent': discount_percent,
                'tax_amount': float(tax_amount),
                'payment_type': payment_type,
                'items': []
            }

            # Add items to receipt data
            for item in order_items:
                receipt_data['items'].append({
                    'product_name': item['product_name'],
                    'quantity': item['quantity'],
                    'unit_price': float(item['price']),
                    'total_price': float(item['subtotal'])
                })

            return JsonResponse({
                'success': True,
                'transaction_id': transaction_obj.id,
                'receipt_id': receipt.id,
                'total_amount': float(total_amount),
                'receipt': receipt_data,
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
        print(f"Order completion validation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        print(f"Order completion error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Order completion failed: {str(e)}'}, status=500)


def generate_simple_html_receipt(receipt, transaction_obj, order_items, user, receipt_id):
    """
    Generate a simple HTML receipt for download when PDF generation fails
    """
    from django.template.loader import render_to_string

    context = {
        'receipt': receipt,
        'transaction': transaction_obj,
        'order_items': order_items,
        'subtotal': receipt.subtotal,
        'store': transaction_obj.store,
        'cashier': user,
        'timestamp': transaction_obj.timestamp,
        'customer_name': receipt.customer_name,
        'customer_phone': receipt.customer_phone,
        'discount_amount': receipt.discount_amount,
        'discount_percent': receipt.discount_percent,
        'tax_amount': receipt.tax_amount,
        'payment_method': transaction_obj.payment_type,
    }

    # Generate clean HTML receipt
    receipt_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Receipt #{receipt.id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .store-name {{ font-size: 18px; font-weight: bold; }}
            .receipt-info {{ margin: 20px 0; }}
            .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            .items-table th, .items-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .items-table th {{ background-color: #f2f2f2; }}
            .totals {{ margin-top: 20px; text-align: right; }}
            .total-line {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="store-name">EZM Trade & Investment</div>
            <div>Receipt #{receipt.id}</div>
        </div>

        <div class="receipt-info">
            <p><strong>Transaction ID:</strong> {transaction_obj.id}</p>
            <p><strong>Date:</strong> {transaction_obj.timestamp.strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>Salesperson:</strong> {user.get_full_name() or user.username}</p>
            <p><strong>Customer:</strong> {receipt.customer_name or 'Walk-in Customer'}</p>
            <p><strong>Phone:</strong> {receipt.customer_phone or 'N/A'}</p>
            <p><strong>Payment Method:</strong> {transaction_obj.get_payment_type_display()}</p>
        </div>

        <table class="items-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Qty</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
    """

    for item in order_items:
        line_total = item.quantity * item.price_at_time_of_sale
        receipt_html += f"""
                <tr>
                    <td>{item.product.name}</td>
                    <td>{item.quantity}</td>
                    <td>ETB {item.price_at_time_of_sale:.2f}</td>
                    <td>ETB {line_total:.2f}</td>
                </tr>
        """

    receipt_html += f"""
            </tbody>
        </table>

        <div class="totals">
            <p>Subtotal: ETB {receipt.subtotal:.2f}</p>
            <p>Tax (15%): ETB {receipt.tax_amount:.2f}</p>
            <p>Discount: ETB {receipt.discount_amount:.2f}</p>
            <p class="total-line">Total: ETB {receipt.total_amount:.2f}</p>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <p>Thank you for your business!</p>
        </div>
    </body>
    </html>
    """

    response = HttpResponse(receipt_html, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="receipt_{receipt_id}.html"'
    return response


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

        # Calculate tax (15% of total) - convert to Decimal for proper calculation
        from decimal import Decimal
        tax_rate = Decimal('0.15')
        tax_divisor = Decimal('1.15')
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

        # Generate PDF using ReportLab for reliable PDF generation
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas
            from io import BytesIO

            # Create PDF buffer with receipt-like dimensions
            buffer = BytesIO()

            # Create canvas for custom receipt layout
            c = canvas.Canvas(buffer, pagesize=(4*inch, 11*inch))  # Receipt paper size
            width, height = 4*inch, 11*inch

            # Set font
            c.setFont("Courier", 10)  # Monospace font for receipt look

            y_position = height - 0.5*inch

            # Store header (centered)
            store_name = "EZM TRADE & INVESTMENT"
            c.setFont("Courier-Bold", 12)
            text_width = c.stringWidth(store_name, "Courier-Bold", 12)
            c.drawString((width - text_width) / 2, y_position, store_name)
            y_position -= 20

            # Store address (centered)
            c.setFont("Courier", 9)
            address = "Piassa, Addis Ababa"
            text_width = c.stringWidth(address, "Courier", 9)
            c.drawString((width - text_width) / 2, y_position, address)
            y_position -= 15

            phone = f"Phone: {transaction_obj.store.phone_number or 'N/A'}"
            text_width = c.stringWidth(phone, "Courier", 9)
            c.drawString((width - text_width) / 2, y_position, phone)
            y_position -= 25

            # Separator line
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 20

            # Receipt details
            c.setFont("Courier", 9)
            receipt_details = [
                f"Receipt #: {receipt.id}",
                f"Trans ID: {transaction_obj.id}",
                f"Date: {transaction_obj.timestamp.strftime('%m/%d/%Y %I:%M %p')}",
                f"Salesperson: {request.user.get_full_name() or request.user.username}",
                f"Customer: {receipt.customer_name or 'Walk-in Customer'}",
                f"Payment: {transaction_obj.get_payment_type_display()}"
            ]

            for detail in receipt_details:
                c.drawString(0.2*inch, y_position, detail)
                y_position -= 12

            y_position -= 10

            # Items separator
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 15

            # Items header
            c.setFont("Courier-Bold", 9)
            c.drawString(0.2*inch, y_position, "ITEM")
            c.drawString(2.2*inch, y_position, "QTY")
            c.drawString(2.8*inch, y_position, "PRICE")
            c.drawString(3.4*inch, y_position, "TOTAL")
            y_position -= 12

            # Items separator
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 15

            # Items
            c.setFont("Courier", 8)
            for item in order_items:
                line_total = item.quantity * item.price_at_time_of_sale

                # Item name (truncate if too long)
                item_name = item.product.name[:20] if len(item.product.name) > 20 else item.product.name
                c.drawString(0.2*inch, y_position, item_name)

                # Quantity (right aligned)
                qty_str = str(item.quantity)
                qty_width = c.stringWidth(qty_str, "Courier", 8)
                c.drawString(2.5*inch - qty_width, y_position, qty_str)

                # Unit price (right aligned)
                price_str = f"{item.price_at_time_of_sale:.2f}"
                price_width = c.stringWidth(price_str, "Courier", 8)
                c.drawString(3.2*inch - price_width, y_position, price_str)

                # Line total (right aligned)
                total_str = f"{line_total:.2f}"
                total_width = c.stringWidth(total_str, "Courier", 8)
                c.drawString(3.8*inch - total_width, y_position, total_str)

                y_position -= 12

            y_position -= 10

            # Totals separator
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 15

            # Totals
            c.setFont("Courier", 9)
            totals = [
                ("Subtotal", receipt.subtotal),
                ("Tax (15%)", receipt.tax_amount),
                ("Discount", receipt.discount_amount),
            ]

            for label, amount in totals:
                # Create dot leaders
                dots_needed = 25 - len(label) - len(f"{amount:.2f}")
                dots = "." * max(0, dots_needed)
                line = f"{label}{dots}ETB {amount:.2f}"
                c.drawString(0.2*inch, y_position, line)
                y_position -= 12

            # Total line (bold)
            c.setFont("Courier-Bold", 10)
            total_dots = 22 - len(f"{receipt.total_amount:.2f}")
            total_dots_str = "." * max(0, total_dots)
            total_line = f"TOTAL{total_dots_str}ETB {receipt.total_amount:.2f}"
            c.drawString(0.2*inch, y_position, total_line)
            y_position -= 25

            # Final separator
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 20

            # Thank you message (centered)
            c.setFont("Courier", 9)
            thank_you = "THANK YOU FOR YOUR BUSINESS!"
            text_width = c.stringWidth(thank_you, "Courier", 9)
            c.drawString((width - text_width) / 2, y_position, thank_you)
            y_position -= 15

            visit_again = "Please visit us again!"
            text_width = c.stringWidth(visit_again, "Courier", 9)
            c.drawString((width - text_width) / 2, y_position, visit_again)

            # Save the PDF
            c.save()

            # Return PDF response
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{receipt_id}.pdf"'
            return response

        except ImportError as e:
            print(f"ReportLab not available: {str(e)}")
            # Fallback: Generate simple HTML receipt for download
            return generate_simple_html_receipt(receipt, transaction_obj, order_items, request.user, receipt_id)

        except Exception as pdf_error:
            print(f"PDF Generation Error: {str(pdf_error)}")
            import traceback
            traceback.print_exc()
            # Fallback: Generate simple HTML receipt for download
            return generate_simple_html_receipt(receipt, transaction_obj, order_items, request.user, receipt_id)

    except Exception as e:
        print(f"Receipt Generation Error: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()  # Print full traceback
        messages.error(request, f"Error generating receipt: {str(e)}")
        return redirect('initiate_order')


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
            return redirect('initiate_order')

        # Get order items
        order_items = TransactionOrder.objects.filter(
            transaction=transaction_obj
        ).select_related('receipt', 'product')

        # Add subtotal to each item for template
        for item in order_items:
            item.subtotal = item.quantity * item.price_at_time_of_sale

        # Debug: Print data to console
        print(f"DEBUG - Receipt ID: {receipt.id}")
        print(f"DEBUG - Customer: {receipt.customer_name}")
        print(f"DEBUG - Order items count: {order_items.count()}")
        for item in order_items:
            print(f"DEBUG - Item: {item.product.name if item.product else 'No Product'}, Qty: {item.quantity}, Price: {item.price_at_time_of_sale}")

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
        return redirect('initiate_order')


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

            # Update transfer request (approve but don't transfer stock yet)
            transfer_request.status = 'approved'
            transfer_request.approved_quantity = approved_quantity
            transfer_request.reviewed_by = request.user
            transfer_request.reviewed_date = timezone.now()
            transfer_request.review_notes = review_notes
            transfer_request.save()

            # Note: Stock transfer will happen when the receiving store marks it as completed
            # This ensures the receiving store actually receives the items before stock is updated

            success_msg = f"Transfer request #{transfer_request.request_number} approved for {approved_quantity} units. Stock will be transferred when {transfer_request.to_store.name} confirms receipt."

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
                received_quantity = int(data.get('received_quantity', transfer_request.approved_quantity))
            else:
                completion_notes = request.POST.get('completion_notes', '').strip()
                received_quantity = int(request.POST.get('received_quantity', transfer_request.approved_quantity))

            # Validate received quantity
            if received_quantity <= 0:
                error_msg = "Received quantity must be greater than 0."
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('store_manager_transfer_requests')

            if received_quantity > transfer_request.approved_quantity:
                error_msg = f"Received quantity ({received_quantity}) cannot exceed approved quantity ({transfer_request.approved_quantity})."
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('store_manager_transfer_requests')

            # Now perform the actual stock transfer
            from Inventory.models import Stock
            from django.utils import timezone

            # Get source stock (from the sending store)
            try:
                source_stock = Stock.objects.get(
                    store=transfer_request.from_store,
                    product=transfer_request.product
                )
            except Stock.DoesNotExist:
                error_msg = f"Source stock not found for {transfer_request.product.name} in {transfer_request.from_store.name}."
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('store_manager_transfer_requests')

            # Check if source store still has enough stock
            if source_stock.quantity < received_quantity:
                error_msg = f"Insufficient stock in {transfer_request.from_store.name}. Available: {source_stock.quantity}, Required: {received_quantity}."
                if request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('store_manager_transfer_requests')

            # Perform stock transfer
            # Reduce stock from source store
            source_stock.quantity -= received_quantity
            source_stock.last_updated = timezone.now()
            source_stock.save()

            # Add stock to destination store (this store)
            dest_stock, created = Stock.objects.get_or_create(
                store=store,
                product=transfer_request.product,
                defaults={
                    'quantity': 0,
                    'low_stock_threshold': 10,
                    'selling_price': source_stock.selling_price,
                    'last_updated': timezone.now()
                }
            )
            dest_stock.quantity += received_quantity
            dest_stock.last_updated = timezone.now()
            dest_stock.save()

            # Update request status to completed
            transfer_request.status = 'completed'
            transfer_request.actual_quantity_transferred = received_quantity
            transfer_request.received_date = timezone.now()
            transfer_request.review_notes = completion_notes or f"Transfer completed by {request.user.get_full_name() or request.user.username}. Received {received_quantity} units."
            transfer_request.save()

            # Success response
            success_msg = f"Transfer request {transfer_request.request_number} completed successfully. {received_quantity} units added to your store inventory."

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

        # Generate PDF using ReportLab for reliable PDF generation
        pdf = None

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas
            from io import BytesIO

            # Create PDF buffer with receipt-like dimensions
            buffer = BytesIO()

            # Create canvas for custom receipt layout
            c = canvas.Canvas(buffer, pagesize=(4*inch, 11*inch))  # Receipt paper size
            width, height = 4*inch, 11*inch

            # Set font
            c.setFont("Courier", 10)  # Monospace font for receipt look

            y_position = height - 0.5*inch

            # Store header (centered)
            store_name = "EZM TRADE & INVESTMENT"
            c.setFont("Courier-Bold", 12)
            text_width = c.stringWidth(store_name, "Courier-Bold", 12)
            c.drawString((width - text_width) / 2, y_position, store_name)
            y_position -= 20

            # Store address (centered)
            c.setFont("Courier", 9)
            address = "Piassa, Addis Ababa"
            text_width = c.stringWidth(address, "Courier", 9)
            c.drawString((width - text_width) / 2, y_position, address)
            y_position -= 15

            phone = f"Phone: {transaction_obj.store.phone_number or 'N/A'}"
            text_width = c.stringWidth(phone, "Courier", 9)
            c.drawString((width - text_width) / 2, y_position, phone)
            y_position -= 25

            # Separator line
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 20

            # Receipt details
            c.setFont("Courier", 9)
            receipt_details = [
                f"Receipt #: {receipt.id}",
                f"Trans ID: {transaction_obj.id}",
                f"Date: {transaction_obj.timestamp.strftime('%m/%d/%Y %I:%M %p')}",
                f"Salesperson: {request.user.get_full_name() or request.user.username}",
                f"Customer: {receipt.customer_name or 'Walk-in Customer'}",
                f"Payment: {transaction_obj.get_payment_type_display()}"
            ]

            for detail in receipt_details:
                c.drawString(0.2*inch, y_position, detail)
                y_position -= 12

            y_position -= 10

            # Items separator
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 15

            # Items header
            c.setFont("Courier-Bold", 9)
            c.drawString(0.2*inch, y_position, "ITEM")
            c.drawString(2.2*inch, y_position, "QTY")
            c.drawString(2.8*inch, y_position, "PRICE")
            c.drawString(3.4*inch, y_position, "TOTAL")
            y_position -= 12

            # Items separator
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 15

            # Items
            c.setFont("Courier", 8)
            for item in order_items:
                line_total = item.quantity * item.price_at_time_of_sale

                # Item name (truncate if too long)
                item_name = item.product.name[:20] if len(item.product.name) > 20 else item.product.name
                c.drawString(0.2*inch, y_position, item_name)

                # Quantity (right aligned)
                qty_str = str(item.quantity)
                qty_width = c.stringWidth(qty_str, "Courier", 8)
                c.drawString(2.5*inch - qty_width, y_position, qty_str)

                # Unit price (right aligned)
                price_str = f"{item.price_at_time_of_sale:.2f}"
                price_width = c.stringWidth(price_str, "Courier", 8)
                c.drawString(3.2*inch - price_width, y_position, price_str)

                # Line total (right aligned)
                total_str = f"{line_total:.2f}"
                total_width = c.stringWidth(total_str, "Courier", 8)
                c.drawString(3.8*inch - total_width, y_position, total_str)

                y_position -= 12

            y_position -= 10

            # Totals separator
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 15

            # Totals
            c.setFont("Courier", 9)
            totals = [
                ("Subtotal", receipt.subtotal),
                ("Tax (15%)", receipt.tax_amount),
                ("Discount", receipt.discount_amount),
            ]

            for label, amount in totals:
                # Create dot leaders
                dots_needed = 25 - len(label) - len(f"{amount:.2f}")
                dots = "." * max(0, dots_needed)
                line = f"{label}{dots}ETB {amount:.2f}"
                c.drawString(0.2*inch, y_position, line)
                y_position -= 12

            # Total line (bold)
            c.setFont("Courier-Bold", 10)
            total_dots = 22 - len(f"{receipt.total_amount:.2f}")
            total_dots_str = "." * max(0, total_dots)
            total_line = f"TOTAL{total_dots_str}ETB {receipt.total_amount:.2f}"
            c.drawString(0.2*inch, y_position, total_line)
            y_position -= 25

            # Final separator
            c.line(0.2*inch, y_position, width - 0.2*inch, y_position)
            y_position -= 20

            # Thank you message (centered)
            c.setFont("Courier", 9)
            thank_you = "THANK YOU FOR YOUR BUSINESS!"
            text_width = c.stringWidth(thank_you, "Courier", 9)
            c.drawString((width - text_width) / 2, y_position, thank_you)
            y_position -= 15

            visit_again = "Please visit us again!"
            text_width = c.stringWidth(visit_again, "Courier", 9)
            c.drawString((width - text_width) / 2, y_position, visit_again)

            # Save the PDF
            c.save()

            # Get PDF bytes
            buffer.seek(0)
            pdf = buffer.getvalue()

        except ImportError as e:
            print(f"ReportLab not available for PDF generation: {str(e)}")
            pdf = None
        except Exception as pdf_error:
            print(f"PDF generation failed: {pdf_error}")
            import traceback
            traceback.print_exc()
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
            # Generate HTML receipt for email attachment
            html_receipt = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Receipt #{receipt.id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .store-name {{ font-size: 18px; font-weight: bold; }}
        .receipt-info {{ margin: 20px 0; }}
        .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .items-table th, .items-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .items-table th {{ background-color: #f2f2f2; }}
        .totals {{ margin-top: 20px; text-align: right; }}
        .total-line {{ font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="store-name">EZM Trade & Investment</div>
        <div>Receipt #{receipt.id}</div>
    </div>

    <div class="receipt-info">
        <p><strong>Transaction ID:</strong> {transaction_obj.id}</p>
        <p><strong>Date:</strong> {transaction_obj.timestamp.strftime('%B %d, %Y at %I:%M %p')}</p>
        <p><strong>Salesperson:</strong> {request.user.get_full_name() or request.user.username}</p>
        <p><strong>Customer:</strong> {receipt.customer_name or 'Walk-in Customer'}</p>
        <p><strong>Phone:</strong> {receipt.customer_phone or 'N/A'}</p>
        <p><strong>Payment Method:</strong> {transaction_obj.get_payment_type_display()}</p>
    </div>

    <table class="items-table">
        <thead>
            <tr>
                <th>Item</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>"""

            for item in order_items:
                line_total = item.quantity * item.price_at_time_of_sale
                html_receipt += f"""
            <tr>
                <td>{item.product.name}</td>
                <td>{item.quantity}</td>
                <td>ETB {item.price_at_time_of_sale:.2f}</td>
                <td>ETB {line_total:.2f}</td>
            </tr>"""

            html_receipt += f"""
        </tbody>
    </table>

    <div class="totals">
        <p>Subtotal: ETB {receipt.subtotal:.2f}</p>
        <p>Tax (15%): ETB {receipt.tax_amount:.2f}</p>
        <p>Discount: ETB {receipt.discount_amount:.2f}</p>
        <p class="total-line">Total: ETB {receipt.total_amount:.2f}</p>
    </div>

    <div style="text-align: center; margin-top: 30px;">
        <p>Thank you for your business!</p>
    </div>
</body>
</html>"""

            # Attach HTML receipt
            email.attach(
                f'receipt_{receipt.id}.html',
                html_receipt.encode('utf-8'),
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
            import traceback
            traceback.print_exc()  # Print full traceback for debugging

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
        return JsonResponse({
            'success': False,
            'error': f'Failed to send email: {str(e)}',
            'message': f'Failed to send email: {str(e)}'
        }, status=500)


@login_required
def cashier_transactions(request):
    """
    Display transaction history for the current cashier with search and filter functionality
    """
    if request.user.role != 'cashier':
        messages.error(request, "Access denied")
        return redirect('login')

    try:
        from django.db.models import Sum, Q
        from django.core.paginator import Paginator
        from django.http import HttpResponse
        import csv
        from datetime import datetime

        # Base queryset for receipts at this cashier's store
        receipts_queryset = Receipt.objects.filter(
            transaction__store=request.user.store,
            transaction__transaction_type='sale'
        ).select_related('transaction').prefetch_related('orders')

        # Apply search and filter parameters
        receipt_id = request.GET.get('receipt_id', '').strip()
        customer_name = request.GET.get('customer_name', '').strip()
        customer_phone = request.GET.get('customer_phone', '').strip()
        payment_type = request.GET.get('payment_type', '').strip()
        date_from = request.GET.get('date_from', '').strip()
        date_to = request.GET.get('date_to', '').strip()
        amount_min = request.GET.get('amount_min', '').strip()
        amount_max = request.GET.get('amount_max', '').strip()

        # Apply filters
        if receipt_id:
            try:
                receipts_queryset = receipts_queryset.filter(id=int(receipt_id))
            except ValueError:
                messages.warning(request, "Invalid receipt ID format")

        if customer_name:
            receipts_queryset = receipts_queryset.filter(
                customer_name__icontains=customer_name
            )

        if customer_phone:
            receipts_queryset = receipts_queryset.filter(
                customer_phone__icontains=customer_phone
            )

        if payment_type:
            receipts_queryset = receipts_queryset.filter(
                transaction__payment_type=payment_type
            )

        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                receipts_queryset = receipts_queryset.filter(
                    timestamp__date__gte=from_date
                )
            except ValueError:
                messages.warning(request, "Invalid 'from' date format")

        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                receipts_queryset = receipts_queryset.filter(
                    timestamp__date__lte=to_date
                )
            except ValueError:
                messages.warning(request, "Invalid 'to' date format")

        if amount_min:
            try:
                min_amount = float(amount_min)
                receipts_queryset = receipts_queryset.filter(
                    total_amount__gte=min_amount
                )
            except ValueError:
                messages.warning(request, "Invalid minimum amount format")

        if amount_max:
            try:
                max_amount = float(amount_max)
                receipts_queryset = receipts_queryset.filter(
                    total_amount__lte=max_amount
                )
            except ValueError:
                messages.warning(request, "Invalid maximum amount format")

        # Order by timestamp (newest first)
        receipts_queryset = receipts_queryset.order_by('-timestamp')

        # Handle CSV export
        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

            writer = csv.writer(response)
            writer.writerow([
                'Receipt ID', 'Date', 'Time', 'Customer Name', 'Customer Phone',
                'Payment Type', 'Subtotal', 'Discount', 'Tax', 'Total Amount', 'Items Count'
            ])

            for receipt in receipts_queryset:
                writer.writerow([
                    receipt.id,
                    receipt.timestamp.strftime('%Y-%m-%d'),
                    receipt.timestamp.strftime('%H:%M:%S'),
                    receipt.customer_name or 'Walk-in Customer',
                    receipt.customer_phone or '',
                    receipt.transaction.get_payment_type_display(),
                    f"{receipt.subtotal:.2f}",
                    f"{receipt.discount_amount:.2f}",
                    f"{receipt.tax_amount:.2f}",
                    f"{receipt.total_amount:.2f}",
                    receipt.orders.count()
                ])

            return response

        # Pagination
        paginator = Paginator(receipts_queryset, 20)  # 20 transactions per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Calculate filtered revenue
        filtered_revenue = receipts_queryset.aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        # Calculate total revenue from all receipts at this store (for stats)
        total_revenue = Receipt.objects.filter(
            transaction__store=request.user.store,
            transaction__transaction_type='sale'
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0

        context = {
            'receipts': page_obj,
            'cashier': request.user,
            'total_revenue': total_revenue,
            'filtered_revenue': filtered_revenue,
            'is_paginated': page_obj.has_other_pages(),
            'page_obj': page_obj,
        }

        return render(request, 'store/cashier_transactions.html', context)

    except Exception as e:
        messages.error(request, f"Error loading transactions: {str(e)}")
        return redirect('initiate_order')


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
def create_cashier(request):
    """
    Store manager creates a new cashier account
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        # Validation
        errors = []
        if not username:
            errors.append("Username is required.")
        elif CustomUser.objects.filter(username=username).exists():
            errors.append("Username already exists.")

        if not email:
            errors.append("Email is required.")
        elif CustomUser.objects.filter(email=email).exists():
            errors.append("Email already exists.")

        if not password:
            errors.append("Password is required.")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'store/create_cashier.html', {'store': store})

        # Create cashier
        try:
            cashier = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                role='cashier',
                store=store,
                is_first_login=True
            )

            # Create StoreCashier record
            StoreCashier.objects.create(
                store=store,
                cashier=cashier,
                is_active=True
            )

            messages.success(request, f"Successfully created cashier account for {cashier.get_full_name() or cashier.username}")
            return redirect('manage_cashiers')

        except Exception as e:
            messages.error(request, f"Error creating cashier: {str(e)}")

    context = {
        'store': store,
    }
    return render(request, 'store/create_cashier.html', context)


@login_required
def edit_cashier(request, cashier_id):
    """
    Store manager edits a cashier's information
    """
    if request.user.role != 'store_manager':
        messages.error(request, "Access denied. Store manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
        cashier = get_object_or_404(CustomUser, id=cashier_id, store=store, role='cashier')
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    if request.method == 'POST':
        # Update cashier information
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        # Validate email uniqueness
        if email and CustomUser.objects.filter(email=email).exclude(id=cashier.id).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, 'store/edit_cashier.html', {'cashier': cashier, 'store': store})

        # Update cashier
        cashier.first_name = first_name
        cashier.last_name = last_name
        cashier.email = email
        cashier.phone_number = phone_number
        cashier.is_active = is_active
        cashier.save()

        messages.success(request, f"Successfully updated {cashier.get_full_name() or cashier.username}'s information.")
        return redirect('manage_cashiers')

    context = {
        'cashier': cashier,
        'store': store,
    }
    return render(request, 'store/edit_cashier.html', context)


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
    in_stock_count = 0
    low_stock_count = 0
    out_of_stock_count = 0

    for stock in stock_queryset:
        is_low_stock = stock.quantity <= stock.low_stock_threshold

        # Count statistics
        if stock.quantity == 0:
            out_of_stock_count += 1
        elif is_low_stock:
            low_stock_count += 1
        else:
            in_stock_count += 1

        product_data.append({
            'product': stock.product,
            'quantity': stock.quantity,
            'selling_price': stock.selling_price,
            'low_stock_threshold': stock.low_stock_threshold,
            'is_low_stock': is_low_stock,
            'stock_id': stock.id
        })

    context = {
        'product_data': product_data,
        'search_term': search_term,
        'store': store,
        'total_products': len(product_data),
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
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
        return redirect('initiate_order')

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
            return redirect('initiate_order')

        # Get ticket
        ticket = CustomerTicket.objects.select_related('store').prefetch_related('items__product').get(
            ticket_number=ticket_number,
            store=store
        )

        # Check if ticket can be processed
        if ticket.status in ['completed', 'cancelled']:
            messages.warning(request, f'Ticket #{ticket_number} cannot be processed as it is already {ticket.status}.')
            return redirect('initiate_order')

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
        return redirect('initiate_order')
    except Exception as e:
        messages.error(request, f'Error processing ticket: {str(e)}')
        return redirect('initiate_order')


@login_required
def get_ticket_api(request, ticket_number):
    """
    API endpoint to get ticket details for AJAX requests
    """
    if request.user.role != 'cashier':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        from webfront.models import CustomerTicket

        ticket = CustomerTicket.objects.get(
            ticket_number=ticket_number,
            store=request.user.store
        )

        # Get ticket items
        items = []
        for item in ticket.items.all():
            items.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price)
            })

        ticket_data = {
            'ticket_number': ticket.ticket_number,
            'customer_name': ticket.customer_name,
            'customer_phone': ticket.customer_phone,
            'total_amount': float(ticket.total_amount),
            'status': ticket.status,
            'items': items
        }

        return JsonResponse({
            'success': True,
            'ticket': ticket_data
        })

    except CustomerTicket.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Ticket #{ticket_number} not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def save_cart_to_session(request):
    """
    Save cart data from localStorage to Django session
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    if request.user.role != 'cashier':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        cart_data = data.get('cart')

        if cart_data:
            request.session['cart'] = cart_data
            request.session.modified = True
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'No cart data provided'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def save_ticket_info_to_session(request):
    """
    Save ticket info from localStorage to Django session
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    if request.user.role != 'cashier':
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        ticket_info = data.get('ticket_info')

        if ticket_info:
            request.session['ticket_info'] = ticket_info
            request.session.modified = True
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'No ticket info provided'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def store_manager_stock_detail(request, stock_id):
    """
    Store manager specific stock detail view with restock request functionality
    """
    if request.user.role != 'store_manager':
        messages.warning(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    # Get the stock item
    stock = get_object_or_404(Stock.objects.select_related('product', 'store'), id=stock_id, store=store)

    # Get stock history for this product at this store (last 30 days)
    from datetime import timedelta
    from django.utils import timezone
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Get recent transactions for this product
    recent_transactions = TransactionOrder.objects.filter(
        product=stock.product,
        transaction__store=store,
        transaction__timestamp__gte=thirty_days_ago
    ).select_related('transaction').order_by('-transaction__timestamp')[:10]

    # Get recent restock requests for this product
    recent_restock_requests = RestockRequest.objects.filter(
        store=store,
        product=stock.product
    ).order_by('-requested_date')[:5]

    # Check if there's a pending restock request for this product
    pending_restock = RestockRequest.objects.filter(
        store=store,
        product=stock.product,
        status='pending'
    ).first()

    # Get other stores that have this product
    other_stores_stock = Stock.objects.filter(
        product=stock.product
    ).exclude(store=store).select_related('store').order_by('store__name')

    # Calculate sales velocity (units sold per day)
    total_sold = recent_transactions.aggregate(
        total=models.Sum('quantity')
    )['total'] or 0

    days_period = 30
    sales_velocity = total_sold / days_period if total_sold > 0 else 0

    # Estimate days until out of stock
    days_until_empty = stock.quantity / sales_velocity if sales_velocity > 0 else None

    context = {
        'stock': stock,
        'store': store,
        'recent_transactions': recent_transactions,
        'recent_restock_requests': recent_restock_requests,
        'pending_restock': pending_restock,
        'other_stores_stock': other_stores_stock,
        'total_sold_30_days': total_sold,
        'sales_velocity': sales_velocity,
        'days_until_empty': days_until_empty,
    }

    return render(request, 'store/store_manager_stock_detail.html', context)


@login_required
def store_transactions_list(request):
    """
    Store manager view for all store transactions with pagination and filtering
    """
    if request.user.role != 'store_manager':
        messages.warning(request, "Access denied. Store Manager role required.")
        return redirect('login')

    try:
        store = Store.objects.get(store_manager=request.user)
    except Store.DoesNotExist:
        messages.error(request, "You are not assigned to manage any store.")
        return redirect('store_manager_page')

    # Get period from request (default to 30 days)
    period = request.GET.get('period', '30')

    from datetime import timedelta
    from django.utils import timezone
    from django.core.paginator import Paginator

    # Calculate date ranges
    now = timezone.now()
    if period == '7':
        start_date = now - timedelta(days=7)
    elif period == '30':
        start_date = now - timedelta(days=30)
    elif period == '90':
        start_date = now - timedelta(days=90)
    elif period == '365':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)

    # Get all transactions for the store in the period
    transactions = Transaction.objects.filter(
        store=store,
        timestamp__gte=start_date
    ).select_related('store', 'receipt').order_by('-timestamp')

    # Pagination
    paginator = Paginator(transactions, 25)  # Show 25 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate summary
    total_revenue = transactions.aggregate(
        total=models.Sum('total_amount')
    )['total'] or 0

    total_transactions_count = transactions.count()
    avg_transaction_value = total_revenue / total_transactions_count if total_transactions_count > 0 else 0

    context = {
        'store': store,
        'page_obj': page_obj,
        'period': period,
        'start_date': start_date,
        'end_date': now,
        'total_revenue': total_revenue,
        'total_transactions': total_transactions_count,
        'avg_transaction_value': avg_transaction_value,
    }

    return render(request, 'store/store_transactions_list.html', context)
