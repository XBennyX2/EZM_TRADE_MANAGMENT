# store/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import StoreCreateForm, StoreManagerAssignForm
from .models import Store, StoreManager

@login_required
def create_store(request):
    if request.user.role != 'store_owner':
        messages.error(request, "Access denied.")
        return redirect('store_owner_page')

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