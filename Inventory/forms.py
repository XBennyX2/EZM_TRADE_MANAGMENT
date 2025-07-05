from django import forms
from .models import Product, Stock, Supplier, WarehouseProduct, Warehouse, PurchaseOrder, PurchaseOrderItem

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


class SupplierForm(forms.ModelForm):
    """
    Form for creating and editing suppliers.
    """
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'email', 'phone', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier Name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WarehouseProductForm(forms.ModelForm):
    """
    Form for creating and editing warehouse products.
    """
    class Meta:
        model = WarehouseProduct
        fields = [
            'product_id', 'product_name', 'category', 'supplier', 'quantity_in_stock',
            'unit_price', 'minimum_stock_level', 'maximum_stock_level', 'reorder_point',
            'sku', 'barcode', 'weight', 'dimensions', 'warehouse_location', 'is_active'
        ]
        widgets = {
            'product_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product ID'}),
            'product_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'minimum_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'maximum_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'reorder_point': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SKU'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barcode'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'L x W x H'}),
            'warehouse_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aisle A, Shelf 3'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class WarehouseForm(forms.ModelForm):
    """
    Form for creating and editing warehouse information.
    """
    class Meta:
        model = Warehouse
        fields = ['name', 'address', 'phone', 'email', 'manager_name', 'capacity', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Warehouse Name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'manager_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Manager Name'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PurchaseOrderForm(forms.ModelForm):
    """
    Form for creating and editing purchase orders.
    """
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'expected_delivery_date', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'expected_delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes or special instructions'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active suppliers
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)


class PurchaseOrderItemForm(forms.ModelForm):
    """
    Form for adding items to purchase orders.
    """
    class Meta:
        model = PurchaseOrderItem
        fields = ['warehouse_product', 'quantity_ordered', 'unit_price']
        widgets = {
            'warehouse_product': forms.Select(attrs={'class': 'form-control'}),
            'quantity_ordered': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
        }

    def __init__(self, *args, supplier=None, **kwargs):
        super().__init__(*args, **kwargs)
        if supplier:
            # Only show products from the selected supplier
            self.fields['warehouse_product'].queryset = WarehouseProduct.objects.filter(
                supplier=supplier,
                is_active=True
            )
        else:
            self.fields['warehouse_product'].queryset = WarehouseProduct.objects.filter(is_active=True)


# Formset for handling multiple purchase order items
PurchaseOrderItemFormSet = forms.inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)