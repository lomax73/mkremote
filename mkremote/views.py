import markdown
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class HelpView(LoginRequiredMixin, TemplateView):
    template_name = 'help.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        guida_path = settings.BASE_DIR / 'docs' / 'guida_utente.md'
        testo = guida_path.read_text(encoding='utf-8')
        context['guida_html'] = markdown.markdown(testo, extensions=['tables', 'fenced_code'])
        return context
