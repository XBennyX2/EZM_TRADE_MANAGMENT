from django import forms
from .models import (
    Product, Stock, Supplier, WarehouseProduct, Warehouse, PurchaseOrder, PurchaseOrderItem,
    SupplierProfile, SupplierProduct, PurchaseRequest, PurchaseRequestItem, ProductCategory,
    RestockRequest, StoreStockTransferRequest
)

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


class WarehouseProductStockEditForm(forms.ModelForm):
    """
    Simple form for Head Managers to edit warehouse product stock quantities.
    """
    class Meta:
        model = WarehouseProduct
        fields = ['quantity_in_stock']
        widgets = {
            'quantity_in_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': 'Enter stock quantity'
            })
        }

    def clean_quantity_in_stock(self):
        """Validate that stock quantity is non-negative"""
        quantity = self.cleaned_data.get('quantity_in_stock')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError("Stock quantity cannot be negative.")
        return quantity


class ProductStockThresholdEditForm(forms.ModelForm):
    """
    Form for Head Managers to edit product minimum stock level (threshold) only.
    """
    class Meta:
        model = Product
        fields = ['minimum_stock_level']
        widgets = {
            'minimum_stock_level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': 'Enter minimum stock threshold'
            })
        }

    def clean_minimum_stock_level(self):
        """Validate that minimum stock level is non-negative"""
        threshold = self.cleaned_data.get('minimum_stock_level')
        if threshold is not None and threshold < 0:
            raise forms.ValidationError("Minimum stock level cannot be negative.")
        return threshold


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
            # Only show products from the selected supplier with stock
            self.fields['warehouse_product'].queryset = WarehouseProduct.objects.filter(
                supplier=supplier,
                is_active=True,
                quantity_in_stock__gt=0
            )
        else:
            self.fields['warehouse_product'].queryset = WarehouseProduct.objects.filter(
                is_active=True,
                quantity_in_stock__gt=0
            )

        # Customize the display of warehouse products to show unique identifiers
        self.fields['warehouse_product'].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        """Custom label to show product name with unique identifier"""
        return f"{obj.product_name} - [{obj.product_id}] (Stock: {obj.quantity_in_stock})"


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


# --- Supplier Onboarding Forms ---

