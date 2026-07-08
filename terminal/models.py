from django.conf import settings
from django.db import models

from routers.models import Router


class SessioneTerminale(models.Model):
    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='sessioni_terminale')
    utente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    aperta_il = models.DateTimeField(auto_now_add=True)
    chiusa_il = models.DateTimeField(null=True, blank=True)
    errore = models.TextField(blank=True)

    class Meta:
        ordering = ['-aperta_il']

    def __str__(self):
        return f'{self.utente} su {self.router.nome} — {self.aperta_il:%Y-%m-%d %H:%M}'
