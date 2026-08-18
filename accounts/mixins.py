from django.contrib.auth.mixins import UserPassesTestMixin


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Terminale, credenziali in chiaro e generazione script VPN/firewall
    danno accesso completo a router di clienti reali: oltre al login,
    richiede esplicitamente is_superuser (non c'è ancora un modello di
    permessi per-router, vedi RedFlag id 95)."""

    def test_func(self):
        return self.request.user.is_superuser