class SupplierProfileForm(forms.ModelForm):
    """
    Comprehensive form for supplier onboarding and profile setup.
    """
    class Meta:
        model = SupplierProfile
        exclude = ['supplier', 'is_onboarding_complete', 'onboarding_completed_date']

        widgets = {
            # Business Information
            'business_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your business/company name'
            }),
            'business_type': forms.Select(attrs={'class': 'form-control'}),
            'business_registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business registration or license number'
            }),
            'tax_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax ID or EIN number'
            }),

            # Contact Details
            'primary_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primary contact person name'
            }),
            'primary_contact_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Job title or position'
            }),
            'primary_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'primary_contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@company.com'
            }),

            # Business Address
            'business_address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Street address'
            }),
            'business_address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment, suite, unit, building, floor, etc.'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state_province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State or Province'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ZIP or Postal Code'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country'
            }),

            # Business Operations
            'product_categories': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'e.g., Electronics, Furniture, Clothing, Food & Beverages'
            }),
            'estimated_delivery_timeframe': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 3-5 business days, 1-2 weeks'
            }),
            'preferred_payment_terms': forms.Select(attrs={'class': 'form-control'}),
            'minimum_order_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),

            # Certifications and Compliance
            'business_license': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Business license number'
            }),
            'certifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List any relevant certifications (ISO, FDA, etc.)'
            }),
            'insurance_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Insurance provider and policy details'
            }),

            # Banking Information
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank name'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account number'
            }),
            'routing_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Routing number'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mark required fields
        required_fields = [
            'business_name', 'business_type', 'primary_contact_name', 'primary_contact_phone', 'primary_contact_email',
            'business_address_line1', 'city', 'state_province', 'postal_code', 'country',
            'product_categories', 'estimated_delivery_timeframe', 'preferred_payment_terms'
        ]

        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                # Add asterisk to label for required fields
                if self.fields[field_name].label:
                    self.fields[field_name].label += ' *'
                else:
                    self.fields[field_name].label = field_name.replace('_', ' ').title() + ' *'

        # Add help text and validation messages
        self.fields['business_name'].help_text = "Legal name of your business or company"
        self.fields['primary_contact_name'].help_text = "Primary contact person for business communications"
        self.fields['primary_contact_email'].help_text = "Business email address for official communications"
        self.fields['primary_contact_phone'].help_text = "Primary business phone number"
        self.fields['product_categories'].help_text = "Separate multiple categories with commas (e.g., Electronics, Furniture, Clothing)"
        self.fields['estimated_delivery_timeframe'].help_text = "Typical delivery time for your products (e.g., 3-5 business days, 1-2 weeks)"
        self.fields['minimum_order_value'].help_text = "Minimum order value in USD (leave blank if no minimum)"

        # Add custom CSS classes for better styling
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})
                if field.required:
                    field.widget.attrs.update({'required': 'required'})

    def clean_primary_contact_email(self):
        """Validate contact email format"""
        email = self.cleaned_data.get('primary_contact_email')
        if email:
            try:
                from django.core.validators import validate_email
                validate_email(email)
            except forms.ValidationError:
                raise forms.ValidationError("Please enter a valid email address.")
        return email

    def clean_primary_contact_phone(self):
        """Validate business phone format"""
        phone = self.cleaned_data.get('primary_contact_phone')
        if phone:
            # Remove common phone formatting characters
            cleaned_phone = ''.join(filter(str.isdigit, phone))
            if len(cleaned_phone) < 10:
                raise forms.ValidationError("Please enter a valid phone number with at least 10 digits.")
        return phone

    def clean_minimum_order_value(self):
        """Validate minimum order value"""
        value = self.cleaned_data.get('minimum_order_value')
        if value is not None and value < 0:
            raise forms.ValidationError("Minimum order value cannot be negative.")
        return value

    def clean_product_categories(self):
        """Validate and format product categories"""
        categories = self.cleaned_data.get('product_categories')
        if categories:
            # Split by comma and clean up each category
            category_list = [cat.strip() for cat in categories.split(',') if cat.strip()]
            if len(category_list) == 0:
                raise forms.ValidationError("Please enter at least one product category.")
            # Rejoin cleaned categories
            return ', '.join(category_list)
        return categories


