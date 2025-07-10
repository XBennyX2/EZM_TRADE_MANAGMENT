from django import forms
from .models import (
    Product, Stock, Supplier, WarehouseProduct, Warehouse, PurchaseOrder, PurchaseOrderItem,
    SupplierProfile, SupplierProduct, PurchaseRequest, PurchaseRequestItem, ProductCategory
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
    """
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

    class Meta:
        model = SupplierProduct
        exclude = ['supplier', 'created_date', 'updated_date', 'category']

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
                'placeholder': 'Current stock quantity (optional)'
            }),

            # Product Images
            'product_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),

            # Status
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate category choices
        categories = ProductCategory.objects.filter(is_active=True).order_by('name')
        category_choices = [('', 'Select a category')]
        category_choices.extend([(cat.name, cat.name) for cat in categories])
        category_choices.append(('other', 'Other (specify below)'))

        self.fields['category_choice'].choices = category_choices

        # Set default currency to ETB
        self.fields['currency'].initial = 'ETB'
        self.fields['currency'].required = False

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
        self.fields['stock_quantity'].help_text = "Current available stock (optional)"
        self.fields['category_choice'].help_text = "Select an existing category or choose 'Other' to create a new one"

    def clean(self):
        cleaned_data = super().clean()
        category_choice = cleaned_data.get('category_choice')
        custom_category = cleaned_data.get('custom_category')

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

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Set the category from cleaned data
        if hasattr(self, 'cleaned_data') and 'category' in self.cleaned_data:
            instance.category = self.cleaned_data['category']

        if commit:
            instance.save()
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