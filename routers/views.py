from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import RouterForm
from .models import Router


class RouterListView(LoginRequiredMixin, ListView):
    model = Router
    template_name = 'routers/router_list.html'
    context_object_name = 'routers'


class RouterDetailView(LoginRequiredMixin, DetailView):
    model = Router
    template_name = 'routers/router_detail.html'
    context_object_name = 'router'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from backups.models import Backup
        context['ultimo_backup'] = Backup.objects.filter(router=self.object).first()
        return context


class RouterCreateView(LoginRequiredMixin, CreateView):
    model = Router
    form_class = RouterForm
    template_name = 'routers/router_form.html'
    success_url = reverse_lazy('router-list')


class RouterUpdateView(LoginRequiredMixin, UpdateView):
    model = Router
    form_class = RouterForm
    template_name = 'routers/router_form.html'

    def get_success_url(self):
        return reverse_lazy('router-detail', kwargs={'pk': self.object.pk})


class RouterDeleteView(LoginRequiredMixin, DeleteView):
    model = Router
    template_name = 'routers/router_confirm_delete.html'
    success_url = reverse_lazy('router-list')


class RouterRevealPasswordView(LoginRequiredMixin, View):
    """Decifra e restituisce la password salvata di un router, per recuperarla se dimenticata."""

    def post(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        return JsonResponse({'password': router.password})
