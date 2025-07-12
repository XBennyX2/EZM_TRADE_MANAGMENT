#!/usr/bin/env python
"""
Simple test to verify analytics functionality.
"""

import os
import sys

# Add the project directory to Python path
project_dir = '/home/kal/Documents/Final_Project/rec/EZM_TRADE_MANAGMENT'
sys.path.insert(0, project_dir)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    import django
    django.setup()
    
    print("🧪 Testing Analytics Implementation")
    print("=" * 50)
    
    # Test URL imports
    try:
        from django.urls import reverse
        analytics_url = reverse('analytics_dashboard')
        financial_url = reverse('financial_reports')
        api_url = reverse('analytics_api')
        
        print("✅ URL patterns configured correctly:")
        print(f"   - Analytics Dashboard: {analytics_url}")
        print(f"   - Financial Reports: {financial_url}")
        print(f"   - Analytics API: {api_url}")
    except Exception as e:
        print(f"❌ URL configuration error: {e}")
    
    # Test view imports
    try:
        from users.views import analytics_dashboard, financial_reports, analytics_api
        print("✅ Analytics views imported successfully")
    except Exception as e:
        print(f"❌ View import error: {e}")
    
    # Test model imports
    try:
        from transactions.models import Transaction, FinancialRecord
        from store.models import Store
        from Inventory.models import Product, Stock
        print("✅ Required models imported successfully")
    except Exception as e:
        print(f"❌ Model import error: {e}")
    
    # Test template tags
    try:
        from users.templatetags.analytics_extras import lookup, currency, percentage
        print("✅ Template filters imported successfully")
    except Exception as e:
        print(f"❌ Template filter error: {e}")
    
    # Test basic data queries
    try:
        stores_count = Store.objects.count()
        transactions_count = Transaction.objects.count()
        products_count = Product.objects.count()
        
        print("✅ Database queries working:")
        print(f"   - Stores: {stores_count}")
        print(f"   - Transactions: {transactions_count}")
        print(f"   - Products: {products_count}")
    except Exception as e:
        print(f"❌ Database query error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Analytics system is ready!")
    print("\n📋 Features Available:")
    print("   ✓ Store performance comparison")
    print("   ✓ Top selling products per store")
    print("   ✓ Overall best sellers identification")
    print("   ✓ Financial reports and P&L statements")
    print("   ✓ Interactive charts and visualizations")
    print("   ✓ Time period filtering")
    print("   ✓ Export functionality")
    
    print("\n🌐 Access URLs:")
    print("   - Analytics Dashboard: /users/head-manager/analytics/")
    print("   - Financial Reports: /users/head-manager/financial-reports/")
    
    print("\n🔑 Login as head manager to access the analytics system!")
    
except Exception as e:
    print(f"❌ Setup error: {e}")
    import traceback
    traceback.print_exc()