class SupplierProductForm(forms.ModelForm):
    """
    Form for suppliers to add/edit products in their catalog.
    Suppliers can set and edit stock quantities which are visible to Head Managers.
    """
    # Product name as free text input
    product_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'product_name_input',
            'placeholder': 'Enter product name...',
            'autocomplete': 'off'
        }),
        help_text="Enter any product name you want to offer"
    )

    # Optional warehouse product reference (for existing warehouse products)
    warehouse_product = forms.ModelChoiceField(
        queryset=WarehouseProduct.objects.all(),
        required=False,
        widget=forms.HiddenInput(),
        help_text="Optional reference to warehouse product if applicable"
    )

    # Stock quantity field - suppliers can edit this
    stock_quantity = forms.IntegerField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter available stock quantity',
            'min': '0'
        }),
        help_text="Current stock quantity available for this product"
    )

    category_choice = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'category_choice'})
    )
    custom_category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new category name',
            'id': 'custom_category',
            'style': 'display: none;'
        })
    )

    def __init__(self, *args, **kwargs):
        self.supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)

        # Set up warehouse product queryset for optional reference
        self.fields['warehouse_product'].queryset = WarehouseProduct.objects.filter(
            is_active=True
        )

        # Populate construction-related category choices
        construction_categories = [
            ('Plumbing Supplies', 'Plumbing Supplies'),
            ('Electrical Components', 'Electrical Components'),
            ('Cement & Masonry', 'Cement & Masonry'),
            ('Hardware & Tools', 'Hardware & Tools'),
            ('Paint & Finishing', 'Paint & Finishing'),
            ('Roofing Materials', 'Roofing Materials'),
            ('Insulation & Drywall', 'Insulation & Drywall'),
            ('Flooring Materials', 'Flooring Materials'),
            ('Windows & Doors', 'Windows & Doors'),
            ('Safety Equipment', 'Safety Equipment'),
        ]

        category_choices = [('', 'Select a category')]
        category_choices.extend(construction_categories)
        category_choices.append(('other', 'Other (specify below)'))

        self.fields['category_choice'].choices = category_choices

        # Set default currency to ETB
        self.fields['currency'].initial = 'ETB'
        self.fields['currency'].required = False

        # If editing existing product, set the current product name as selected
        if self.instance and self.instance.pk:
            if self.instance.product_name:
                self.fields['product_name'].initial = self.instance.product_name
            if self.instance.warehouse_product:
                self.fields['warehouse_product'].initial = self.instance.warehouse_product

        # Set initial value if editing existing product
        if self.instance and self.instance.pk and hasattr(self.instance, 'category'):
            if self.instance.category:
                # Check if the category exists in our choices
                existing_categories = [choice[0] for choice in category_choices[1:-1]]  # Exclude empty and 'other'
                if self.instance.category in existing_categories:
                    self.fields['category_choice'].initial = self.instance.category
                else:
                    self.fields['category_choice'].initial = 'other'
                    self.fields['custom_category'].initial = self.instance.category
                    self.fields['custom_category'].widget.attrs['style'] = ''

        # Add help text
        self.fields['product_code'].help_text = "Unique identifier for this product"
        self.fields['minimum_order_quantity'].help_text = "Minimum quantity customers must order"
        self.fields['maximum_order_quantity'].help_text = "Maximum quantity per order (leave blank for unlimited)"
        self.fields['stock_quantity'].help_text = "Current available stock (automatically decreases when orders are placed)"
        self.fields['category_choice'].help_text = "Select an existing category or choose 'Other' to create a new one"

    class Meta:
        model = SupplierProduct
        exclude = ['supplier', 'created_date', 'updated_date', 'category']

        # Custom field ordering including stock_quantity
        field_order = [
            'warehouse_product', 'product_name', 'product_code', 'description',
            'category_choice', 'custom_category', 'subcategory', 'unit_price',
            'currency', 'minimum_order_quantity', 'maximum_order_quantity',
            'stock_quantity'
        ]

        widgets = {
            # Product Information
            'product_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'product_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SKU or product code (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed product description'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product category'
            }),
            'subcategory': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product subcategory (optional)'
            }),

            # Pricing and Quantities
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'USD'
            }),
            'minimum_order_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1'
            }),
            'maximum_order_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave blank for no limit'
            }),

            # Product Specifications
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Technical specifications, features, etc.'
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'L x W x H (e.g., 10 x 5 x 3 inches)'
            }),
            'weight': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Weight (e.g., 2.5 lbs, 1.2 kg)'
            }),
            'color_options': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Available colors (comma-separated)'
            }),
            'material': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Material composition'
            }),

            # Availability and Delivery
            'availability_status': forms.Select(attrs={'class': 'form-control'}),
            'estimated_delivery_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2-3 business days, 1 week'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter available stock quantity',
                'min': '0'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter available stock quantity',
                'min': '0'
            }),

            # Product Images
            'product_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),

            # Status
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



    def clean(self):
        cleaned_data = super().clean()
        category_choice = cleaned_data.get('category_choice')
        custom_category = cleaned_data.get('custom_category')
        product_code = cleaned_data.get('product_code')
        product_name = cleaned_data.get('product_name')

        # Get warehouse product from form data (optional)
        warehouse_product = cleaned_data.get('warehouse_product')

        # Validate product name is provided
        if not product_name or not product_name.strip():
            raise forms.ValidationError("Product name is required.")

        # If warehouse product is selected, validate it
        if warehouse_product:
            # Validate warehouse product is still available
            if not warehouse_product.is_active:
                raise forms.ValidationError(
                    f"Product '{warehouse_product.product_name}' is no longer active."
                )

            if warehouse_product.quantity_in_stock <= 0:
                raise forms.ValidationError(
                    f"Product '{warehouse_product.product_name}' is out of stock."
                )

            # Check for duplicates if supplier is provided
            if self.supplier:
                existing = SupplierProduct.objects.filter(
                    supplier=self.supplier,
                    warehouse_product=warehouse_product
                ).exclude(pk=self.instance.pk if self.instance.pk else None)

                if existing.exists():
                    raise forms.ValidationError(
                        f"You have already added '{warehouse_product.product_name}' to your catalog."
                    )

        # Check for duplicate product names for this supplier (regardless of warehouse product)
        if self.supplier and product_name:
            existing_by_name = SupplierProduct.objects.filter(
                supplier=self.supplier,
                product_name__iexact=product_name.strip()
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            if existing_by_name.exists():
                raise forms.ValidationError(
                    f"You already have a product named '{product_name}' in your catalog. "
                    "Please use a different product name."
                )

        # Handle category validation
        if category_choice == 'other':
            if not custom_category:
                raise forms.ValidationError("Please enter a custom category name when 'Other' is selected.")
            # Create or get the category
            category, created = ProductCategory.objects.get_or_create(
                name=custom_category.strip(),
                defaults={'is_active': True}
            )
            cleaned_data['category'] = category.name
        elif category_choice:
            cleaned_data['category'] = category_choice
        else:
            raise forms.ValidationError("Please select a category.")

        # Handle product code validation
        if self.supplier:
            if product_code:
                # Check if product code already exists for this supplier
                existing_product = SupplierProduct.objects.filter(
                    supplier=self.supplier,
                    product_code=product_code
                ).exclude(pk=self.instance.pk if self.instance else None)

                if existing_product.exists():
                    raise forms.ValidationError(
                        f"A product with code '{product_code}' already exists in your catalog. "
                        "Please use a different product code."
                    )
            else:
                # Auto-generate product code if not provided
                import uuid
                import time
                base_code = f"SP{int(time.time())}"
                counter = 1
                while SupplierProduct.objects.filter(
                    supplier=self.supplier,
                    product_code=base_code
                ).exists():
                    base_code = f"SP{int(time.time())}{counter}"
                    counter += 1
                cleaned_data['product_code'] = base_code

        # Validate stock quantity and set availability status
        stock_quantity = cleaned_data.get('stock_quantity')
        if stock_quantity is not None:
            if stock_quantity < 0:
                raise forms.ValidationError("Stock quantity cannot be negative.")

            # Set availability status based on stock quantity
            if stock_quantity == 0:
                cleaned_data['availability_status'] = 'out_of_stock'
            elif stock_quantity <= 10:
                cleaned_data['availability_status'] = 'limited_stock'
            else:
                cleaned_data['availability_status'] = 'in_stock'

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Get the warehouse product from cleaned data (optional)
        if hasattr(self, 'cleaned_data') and 'warehouse_product' in self.cleaned_data:
            warehouse_product = self.cleaned_data['warehouse_product']
            if warehouse_product:
                # Auto-populate other fields if not provided (but don't override user input)
                if not instance.product_code:
                    instance.product_code = warehouse_product.product_id
                if not instance.description:
                    instance.description = f"Product from warehouse inventory - {warehouse_product.product_name}"
                if not instance.unit_price:
                    instance.unit_price = warehouse_product.unit_price

                # Set the warehouse product reference
                instance.warehouse_product = warehouse_product

        # Set the category from cleaned data
        if hasattr(self, 'cleaned_data') and 'category' in self.cleaned_data:
            instance.category = self.cleaned_data['category']

        # Set the product code from cleaned data (auto-generated if not provided)
        if hasattr(self, 'cleaned_data') and 'product_code' in self.cleaned_data:
            instance.product_code = self.cleaned_data['product_code']

        if commit:
            instance.save()
        return instance


class SupplierStockAdjustmentForm(forms.ModelForm):
    """
    Form for suppliers to manually adjust their stock levels.
    This is separate from product editing and allows stock corrections/increases.
    """
    stock_quantity = forms.IntegerField(
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new stock quantity',
            'min': '0'
        }),
        help_text="Update your current stock quantity"
    )

    adjustment_reason = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reason for stock adjustment (optional)'
        }),
        help_text="Optional: Explain why you're adjusting the stock"
    )

    class Meta:
        model = SupplierProduct
        fields = ['stock_quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['stock_quantity'].initial = self.instance.stock_quantity

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity is not None and stock_quantity < 0:
            raise forms.ValidationError("Stock quantity cannot be negative.")
        return stock_quantity

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Update availability status based on new stock quantity
        if instance.stock_quantity == 0:
            instance.availability_status = 'out_of_stock'
        elif instance.stock_quantity <= 10:
            instance.availability_status = 'limited_stock'
        else:
            instance.availability_status = 'in_stock'

        if commit:
            instance.save()

            # Log the stock adjustment
            import logging
            logger = logging.getLogger(__name__)
            reason = self.cleaned_data.get('adjustment_reason', 'Manual stock adjustment')
            logger.info(f"Stock manually adjusted for {instance.product_name} (ID: {instance.id}): "
                       f"New stock: {instance.stock_quantity}. Reason: {reason}")

        return instance


# --- Purchase Request Forms ---

class PurchaseRequestForm(forms.ModelForm):
    """
    Form for Head Managers to create purchase requests to suppliers.
    """
    class Meta:
        model = PurchaseRequest
        exclude = [
            'request_number', 'requested_by', 'status', 'supplier_notes',
            'estimated_total', 'quoted_total', 'sent_date', 'response_date'
        ]

        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Purchase request title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional details or requirements'
            }),
            'required_delivery_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Delivery address'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Internal notes (not visible to supplier)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter suppliers to only show active ones
        self.fields['supplier'].queryset = Supplier.objects.filter(is_active=True)
        self.fields['required_delivery_date'].help_text = "When do you need this delivered?"


