<<<<<<< HEAD
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






=======
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Store
from .forms import StoreForm

class StoreOwnerRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is an admin or store owner."""
    def test_func(self):
        return self.request.user.role in ['admin', 'store_owner']

class StoreListView(LoginRequiredMixin, ListView):
    model = Store
    template_name = 'store/store_list.html' # We will create this template
    context_object_name = 'store'

class StoreCreateView(LoginRequiredMixin, StoreOwnerRequiredMixin, CreateView):
    model = Store
    form_class = StoreForm
    template_name = 'store/store_form.html'
    success_url = reverse_lazy('store_list') # Redirect to the list view on success

class StoreUpdateView(LoginRequiredMixin, StoreOwnerRequiredMixin, UpdateView):
    model = Store
    form_class = StoreForm
    template_name = 'store/store_form.html'
    success_url = reverse_lazy('store_list')

class StoreDeleteView(LoginRequiredMixin, StoreOwnerRequiredMixin, DeleteView):
    model = Store
    template_name = 'store/store_confirm_delete.html'
    success_url = reverse_lazy('store_list')
>>>>>>> 47f5317cd9a21712765f9056ed714eab714307ef
