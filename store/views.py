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
    template_name = 'stores/store_list.html' # We will create this template
    context_object_name = 'stores'

class StoreCreateView(LoginRequiredMixin, StoreOwnerRequiredMixin, CreateView):
    model = Store
    form_class = StoreForm
    template_name = 'stores/store_form.html'
    success_url = reverse_lazy('store_list') # Redirect to the list view on success

class StoreUpdateView(LoginRequiredMixin, StoreOwnerRequiredMixin, UpdateView):
    model = Store
    form_class = StoreForm
    template_name = 'stores/store_form.html'
    success_url = reverse_lazy('store_list')

class StoreDeleteView(LoginRequiredMixin, StoreOwnerRequiredMixin, DeleteView):
    model = Store
    template_name = 'stores/store_confirm_delete.html'
    success_url = reverse_lazy('store_list')