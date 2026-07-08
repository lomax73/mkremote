from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from routers.models import Router

from .forms import AlertSettingsForm
from .models import AlertEvent, AlertSettings, RouterMetric


class DashboardView(LoginRequiredMixin, ListView):
    model = Router
    template_name = 'monitoring/dashboard.html'
    context_object_name = 'routers'

    def get_queryset(self):
        return Router.objects.prefetch_related('metriche').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for router in context['routers']:
            router.ultima_metrica = router.metriche.first()
        context['alert_aperti'] = AlertEvent.objects.filter(stato=AlertEvent.Stato.APERTO).select_related('router')
        return context


class RouterMonitorDetailView(LoginRequiredMixin, DetailView):
    model = Router
    template_name = 'monitoring/router_detail.html'
    context_object_name = 'router'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['alert_router'] = self.object.alert.all()[:20]
        return context


class RouterMetricsDataView(LoginRequiredMixin, View):
    """Endpoint JSON per alimentare i grafici Chart.js senza ricaricare la pagina."""

    def get(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        metriche = router.metriche.order_by('rilevato_il')[:500]
        return JsonResponse({
            'labels': [m.rilevato_il.isoformat() for m in metriche],
            'cpu': [m.cpu_load_percent for m in metriche],
            'ram_usata': [m.ram_usata_bytes for m in metriche],
            'ram_totale': [m.ram_totale_bytes for m in metriche],
            'temperatura': [m.temperatura_celsius for m in metriche],
        })


class AlertSettingsView(LoginRequiredMixin, View):
    template_name = 'monitoring/alert_settings.html'

    def get(self, request):
        form = AlertSettingsForm(instance=AlertSettings.get_solo())
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AlertSettingsForm(request.POST, instance=AlertSettings.get_solo())
        if form.is_valid():
            form.save()
            messages.success(request, 'Impostazioni di alert aggiornate.')
            return redirect('monitoring-settings')
        return render(request, self.template_name, {'form': form})