class PurchaseRequestItemForm(forms.ModelForm):
    """
    Form for individual items in a purchase request.
    """
    class Meta:
        model = PurchaseRequestItem
        exclude = [
            'purchase_request', 'total_price', 'quoted_unit_price',
            'quoted_total_price', 'supplier_notes'
        ]

        widgets = {
            'supplier_product': forms.Select(attrs={'class': 'form-control'}),
            'requested_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'readonly': True
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any special requirements for this item'
            }),
        }

    def __init__(self, *args, **kwargs):
        supplier = kwargs.pop('supplier', None)
        super().__init__(*args, **kwargs)

        if supplier:
            # Filter products to only show products from the selected supplier
            self.fields['supplier_product'].queryset = SupplierProduct.objects.filter(
                supplier=supplier,
                is_active=True
            )
        else:
            self.fields['supplier_product'].queryset = SupplierProduct.objects.none()

        # Customize the display of supplier products to show unique identifiers
        self.fields['supplier_product'].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        """Custom label to show product name with unique identifier"""
        warehouse_info = ""
        if obj.warehouse_product:
            warehouse_info = f" - [{obj.warehouse_product.product_id}]"
        return f"{obj.product_name}{warehouse_info} (Code: {obj.product_code})"


# Formset for Purchase Request Items
PurchaseRequestItemFormSet = forms.inlineformset_factory(
    PurchaseRequest,
    PurchaseRequestItem,
    form=PurchaseRequestItemForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)


