from django.contrib import admin
from .models import (
    Transaction, FinancialRecord, Receipt, Order,
    SupplierAccount, SupplierTransaction, SupplierPayment,
    SupplierCredit, SupplierInvoice
)

# Register existing models
admin.site.register(Transaction)
admin.site.register(FinancialRecord)
admin.site.register(Receipt)
admin.site.register(Order)

# Register supplier models
@admin.register(SupplierAccount)
class SupplierAccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'supplier', 'current_balance', 'payment_terms', 'is_active']
    list_filter = ['payment_terms', 'is_active', 'created_date']
    search_fields = ['account_number', 'supplier__name']
    readonly_fields = ['account_number', 'created_date', 'updated_date']

@admin.register(SupplierTransaction)
class SupplierTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_number', 'supplier_account', 'transaction_type', 'amount', 'status', 'transaction_date']
    list_filter = ['transaction_type', 'status', 'transaction_date']
    search_fields = ['transaction_number', 'supplier_account__supplier__name', 'reference_number']
    readonly_fields = ['transaction_number', 'transaction_date']

@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'supplier_transaction', 'payment_method', 'amount_paid', 'status', 'payment_date']
    list_filter = ['payment_method', 'status', 'payment_date']
    search_fields = ['payment_number', 'bank_reference', 'check_number']
    readonly_fields = ['payment_number', 'payment_date']

@admin.register(SupplierCredit)
class SupplierCreditAdmin(admin.ModelAdmin):
    list_display = ['credit_number', 'supplier_transaction', 'credit_type', 'credit_amount', 'status', 'credit_date']
    list_filter = ['credit_type', 'status', 'credit_date']
    search_fields = ['credit_number', 'original_invoice']
    readonly_fields = ['credit_number', 'credit_date']

@admin.register(SupplierInvoice)
class SupplierInvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'purchase_order', 'total_amount', 'status', 'invoice_date', 'due_date']
    list_filter = ['status', 'invoice_date', 'due_date']
    search_fields = ['invoice_number', 'purchase_order__order_number']
    readonly_fields = ['received_date', 'total_amount']
