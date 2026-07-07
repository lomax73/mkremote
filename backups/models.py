from django.db import models

from routers.models import Router


class Backup(models.Model):
    class Tipo(models.TextChoices):
        BINARIO = 'binario', 'Backup binario (.backup)'
        EXPORT = 'export', 'Export testuale (.rsc)'

    class Esito(models.TextChoices):
        RIUSCITO = 'riuscito', 'Riuscito'
        FALLITO = 'fallito', 'Fallito'

    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='backups')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    esito = models.CharField(max_length=20, choices=Esito.choices)

    s3_key = models.CharField(max_length=500, blank=True)
    dimensione_bytes = models.PositiveBigIntegerField(null=True, blank=True)

    errore = models.TextField(blank=True)

    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creato_il']

    def __str__(self):
        return f'{self.router.nome} — {self.tipo} — {self.creato_il:%Y-%m-%d %H:%M}'
