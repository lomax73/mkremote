from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from routers.models import Router

from .models import Backup, BackupRun
from .storage import ObjectStorageNotConfigured, download_backup_file
from .tasks import backup_router_task


class BackupOverviewView(LoginRequiredMixin, ListView):
    """Elenco router con link diretto ai backup di ciascuno, raggiungibile
    dalla sidebar — la pagina backup vera e propria è per singolo router."""
    model = Router
    template_name = 'backups/backup_overview.html'
    context_object_name = 'routers'

    def get_queryset(self):
        return Router.objects.all().order_by('nome')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for router in context['routers']:
            router.ultimo_backup = router.backups.order_by('-creato_il').first()
        return context


class BackupListView(LoginRequiredMixin, ListView):
    model = Backup
    template_name = 'backups/backup_list.html'
    context_object_name = 'backups'

    def get_queryset(self):
        self.router = get_object_or_404(Router, pk=self.kwargs['pk'])
        return Backup.objects.filter(router=self.router)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['router'] = self.router
        context['run_recenti'] = self.router.backup_run.all()[:10]
        return context


class BackupNowView(LoginRequiredMixin, View):
    def post(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        run = BackupRun.objects.create(router=router)
        backup_router_task.delay(router.pk, run.pk)
        return redirect('backup-run-detail', pk=router.pk, run_id=run.pk)


class BackupRunDetailView(LoginRequiredMixin, DetailView):
    model = BackupRun
    pk_url_kwarg = 'run_id'
    template_name = 'backups/backup_run_detail.html'
    context_object_name = 'run'

    def get_queryset(self):
        return BackupRun.objects.filter(router_id=self.kwargs['pk'])


class BackupRunStatusView(LoginRequiredMixin, View):
    """Endpoint JSON per il polling dal vivo della pagina di log."""
    def get(self, request, pk, run_id):
        run = get_object_or_404(BackupRun, pk=run_id, router_id=pk)
        return JsonResponse({'stato': run.stato, 'log': run.log})


class BackupDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk, backup_id):
        backup = get_object_or_404(Backup, pk=backup_id, router_id=pk)
        if not backup.storage_path:
            messages.error(request, 'Questo backup non ha un file associato (esito fallito).')
            return redirect('backup-list', pk=pk)
        try:
            content = download_backup_file(backup.storage_path)
        except ObjectStorageNotConfigured as exc:
            messages.error(request, str(exc))
            return redirect('backup-list', pk=pk)
        filename = backup.storage_path.rsplit('/', 1)[-1]
        response = HttpResponse(content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
