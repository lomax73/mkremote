from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import RouterForm
from .models import Router
from .services import RouterProbeError, probe_router


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


class RouterProbeView(LoginRequiredMixin, View):
    """Interroga il router via API RouterOS con i dati non ancora salvati del form:
    serve sia come test di connessione sia per compilare automaticamente modello e firmware.
    """

    def post(self, request):
        host = request.POST.get('ip_lan', '').strip() or request.POST.get('ip_pubblico_o_ddns', '').strip()
        if not host:
            return JsonResponse({'ok': False, 'error': "Inserisci l'IP LAN o l'IP pubblico del router."})

        try:
            porta_api = int(request.POST.get('porta_api') or 8728)
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'Porta API non valida.'})

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        if not username or not password:
            return JsonResponse({'ok': False, 'error': 'Inserisci username e password per interrogare il router.'})

        try:
            info = probe_router(host=host, port=porta_api, username=username, password=password)
        except RouterProbeError as exc:
            return JsonResponse({'ok': False, 'error': f'Connessione fallita: {exc}'})

        return JsonResponse({'ok': True, **info})
