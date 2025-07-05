from django import forms
from .models import Product, Stock

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'description', 'price', 'material',
            'size', 'variation', 'product_type', 'supplier_company',
            'batch_number', 'expiry_date', 'room', 'shelf', 'floor',
            'storing_condition'
        ]
        widgets = {
            # Basic Information
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Product description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'material': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Material composition'}),

            # Product Specifications
            'size': forms.Select(attrs={'class': 'form-control'}),
            'variation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Color, model, style, etc.'}),
            'product_type': forms.Select(attrs={'class': 'form-control'}),

            # Supplier Information
            'supplier_company': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier company name'}),

            # Batch and Tracking
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch/Lot number'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            # Storage Location
            'room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Storage room'}),
            'shelf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shelf location'}),
            'floor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Floor level'}),

            # Storage Conditions
            'storing_condition': forms.Select(attrs={'class': 'form-control'}),
        }

        labels = {
            'name': 'Product Name',
            'category': 'Category',
            'description': 'Description',
            'price': 'Base Price ($)',
            'material': 'Material',
            'size': 'Size',
            'variation': 'Variation',
            'product_type': 'Product Type',
            'supplier_company': 'Supplier Company',
            'batch_number': 'Batch Number',
            'expiry_date': 'Expiry Date',
            'room': 'Storage Room',
            'shelf': 'Shelf',
            'floor': 'Floor',
            'storing_condition': 'Storage Condition',
        }
        
class StockCreateForm(forms.ModelForm):
    """
    A form for a Store Manager to add a new product line to their store.
    """
    class Meta:
        model = Stock
        # The manager selects a product and sets its initial quantity and price.
        # The 'store' will be set automatically in the view, so it's not in the form.
        fields = ['product', 'quantity', 'selling_price', 'low_stock_threshold']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class StockUpdateForm(forms.ModelForm):
    """
    A form for a Store Manager to update the quantity and price of an existing stock item.
    """
    class Meta:
        model = Stock
        # When updating, a manager should only change these fields.
        fields = ['quantity', 'selling_price', 'low_stock_threshold']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
        }