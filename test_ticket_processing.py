#!/usr/bin/env python3
"""
Test script to verify ticket processing functionality
"""

import sqlite3
import json
from datetime import datetime

# Database connection
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("🎫 TICKET PROCESSING FUNCTIONALITY TEST")
print("=" * 50)

# Get ticket statistics
cursor.execute("""
    SELECT status, COUNT(*) as count
    FROM webfront_customerticket 
    GROUP BY status 
    ORDER BY count DESC
""")
status_counts = cursor.fetchall()

print("📊 Ticket Status Overview:")
for status, count in status_counts:
    print(f"   • {status.title()}: {count} tickets")

# Get sample tickets for each status
print(f"\n🔍 Sample Tickets by Status:")
for status, _ in status_counts[:3]:  # Show first 3 statuses
    cursor.execute("""
        SELECT id, ticket_number, customer_phone, total_amount, created_at
        FROM webfront_customerticket 
        WHERE status = ?
        ORDER BY created_at DESC
        LIMIT 3
    """, (status,))
    
    tickets = cursor.fetchall()
    print(f"\n   {status.title()} Tickets:")
    
    for ticket_id, ticket_number, phone, amount, created_at in tickets:
        # Get item count for this ticket
        cursor.execute("""
            SELECT COUNT(*), SUM(quantity)
            FROM webfront_customerticketitem 
            WHERE ticket_id = ?
        """, (ticket_id,))
        
        item_count, total_qty = cursor.fetchone()
        item_count = item_count or 0
        total_qty = total_qty or 0
        
        print(f"     • #{ticket_number} - {phone} - ETB {amount}")
        print(f"       Items: {item_count} products, {total_qty} total qty")
        print(f"       Created: {created_at}")

# Test processable tickets
print(f"\n⚡ Processable Tickets (pending/confirmed):")
cursor.execute("""
    SELECT id, ticket_number, customer_phone, customer_name, total_amount, status
    FROM webfront_customerticket 
    WHERE status IN ('pending', 'confirmed')
    ORDER BY created_at DESC
    LIMIT 5
""")

processable_tickets = cursor.fetchall()

if processable_tickets:
    print(f"   Found {len(processable_tickets)} processable tickets:")
    
    for ticket_id, ticket_number, phone, name, amount, status in processable_tickets:
        # Get items for this ticket
        cursor.execute("""
            SELECT cti.quantity, p.name, cti.unit_price, cti.total_price
            FROM webfront_customerticketitem cti
            JOIN Inventory_product p ON cti.product_id = p.id
            WHERE cti.ticket_id = ?
            ORDER BY p.name
        """, (ticket_id,))
        
        items = cursor.fetchall()
        
        print(f"\n     🎫 Ticket #{ticket_number} (ID: {ticket_id})")
        print(f"        Customer: {name or 'N/A'} ({phone})")
        print(f"        Status: {status.title()}")
        print(f"        Total: ETB {amount}")
        print(f"        Items ({len(items)}):")
        
        for qty, product_name, unit_price, total_price in items[:3]:  # Show first 3 items
            print(f"          - {qty}x {product_name} @ ETB {unit_price} = ETB {total_price}")
        
        if len(items) > 3:
            print(f"          ... and {len(items) - 3} more items")
        
        # Check stock availability for processing
        print(f"        Stock Check:")
        stock_issues = []
        
        for qty, product_name, unit_price, total_price in items:
            cursor.execute("""
                SELECT s.quantity, s.store_id, st.name as store_name
                FROM Inventory_stock s
                JOIN store_store st ON s.store_id = st.id
                JOIN Inventory_product p ON s.product_id = p.id
                WHERE p.name = ?
                ORDER BY s.quantity DESC
                LIMIT 1
            """, (product_name,))
            
            stock_result = cursor.fetchone()
            if stock_result:
                stock_qty, store_id, store_name = stock_result
                if stock_qty >= qty:
                    print(f"          ✅ {product_name}: {stock_qty} available (need {qty})")
                else:
                    print(f"          ❌ {product_name}: {stock_qty} available (need {qty}) - INSUFFICIENT")
                    stock_issues.append(product_name)
            else:
                print(f"          ❌ {product_name}: No stock found")
                stock_issues.append(product_name)
        
        if not stock_issues:
            print(f"        ✅ Ready to process - all items in stock")
        else:
            print(f"        ⚠️  Stock issues with: {', '.join(stock_issues)}")

else:
    print("   No processable tickets found")

# Test URLs and navigation
print(f"\n🌐 Navigation URLs:")
print(f"   • Point of Sale: http://127.0.0.1:8000/stores/cashier/initiate-order/")
print(f"   • Ticket Management: http://127.0.0.1:8000/stores/cashier/ticket-management/")

if processable_tickets:
    sample_ticket_id = processable_tickets[0][0]
    print(f"   • Process Sample Ticket: http://127.0.0.1:8000/stores/process-ticket/{sample_ticket_id}/")

# Check cashier assignment
print(f"\n👤 Cashier Assignment Check:")
cursor.execute("""
    SELECT u.username, u.first_name, u.last_name, s.name as store_name
    FROM users_customuser u
    LEFT JOIN store_store s ON u.store_id = s.id
    WHERE u.role = 'cashier'
    LIMIT 5
""")

cashiers = cursor.fetchall()
if cashiers:
    print("   Active cashiers:")
    for username, first_name, last_name, store_name in cashiers:
        full_name = f"{first_name} {last_name}".strip() or username
        store_info = store_name or "No store assigned"
        print(f"     • {full_name} ({username}) - {store_info}")
else:
    print("   No cashiers found")

# Test ticket processing workflow
print(f"\n🔄 Ticket Processing Workflow:")
print(f"   1. Cashier logs in and accesses ticket management")
print(f"   2. Searches/filters tickets by phone, status, or date")
print(f"   3. Clicks 'Process Order' on pending/confirmed tickets")
print(f"   4. System validates stock availability")
print(f"   5. Ticket items loaded into POS cart")
print(f"   6. Cashier completes order in POS")
print(f"   7. Ticket status updated to 'completed'")

print(f"\n✅ TICKET PROCESSING TEST COMPLETE!")
print(f"📱 Ready to test in browser:")
print(f"   1. Login as cashier")
print(f"   2. Navigate to Customer Tickets")
print(f"   3. Process a pending ticket")
print(f"   4. Complete order in POS")

# Close connection
conn.close()
