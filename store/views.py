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
