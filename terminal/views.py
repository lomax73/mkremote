from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from accounts.mixins import SuperuserRequiredMixin
from routers.models import Router


class TerminalView(LoginRequiredMixin, SuperuserRequiredMixin, DetailView):
    model = Router
    template_name = 'terminal/terminal.html'
    context_object_name = 'router'
