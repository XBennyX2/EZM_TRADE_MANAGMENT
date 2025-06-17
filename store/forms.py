# store/forms.py
from django import forms
from .models import Store

class StoreCreateForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'location']  # exclude 'owner' to avoid user input


from django import forms
from users.models import CustomUser

class AssignManagerForm(forms.Form):
    manager = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__in=['store_manager', '']),
        label="Select Manager",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Further refine queryset if needed, e.g., only verified users
        self.fields['manager'].queryset = CustomUser.objects.filter(
            is_active=True,
            is_verified=True
        ).exclude(role__in=['store_owner', 'admin'])

from django import forms
from users.models import CustomUser
from store.models import StoreCashier

class AssignCashierForm(forms.Form):
    cashier = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        label='Select Cashier',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Step 1: Get all user IDs that are already active cashiers
        assigned_cashier_ids = StoreCashier.objects.filter(is_active=True).values_list('cashier_id', flat=True)

        # Step 2: Filter out those users, and only show verified customers
        self.fields['cashier'].queryset = CustomUser.objects.filter(
            role='customer',
            is_verified=True
        ).exclude(id__in=assigned_cashier_ids)

