#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

def check_and_create_tables():
    cursor = connection.cursor()
    
    # Check if payment tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'payments_%';")
    tables = cursor.fetchall()
    print(f"Existing payment tables: {tables}")
    
    if not tables:
        print("Creating payment tables...")
        
        # Create ChapaTransaction table
        cursor.execute('''
            CREATE TABLE payments_chapatransaction (
                id TEXT PRIMARY KEY,
                chapa_tx_ref VARCHAR(100) UNIQUE NOT NULL,
                chapa_checkout_url TEXT,
                amount DECIMAL(12, 2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'ETB',
                description TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                chapa_response TEXT,
                webhook_data TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                paid_at DATETIME,
                customer_email VARCHAR(254) NOT NULL,
                customer_first_name VARCHAR(100) NOT NULL,
                customer_last_name VARCHAR(100) NOT NULL,
                customer_phone VARCHAR(20),
                supplier_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL
            )
        ''')
        print("Created ChapaTransaction table")
        
        # Create PaymentWebhookLog table
        cursor.execute('''
            CREATE TABLE payments_paymentwebhooklog (
                id TEXT PRIMARY KEY,
                webhook_data TEXT NOT NULL,
                signature VARCHAR(255),
                processed BOOLEAN DEFAULT 0,
                processing_error TEXT,
                created_at DATETIME NOT NULL,
                processed_at DATETIME,
                transaction_id TEXT
            )
        ''')
        print("Created PaymentWebhookLog table")
        
        # Create PurchaseOrderPayment table
        cursor.execute('''
            CREATE TABLE payments_purchaseorderpayment (
                id TEXT PRIMARY KEY,
                status VARCHAR(20) DEFAULT 'initial',
                order_items TEXT NOT NULL,
                subtotal DECIMAL(12, 2) NOT NULL,
                total_amount DECIMAL(12, 2) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                payment_confirmed_at DATETIME,
                notes TEXT,
                chapa_transaction_id TEXT UNIQUE NOT NULL,
                purchase_order_id INTEGER,
                supplier_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL
            )
        ''')
        print("Created PurchaseOrderPayment table")
        
        print("All payment tables created successfully!")
    else:
        print("Payment tables already exist")
    
    # Test if we can query the tables
    try:
        from payments.models import ChapaTransaction
        count = ChapaTransaction.objects.count()
        print(f"ChapaTransaction table accessible, count: {count}")
    except Exception as e:
        print(f"Error accessing ChapaTransaction: {e}")

if __name__ == "__main__":
    check_and_create_tables()
