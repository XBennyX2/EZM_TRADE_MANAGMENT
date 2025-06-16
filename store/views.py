# store/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import StoreCreateForm
from .models import Store, StoreManager

@login_required
def create_store(request):
    if request.user.role != 'store_owner':
        messages.error(request, "Access denied.")
        return redirect('')

    if request.method == 'POST':
        form = StoreCreateForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            store.owner = request.user  # <-- set the owner
            store.save()
            messages.success(request, f"Store '{store.name}' created successfully.")
            return redirect('store_owner_page')  # or wherever you want
    else:
        form = StoreCreateForm()

    return render(request, 'store/create_store.html', {'form': form})

# stores/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Store, StoreManager
from .forms import AssignManagerForm
from users.models import CustomUser


@login_required
def manage_store(request, store_id):
    store = get_object_or_404(Store, id=store_id, owner=request.user)

    current_manager = None
    if hasattr(store, 'manager_assignment') and store.manager_assignment.is_active:
        current_manager = store.manager_assignment.manager

    if request.method == 'POST':
        form = AssignManagerForm(request.POST)
        if form.is_valid():
            new_manager = form.cleaned_data['manager']

            # Promote new_manager to 'store_manager' role before saving assignment
            if new_manager.role != 'store_manager':
                new_manager.role = 'store_manager'
                new_manager.save(update_fields=['role'])

            # Deactivate old manager assignment if exists
            if hasattr(store, 'manager_assignment') and store.manager_assignment.is_active:
                old_assignment = store.manager_assignment
                old_manager = old_assignment.manager
                old_assignment.is_active = False
                old_assignment.save()

                # Demote old manager if they are no longer managing any active stores
                still_manager = StoreManager.objects.filter(manager=old_manager, is_active=True).exists()
                if not still_manager and old_manager.role == 'store_manager':
                    old_manager.role = 'customer'
                    old_manager.save(update_fields=['role'])

            # Create or reactivate assignment for new_manager
            assignment = StoreManager.objects.filter(store=store, manager=new_manager).first()
            if assignment:
                assignment.is_active = True
                assignment.save()
            else:
                # Remove any other assignments for this store to ensure single active manager
                StoreManager.objects.filter(store=store).delete()
                StoreManager.objects.create(store=store, manager=new_manager, is_active=True)

            messages.success(request, f"{new_manager.get_full_name()} assigned as manager for {store.name}.")
            return redirect('store_owner_page')
    else:
        form = AssignManagerForm(initial={'manager': current_manager.id if current_manager else None})

    return render(request, 'store/manage_store.html', {
        'store': store,
        'form': form,
        'current_manager': current_manager,
    })

from .forms import AssignCashierForm
from .models import Store, StoreCashier

def assign_cashier(request, store_id):
    store = get_object_or_404(Store, id=store_id)

    if request.user != store.manager_assignment.manager:
        return redirect('unauthorized_page')  # Only store manager allowed

    if request.method == 'POST':
        form = AssignCashierForm(request.POST)
        if form.is_valid():
            new_cashier = form.cleaned_data['cashier']

            # Ensure new cashier role is 'cashier'
            if new_cashier.role != 'cashier':
                new_cashier.role = 'cashier'
                new_cashier.save(update_fields=['role'])

            try:
                # Check if store already has a cashier assigned
                existing_assignment = StoreCashier.objects.get(store=store, is_active=True)

                old_cashier = existing_assignment.cashier
                if old_cashier != new_cashier:
                    # Revert old cashier's role to 'customer'
                    if old_cashier.role == 'cashier':
                        old_cashier.role = 'customer'
                        old_cashier.save(update_fields=['role'])

                    # Update assignment to new cashier
                    existing_assignment.cashier = new_cashier
                    existing_assignment.save()
                    messages.success(request, f"Cashier changed to {new_cashier.get_full_name()} for store {store.name}.")

                else:
                    messages.info(request, f"{new_cashier.get_full_name()} is already the cashier for this store.")

            except StoreCashier.DoesNotExist:
                # No existing assignment — create a new one
                StoreCashier.objects.create(store=store, cashier=new_cashier, is_active=True)
                messages.success(request, f"{new_cashier.get_full_name()} assigned as cashier for {store.name}.")

            return redirect('store_manager_page')
    else:
        form = AssignCashierForm()

    return render(request, 'store/assign_cashier.html', {'form': form, 'store': store})
@login_required
def revoke_cashier(request, store_id, cashier_id):
    store = get_object_or_404(Store, id=store_id)
    cashier = get_object_or_404(CustomUser, id=cashier_id)

    if request.user != store.manager_assignment.manager:
        return redirect('')

    # Try to get the assignment; if it doesn't exist, warn and redirect
    try:
        assignment = StoreCashier.objects.get(store=store, cashier=cashier)
    except StoreCashier.DoesNotExist:
        messages.warning(request, "This cashier is not assigned to your store.")
        return redirect('store_manager_page')

    # Delete the assignment instead of marking inactive
    assignment.delete()

    # Optionally revert role to 'customer' if no other assignments exist
    other_assignments = StoreCashier.objects.filter(cashier=cashier).exists()
    if not other_assignments and cashier.role == 'cashier':
        cashier.role = 'customer'
        cashier.save(update_fields=['role'])

    messages.success(request, f"{cashier.get_full_name()} has been removed as cashier.")
    return redirect('store_manager_page')