# --- Store Manager Request Forms ---

class RestockRequestForm(forms.ModelForm):
    """
    Form for Store Managers to submit restock requests to Head Manager.
    """
    class Meta:
        model = RestockRequest
        fields = ['product', 'requested_quantity', 'priority']

        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'requested_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter quantity needed',
                'required': True
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
        }

        labels = {
            'product': 'Product *',
            'requested_quantity': 'Requested Quantity *',
            'priority': 'Priority Level *',
        }

    def __init__(self, *args, **kwargs):
        store = kwargs.pop('store', None)
        super().__init__(*args, **kwargs)

        if store:
            # For restock requests, show products available from:
            # 1. Warehouse products
            # 2. Products in other stores
            # 3. All products in the system (for potential restocking)
            from .models import Stock, WarehouseProduct
            from store.models import Store
            from django.db import models

            # Get products available in warehouse
            warehouse_product_names = WarehouseProduct.objects.filter(
                quantity_in_stock__gt=0,
                is_active=True
            ).values_list('product_name', flat=True)

            # Get products available in other stores
            other_stores_products = Stock.objects.filter(
                quantity__gt=0
            ).exclude(store=store).values_list('product', flat=True)

            # Combine all available products for restocking
            # Include products that match warehouse product names or are in other stores
            available_products = Product.objects.filter(
                models.Q(id__in=other_stores_products) |
                models.Q(name__in=warehouse_product_names)
            ).distinct()

            self.fields['product'].queryset = available_products
        else:
            self.fields['product'].queryset = Product.objects.none()

    def clean_requested_quantity(self):
        """Validate requested quantity is positive"""
        quantity = self.cleaned_data.get('requested_quantity')
        if quantity and quantity <= 0:
            raise forms.ValidationError("Requested quantity must be greater than 0.")
        return quantity




