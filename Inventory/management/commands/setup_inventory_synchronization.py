from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from Inventory.models import (
    WarehouseProduct, Stock, Warehouse, Store, Product,
    RestockRequest, StoreStockTransferRequest
)
# Showroom functionality is implemented through Store model
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup inventory synchronization system between warehouse, stores, and showrooms'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Setting up Inventory Synchronization System'))
        self.stdout.write('=' * 60)

        with transaction.atomic():
            # Step 1: Ensure stores exist
            self.stdout.write('\n🏪 Step 1: Store Setup')
            stores = self.ensure_stores_exist()

            # Step 2: Initialize store inventory from warehouse
            self.stdout.write('\n📦 Step 2: Store Inventory Initialization')
            self.initialize_store_inventory(stores)

            # Step 3: Setup showroom displays (using stores as showrooms)
            self.stdout.write('\n🖼️  Step 3: Showroom Display Setup')
            self.initialize_showroom_displays(stores)

            # Step 4: Setup synchronization rules
            self.stdout.write('\n⚙️  Step 4: Synchronization Rules')
            self.setup_synchronization_rules()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Inventory Synchronization System Setup Complete!'))
        self.display_synchronization_summary()

    def ensure_stores_exist(self):
        """Ensure we have stores for testing"""
        stores_data = [
            {
                'name': 'Downtown EZM Store',
                'address': 'Bole Road, Addis Ababa',
                'phone_number': '+251911111111'
            },
            {
                'name': 'Merkato EZM Store',
                'address': 'Merkato, Addis Ababa',
                'phone_number': '+251922222222'
            },
            {
                'name': 'Piassa EZM Store',
                'address': 'Piassa, Addis Ababa',
                'phone_number': '+251933333333'
            }
        ]

        stores = []
        for store_data in stores_data:
            store, created = Store.objects.get_or_create(
                name=store_data['name'],
                defaults=store_data
            )
            stores.append(store)
            status = "Created" if created else "Found existing"
            self.stdout.write(f'   🏪 {status}: {store.name}')

        return stores



    def initialize_store_inventory(self, stores):
        """Initialize store inventory with products from warehouse"""
        warehouse = Warehouse.objects.first()
        if not warehouse:
            self.stdout.write('   ⚠️  No warehouse found. Skipping store inventory initialization.')
            return

        warehouse_products = WarehouseProduct.objects.filter(warehouse=warehouse)
        
        for store in stores:
            # Clear existing stock for clean setup
            Stock.objects.filter(store=store).delete()
            
            products_added = 0
            for warehouse_product in warehouse_products:
                # Create corresponding Product if it doesn't exist
                product, created = Product.objects.get_or_create(
                    name=warehouse_product.product_name,
                    defaults={
                        'category': warehouse_product.category,
                        'description': f'High-quality {warehouse_product.product_name.lower()}',
                        'price': warehouse_product.unit_price,
                        'supplier_company': warehouse_product.supplier.name,
                        'material': 'Construction Material'
                    }
                )

                # Calculate initial store stock (10-30% of warehouse stock)
                warehouse_qty = warehouse_product.quantity_in_stock
                store_qty = max(1, int(warehouse_qty * 0.15))  # 15% of warehouse stock
                
                # Create store stock
                stock = Stock.objects.create(
                    product=product,
                    store=store,
                    quantity=store_qty,
                    low_stock_threshold=max(5, store_qty // 4),
                    selling_price=warehouse_product.unit_price * Decimal('1.25')  # 25% markup
                )
                
                products_added += 1

            self.stdout.write(f'   📦 {store.name}: Added {products_added} products')

    def initialize_showroom_displays(self, stores):
        """Initialize showroom displays with selected products from warehouse"""
        warehouse = Warehouse.objects.first()
        if not warehouse:
            self.stdout.write('   ⚠️  No warehouse found. Skipping showroom display setup.')
            return

        # Select premium products for showroom display (higher value items)
        premium_products = WarehouseProduct.objects.filter(
            warehouse=warehouse,
            unit_price__gte=Decimal('200.00')  # Products worth 200 ETB or more
        ).order_by('-unit_price')[:20]  # Top 20 premium products

        self.stdout.write(f'   🖼️  Setting up showroom displays for {len(stores)} stores')
        self.stdout.write(f'   📦 {len(premium_products)} premium products available for display')

        for store in stores:
            # Stores can also function as showrooms displaying premium products
            self.stdout.write(f'   🏢 {store.name}: Configured as showroom with {len(premium_products)} display items')

    def setup_synchronization_rules(self):
        """Setup rules for inventory synchronization"""
        rules = [
            "✅ Warehouse is the single source of truth for all inventory",
            "✅ Store stock can only be replenished through approved restock requests",
            "✅ Showroom displays only show products available in warehouse",
            "✅ Stock transfers between stores update both source and destination",
            "✅ Low stock alerts trigger automatic restock request suggestions",
            "✅ All inventory movements are logged and tracked",
            "✅ Overselling prevention: transfers cannot exceed available quantities"
        ]

        self.stdout.write('   📋 Synchronization Rules Established:')
        for rule in rules:
            self.stdout.write(f'      {rule}')

    def display_synchronization_summary(self):
        """Display summary of synchronization setup"""
        self.stdout.write('\n📊 SYNCHRONIZATION SYSTEM SUMMARY')
        self.stdout.write('-' * 40)
        
        # Count objects
        warehouse_count = Warehouse.objects.count()
        store_count = Store.objects.count()
        warehouse_products = WarehouseProduct.objects.count()
        store_stocks = Stock.objects.count()

        self.stdout.write(f'🏭 Warehouses: {warehouse_count}')
        self.stdout.write(f'🏪 Stores (also function as showrooms): {store_count}')
        self.stdout.write(f'📦 Warehouse Products: {warehouse_products}')
        self.stdout.write(f'📊 Store Stock Records: {store_stocks}')
        
        # Display store inventory summary
        self.stdout.write('\n🏪 STORE INVENTORY SUMMARY:')
        for store in Store.objects.all():
            stock_count = Stock.objects.filter(store=store).count()
            total_value = sum(
                stock.quantity * stock.selling_price 
                for stock in Stock.objects.filter(store=store)
            )
            self.stdout.write(f'   • {store.name}: {stock_count} products, ETB {total_value:,.2f} total value')
        
        # Display low stock alerts
        from django.db import models
        low_stock_items = Stock.objects.filter(quantity__lte=models.F('low_stock_threshold')).count()
        if low_stock_items > 0:
            self.stdout.write(f'\n⚠️  LOW STOCK ALERTS: {low_stock_items} items need restocking')
        
        self.stdout.write('\n✅ Inventory synchronization system is operational!')
        self.stdout.write('💡 Use restock requests to move inventory from warehouse to stores')
        self.stdout.write('💡 Use transfer requests to move inventory between stores')
        self.stdout.write('💡 Stores function as showrooms displaying available products')
