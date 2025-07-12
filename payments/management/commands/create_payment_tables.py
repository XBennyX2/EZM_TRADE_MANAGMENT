from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create payment tables manually'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # Create ChapaTransaction table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments_chapatransaction (
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
                user_id INTEGER NOT NULL,
                FOREIGN KEY (supplier_id) REFERENCES Inventory_supplier (id),
                FOREIGN KEY (user_id) REFERENCES users_customuser (id)
            )
        ''')
        
        # Create PaymentWebhookLog table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments_paymentwebhooklog (
                id TEXT PRIMARY KEY,
                webhook_data TEXT NOT NULL,
                signature VARCHAR(255),
                processed BOOLEAN DEFAULT 0,
                processing_error TEXT,
                created_at DATETIME NOT NULL,
                processed_at DATETIME,
                transaction_id TEXT,
                FOREIGN KEY (transaction_id) REFERENCES payments_chapatransaction (id)
            )
        ''')
        
        # Create PurchaseOrderPayment table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments_purchaseorderpayment (
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
                user_id INTEGER NOT NULL,
                FOREIGN KEY (chapa_transaction_id) REFERENCES payments_chapatransaction (id),
                FOREIGN KEY (purchase_order_id) REFERENCES Inventory_purchaseorder (id),
                FOREIGN KEY (supplier_id) REFERENCES Inventory_supplier (id),
                FOREIGN KEY (user_id) REFERENCES users_customuser (id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chapa_tx_ref ON payments_chapatransaction (chapa_tx_ref)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chapa_status ON payments_chapatransaction (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chapa_user_status ON payments_chapatransaction (user_id, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chapa_supplier_status ON payments_chapatransaction (supplier_id, status)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_webhook_processed ON payments_paymentwebhooklog (processed)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_webhook_created ON payments_paymentwebhooklog (created_at)')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_status ON payments_purchaseorderpayment (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_user_status ON payments_purchaseorderpayment (user_id, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payment_supplier_status ON payments_purchaseorderpayment (supplier_id, status)')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created payment tables')
        )
