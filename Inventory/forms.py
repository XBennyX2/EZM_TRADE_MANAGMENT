from django import forms
from .models import Product, Stock

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'material']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'material': forms.TextInput(attrs={'class': 'form-control'}),
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