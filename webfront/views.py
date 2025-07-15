from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F
from django.http import JsonResponse
from Inventory.models import Stock, Product
from store.models import Store
from django.contrib.auth.decorators import login_required


def get_navigation_data():
    """
    Utility function to get navigation data for webfront templates
    """
    # Get all stores
    stores = Store.objects.all().order_by('name')

    # Get all unique categories from products that have stock
    categories = Stock.objects.values_list('product__category', flat=True).distinct().order_by('product__category')
    categories = [cat for cat in categories if cat]  # Remove empty categories

    return {
        'webfront_stores': stores,
        'webfront_categories': categories,
    }


def home_page(request):
    """
    Website-style home page with overview statistics
    """
    # Get overview statistics
    total_products = Product.objects.count()
    total_stores = Store.objects.count()
    total_stock_items = Stock.objects.count()
    low_stock_items = Stock.objects.filter(quantity__lte=F('low_stock_threshold')).count()



    # Get recent stock updates
    recent_updates = Stock.objects.select_related('product', 'store').order_by('-last_updated')[:6]

    # Get stores with their stock counts
    stores_with_stock = Store.objects.annotate(
        stock_count=Count('stock_items')
    ).filter(stock_count__gt=0).order_by('-stock_count')[:4]

    # Get top categories by stock count
    top_categories = Product.objects.values('category').annotate(
        product_count=Count('id'),
        total_stock=Sum('stock_levels__quantity')
    ).filter(total_stock__gt=0).order_by('-total_stock')[:3]

    context = {
        'total_products': total_products,
        'total_stores': total_stores,
        'total_stock_items': total_stock_items,
        'low_stock_items': low_stock_items,
        'recent_updates': recent_updates,
        'stores_with_stock': stores_with_stock,
        'top_categories': top_categories,
    }

    # Add navigation data
    context.update(get_navigation_data())

    return render(request, 'webfront/home.html', context)


def stock_list(request):
    """
    Display all store stocks with filtering and pagination
    """
    # Get all stocks with related data
    stocks = Stock.objects.select_related('product', 'store').all()

    # Get filter parameters
    store_filter = request.GET.get('store')
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search')
    low_stock_only = request.GET.get('low_stock')

    # Apply filters
    if store_filter:
        stocks = stocks.filter(store_id=store_filter)

    if category_filter:
        stocks = stocks.filter(product__category=category_filter)

    if search_query:
        stocks = stocks.filter(
            Q(product__name__icontains=search_query) |
            Q(product__description__icontains=search_query) |
            Q(store__name__icontains=search_query)
        )

    if low_stock_only:
        stocks = stocks.filter(quantity__lte=F('low_stock_threshold'))

    # Order by store name and product name
    stocks = stocks.order_by('store__name', 'product__name')

    # Pagination
    paginator = Paginator(stocks, 20)  # Show 20 stocks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get data for filters
    stores = Store.objects.all().order_by('name')
    categories = Product.objects.values_list('category', flat=True).distinct().order_by('category')

    context = {
        'page_obj': page_obj,
        'stores': stores,
        'categories': categories,
        'current_store': store_filter,
        'current_category': category_filter,
        'search_query': search_query,
        'low_stock_only': low_stock_only,
    }

    # Add navigation data
    context.update(get_navigation_data())

    return render(request, 'webfront/stock_list.html', context)


def stock_detail(request, stock_id):
    """
    Display detailed information about a specific stock item
    """
    stock = get_object_or_404(Stock.objects.select_related('product', 'store'), id=stock_id)

    # Get other stores that have this product
    other_stores_stock = Stock.objects.filter(
        product=stock.product
    ).exclude(
        store=stock.store
    ).select_related('store').order_by('store__name')

    context = {
        'stock': stock,
        'other_stores_stock': other_stores_stock,
    }

    # Add navigation data
    context.update(get_navigation_data())

    return render(request, 'webfront/stock_detail.html', context)


def store_stock_view(request, store_id):
    """
    Display all stock items for a specific store
    """
    store = get_object_or_404(Store, id=store_id)

    # Get all stocks for this store
    stocks = Stock.objects.filter(store=store).select_related('product')

    # Get filter parameters
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search')
    low_stock_only = request.GET.get('low_stock')

    # Apply filters
    if category_filter:
        stocks = stocks.filter(product__category=category_filter)

    if search_query:
        stocks = stocks.filter(
            Q(product__name__icontains=search_query) |
            Q(product__description__icontains=search_query)
        )

    if low_stock_only:
        stocks = stocks.filter(quantity__lte=10)

    # Order by product name
    stocks = stocks.order_by('product__name')

    # Pagination
    paginator = Paginator(stocks, 20)  # Show 20 stocks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for this store
    categories = stocks.values_list('product__category', flat=True).distinct().order_by('product__category')

    # Calculate store statistics
    total_products = stocks.count()
    low_stock_count = stocks.filter(quantity__lte=10).count()
    categories_count = stocks.values('product__category').distinct().count()

    context = {
        'store': store,
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_filter,
        'search_query': search_query,
        'low_stock_only': low_stock_only,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'categories_count': categories_count,
    }

    # Add navigation data
    context.update(get_navigation_data())

    return render(request, 'webfront/store_stock.html', context)


def product_stores_view(request, product_id):
    """
    Display all stores that have a specific product with their stock levels
    """
    product = get_object_or_404(Product, id=product_id)

    # Get all stores that have this product
    stocks = Stock.objects.filter(product=product).select_related('store').order_by('store__name')

    # Calculate total stock across all stores
    total_stock = stocks.aggregate(total=Sum('quantity'))['total'] or 0

    context = {
        'product': product,
        'stocks': stocks,
        'total_stock': total_stock,
    }

    # Add navigation data
    context.update(get_navigation_data())

    return render(request, 'webfront/product_stores.html', context)


def api_stock_search(request):
    """
    API endpoint for AJAX stock search
    """
    query = request.GET.get('q', '')
    store_id = request.GET.get('store_id')

    if len(query) < 2:
        return JsonResponse({'results': []})

    stocks = Stock.objects.select_related('product', 'store').filter(
        Q(product__name__icontains=query) |
        Q(product__description__icontains=query)
    )

    if store_id:
        stocks = stocks.filter(store_id=store_id)

    stocks = stocks[:10]  # Limit to 10 results

    results = []
    for stock in stocks:
        results.append({
            'id': stock.id,
            'product_name': stock.product.name,
            'store_name': stock.store.name,
            'quantity': stock.quantity,
            'price': str(stock.selling_price),
            'low_stock': stock.quantity <= stock.low_stock_threshold
        })

    return JsonResponse({'results': results})
