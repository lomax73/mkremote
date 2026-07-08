from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from routers.models import Router

from .models import Backup
from .storage import ObjectStorageNotConfigured, download_backup_file
from .tasks import backup_router_task


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
        return context


class BackupNowView(LoginRequiredMixin, View):
    def post(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        backup_router_task.delay(router.pk)
        messages.success(request, 'Backup manuale avviato: controlla lo storico tra qualche istante.')
        return redirect('backup-list', pk=router.pk)


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
