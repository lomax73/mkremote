from django.db import models

from routers.models import Router


class BackupRun(models.Model):
    """Un'esecuzione del task di backup (manuale o pianificata) per un
    router — copre entrambi i tipi (binario + export). Il log viene
    aggiornato passo passo mentre il task procede, così si può seguire
    dal vivo cosa succede (utile quando un backup fallisce e non è
    chiaro perché)."""

    class Stato(models.TextChoices):
        IN_CORSO = 'in_corso', 'In corso'
        COMPLETATO = 'completato', 'Completato'

    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='backup_run')
    stato = models.CharField(max_length=12, choices=Stato.choices, default=Stato.IN_CORSO)
    log = models.TextField(blank=True, default='')

    avviato_il = models.DateTimeField(auto_now_add=True)
    concluso_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-avviato_il']

    def __str__(self):
        return f'Run backup {self.router.nome} — {self.avviato_il:%Y-%m-%d %H:%M}'


class Backup(models.Model):
    class Tipo(models.TextChoices):
        BINARIO = 'binario', 'Backup binario (.backup)'
        EXPORT = 'export', 'Export testuale (.rsc)'

    class Esito(models.TextChoices):
        RIUSCITO = 'riuscito', 'Riuscito'
        FALLITO = 'fallito', 'Fallito'

    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='backups')
    run = models.ForeignKey(BackupRun, on_delete=models.SET_NULL, null=True, blank=True, related_name='backups')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    esito = models.CharField(max_length=20, choices=Esito.choices)

    storage_path = models.CharField(max_length=500, blank=True)
    dimensione_bytes = models.PositiveBigIntegerField(null=True, blank=True)

    errore = models.TextField(blank=True)

    creato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creato_il']

    def __str__(self):
        return f'{self.router.nome} — {self.tipo} — {self.creato_il:%Y-%m-%d %H:%M}'
