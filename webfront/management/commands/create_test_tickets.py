from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from webfront.models import CustomerTicket, CustomerTicketItem
from store.models import Store
from Inventory.models import Product
import random

class Command(BaseCommand):
    help = 'Create test tickets for debugging'

    def handle(self, *args, **options):
        # Get first store and some products
        store = Store.objects.first()
        products = Product.objects.all()[:5]
        
        if not store:
            self.stdout.write(self.style.ERROR('No stores found. Please create a store first.'))
            return
            
        if not products:
            self.stdout.write(self.style.ERROR('No products found. Please create some products first.'))
            return

        # Create test tickets
        statuses = ['pending', 'confirmed', 'preparing', 'ready', 'completed']
        
        for i in range(10):
            # Create ticket
            ticket = CustomerTicket.objects.create(
                store=store,
                customer_phone=f"123456789{i}",
                customer_name=f"Test Customer {i+1}",
                total_amount=Decimal('0.00'),
                total_items=0,
                status=random.choice(statuses),
                notes=f"Test order #{i+1} from webfront"
            )
            
            # Add random items to ticket
            total_amount = Decimal('0.00')
            total_items = 0
            
            num_items = random.randint(1, 3)
            selected_products = random.sample(list(products), min(num_items, len(products)))
            
            for product in selected_products:
                quantity = random.randint(1, 5)
                unit_price = Decimal(str(random.uniform(10, 100)))
                total_price = unit_price * quantity
                
                CustomerTicketItem.objects.create(
                    ticket=ticket,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price
                )
                
                total_amount += total_price
                total_items += quantity
            
            # Update ticket totals
            ticket.total_amount = total_amount
            ticket.total_items = total_items
            ticket.save()
            
            self.stdout.write(f"Created ticket #{ticket.ticket_number} with {total_items} items")
        
        total_tickets = CustomerTicket.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created test tickets. Total tickets: {total_tickets}')
        )
