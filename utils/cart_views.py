"""
Cart Views for Head Manager Shopping Cart Functionality
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from Inventory.models import SupplierProduct, Supplier
from utils.cart import Cart


def is_head_manager(user):
    """Check if user is a head manager"""
    return user.is_authenticated and user.role == 'head_manager'


@login_required
@user_passes_test(is_head_manager)
def cart_view(request):
    """
    Display the shopping cart contents
    """
    cart = Cart(request)
    cart_items = cart.get_cart_items()
    suppliers_cart = cart.get_cart_by_supplier()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'suppliers_cart': suppliers_cart,
        'total_price': cart.get_total_price(),
        'total_items': cart.get_total_items(),
    }
    
    return render(request, 'cart/cart_detail.html', context)


@login_required
@user_passes_test(is_head_manager)
@require_POST
def cart_add(request):
    """
    Add a product to the cart via AJAX
    """
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        product = get_object_or_404(SupplierProduct, id=product_id)
        cart = Cart(request)
        result = cart.add(product=product, quantity=quantity)

        if result['success']:
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'cart_total_items': cart.get_total_items(),
                'cart_total_price': str(cart.get_total_price()),
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result['message']
            })
        
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'success': False,
            'message': 'Invalid quantity specified'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error adding product to cart'
        })


@login_required
@user_passes_test(is_head_manager)
@require_POST
def cart_remove(request):
    """
    Remove a product from the cart via AJAX
    """
    try:
        product_id = request.POST.get('product_id')
        product = get_object_or_404(SupplierProduct, id=product_id)
        cart = Cart(request)
        cart.remove(product)
        
        return JsonResponse({
            'success': True,
            'message': f'{product.product_name} removed from cart',
            'cart_total_items': cart.get_total_items(),
            'cart_total_price': str(cart.get_total_price()),
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error removing product from cart'
        })


@login_required
@user_passes_test(is_head_manager)
@require_POST
def cart_update_quantity(request):
    """
    Update product quantity in cart via AJAX
    """
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        cart = Cart(request)
        result = cart.update_quantity(product_id, quantity)

        if result['success']:
            # Get updated cart info
            cart_items = cart.get_cart_items()
            updated_item = None
            for item in cart_items:
                if str(item['product'].id) == str(product_id):
                    updated_item = item
                    break

            response_data = {
                'success': True,
                'message': result['message'],
                'cart_total_items': cart.get_total_items(),
                'cart_total_price': str(cart.get_total_price()),
            }

            if updated_item:
                response_data['item_total_price'] = str(updated_item['total_price'])
                response_data['item_quantity'] = updated_item['quantity']

            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'success': False,
                'message': result['message']
            })
        
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'message': 'Invalid quantity specified'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error updating quantity'
        })


@login_required
@user_passes_test(is_head_manager)
def cart_clear(request):
    """
    Clear all items from the cart
    """
    cart = Cart(request)
    cart.clear()
    messages.success(request, 'Cart cleared successfully')
    return redirect('cart_view')


@login_required
@user_passes_test(is_head_manager)
@require_POST
def cart_validate(request):
    """
    Validate cart stock levels before checkout
    """
    try:
        cart = Cart(request)
        validation_result = cart.validate_stock()

        return JsonResponse(validation_result)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error validating cart'
        })


@login_required
@user_passes_test(is_head_manager)
def cart_count(request):
    """
    Get cart item count for AJAX requests
    """
    cart = Cart(request)
    return JsonResponse({
        'cart_total_items': cart.get_total_items(),
        'cart_total_price': str(cart.get_total_price()),
    })


@login_required
@user_passes_test(is_head_manager)
def order_confirmation(request):
    """
    Display order confirmation page with cart contents grouped by supplier
    """
    cart = Cart(request)
    
    if cart.get_total_items() == 0:
        messages.warning(request, 'Your cart is empty. Please add some products before proceeding.')
        return redirect('supplier_list')
    
    suppliers_cart = cart.get_cart_by_supplier()
    
    context = {
        'cart': cart,
        'suppliers_cart': suppliers_cart,
        'total_price': cart.get_total_price(),
        'total_items': cart.get_total_items(),
        'total_suppliers': len(suppliers_cart),
    }
    
    return render(request, 'cart/order_confirmation.html', context)


@login_required
@user_passes_test(is_head_manager)
@require_POST
def proceed_to_purchase_requests(request):
    """
    Process the cart and initiate Chapa payment workflow
    """
    cart = Cart(request)

    if cart.get_total_items() == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart_view')

    suppliers_cart = cart.get_cart_by_supplier()

    if not suppliers_cart:
        messages.error(request, 'No items found in cart.')
        return redirect('cart_view')

    # Redirect to payment initiation
    return redirect('initiate_payment')
