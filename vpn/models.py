from django.conf import settings
from django.db import models


class PersonalVpnDevice(models.Model):
    """Peer WireGuard 'umano' (Fase 7): laptop, telefono, ecc. La chiave privata
    è generata lato server ma non viene mai salvata qui — solo la pubblica,
    che è quella che serve al VPS hub per riconoscere il peer."""

    utente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dispositivi_vpn')
    nome = models.CharField(max_length=100)
    chiave_pubblica = models.CharField(max_length=44, unique=True)
    ip_vpn = models.GenericIPAddressField(protocol='IPv4')

    creato_il = models.DateTimeField(auto_now_add=True)
    revocato_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creato_il']

    def __str__(self):
        return f'{self.nome} ({self.utente})'

    @property
    def attivo(self) -> bool:
        return self.revocato_il is None