class StoreStockTransferRequestForm(forms.ModelForm):
    """
    Form for Store Managers to submit stock transfer requests to other stores.
    """
    class Meta:
        model = StoreStockTransferRequest
        fields = ['product', 'to_store', 'requested_quantity', 'priority']

        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'to_store': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'requested_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Enter quantity to transfer',
                'required': True
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explain why this transfer is needed...',
                'required': True
            }),
        }

        labels = {
            'product': 'Product *',
            'to_store': 'Destination Store *',
            'requested_quantity': 'Quantity to Transfer *',
            'priority': 'Priority Level *',
            'reason': 'Transfer Justification *',
        }

    def __init__(self, *args, **kwargs):
        from_store = kwargs.pop('from_store', None)
        super().__init__(*args, **kwargs)

        if from_store:
            # For transfer requests, show products available in OTHER stores
            # (excluding warehouse and current store)
            # This allows requesting products FROM other stores TO current store
            from .models import Stock
            from store.models import Store

            # Get products available in other stores (excluding current store)
            other_stores_products = Stock.objects.filter(
                quantity__gt=0
            ).exclude(store=from_store).values_list('product', flat=True).distinct()

            self.fields['product'].queryset = Product.objects.filter(
                id__in=other_stores_products
            ).order_by('name')

            # Only show other stores (exclude the current store)
            self.fields['to_store'].queryset = Store.objects.exclude(id=from_store.id)
        else:
            self.fields['product'].queryset = Product.objects.none()
            self.fields['to_store'].queryset = Store.objects.none()

    def clean_requested_quantity(self):
        """Validate requested quantity is positive and available"""
        quantity = self.cleaned_data.get('requested_quantity')
        if quantity and quantity <= 0:
            raise forms.ValidationError("Transfer quantity must be greater than 0.")
        return quantity

    def clean_reason(self):
        """Validate reason is not empty and has minimum length"""
        reason = self.cleaned_data.get('reason', '').strip()
        if not reason:
            raise forms.ValidationError("Please provide a reason for this transfer request.")
        if len(reason) < 10:
            raise forms.ValidationError("Please provide a more detailed reason (at least 10 characters).")
        return reason

    def clean(self):
        """Additional validation for the entire form"""
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        to_store = cleaned_data.get('to_store')
        requested_quantity = cleaned_data.get('requested_quantity')

        if product and to_store and requested_quantity:
            # Check if there's sufficient stock in the source store
            from .models import Stock
            try:
                stock = Stock.objects.get(product=product, store=self.initial.get('from_store'))
                if requested_quantity > stock.quantity:
                    raise forms.ValidationError(
                        f"Cannot transfer {requested_quantity} units. Only {stock.quantity} units available in stock."
                    )
            except Stock.DoesNotExist:
                raise forms.ValidationError("Selected product is not available in your store.")

        return cleaned_data


# --- Supplier Product Search and Filter Forms ---

class SupplierProductSearchForm(forms.Form):
    """
    Form for searching and filtering supplier products.
    """
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search products...'
        })
    )

    category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Category'
        })
    )

    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        empty_label="All Suppliers",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    availability_status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + SupplierProduct.AVAILABILITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    min_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Min price'
        })
    )

    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Max price'
        })
    )