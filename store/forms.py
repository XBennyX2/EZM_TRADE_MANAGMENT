# store/forms.py
from django import forms
from .models import Store

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'address', 'phone_number']  # exclude 'owner' to avoid user input


from django import forms
from users.models import CustomUser

class AssignManagerForm(forms.Form):
    manager = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='store_manager'),
        label="Select Manager",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Choose a store manager..."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active store managers who are not already assigned to a store
        self.fields['manager'].queryset = CustomUser.objects.filter(
            role='store_manager',
            is_active=True,
            managed_store__isnull=True  # Only show managers not already assigned to a store
        )

from django import forms
from users.models import CustomUser
from .models import StoreCashier


class AssignCashierForm(forms.Form):
    cashier = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='cashier', is_active=True, store__isnull=True),
        label="Select Cashier",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Only unassigned cashiers are shown"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show cashiers who are not assigned to any store
        self.fields['cashier'].queryset = CustomUser.objects.filter(
            role='cashier',
            is_active=True,
            store__isnull=True
        )


