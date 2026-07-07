from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from routers.models import Router

from .models import Backup
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
