from django.db import models

from routers.models import Router


class RouterMetric(models.Model):
    """Singolo campionamento di polling per un router (Fase 5)."""

    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='metriche')

    cpu_load_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    ram_usata_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    ram_totale_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    uptime_secondi = models.PositiveBigIntegerField(null=True, blank=True)
    temperatura_celsius = models.SmallIntegerField(null=True, blank=True)

    # Contatori traffico per interfaccia, es. {"ether1": {"rx_bytes": ..., "tx_bytes": ...}}.
    # Schema JSON perché il set di interfacce varia da router a router.
    traffico_interfacce = models.JSONField(default=dict, blank=True)

    rilevato_il = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-rilevato_il']
        indexes = [
            models.Index(fields=['router', '-rilevato_il']),
        ]

    def __str__(self):
        return f'{self.router.nome} — {self.rilevato_il:%Y-%m-%d %H:%M:%S}'


class AlertEvent(models.Model):
    class Tipo(models.TextChoices):
        OFFLINE = 'offline', 'Router offline'
        CPU_ALTA = 'cpu_alta', 'CPU sopra soglia'
        TEMPERATURA_ALTA = 'temperatura_alta', 'Temperatura sopra soglia'
        BACKUP_FALLITO = 'backup_fallito', 'Backup fallito'

    class Stato(models.TextChoices):
        APERTO = 'aperto', 'Aperto'
        CHIUSO = 'chiuso', 'Chiuso'

    router = models.ForeignKey(Router, on_delete=models.CASCADE, related_name='alert')
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    stato = models.CharField(max_length=10, choices=Stato.choices, default=Stato.APERTO)
    messaggio = models.CharField(max_length=500, blank=True)

    aperto_il = models.DateTimeField(auto_now_add=True)
    chiuso_il = models.DateTimeField(null=True, blank=True)
    ultima_notifica_il = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-aperto_il']
        indexes = [
            models.Index(fields=['router', 'tipo', 'stato']),
        ]

    def __str__(self):
        return f'{self.router.nome} — {self.get_tipo_display()} — {self.get_stato_display()}'


class AlertSettings(models.Model):
    """Impostazioni globali di alerting. Singleton (una sola riga, pk=1)."""

    soglia_cpu_percent = models.PositiveSmallIntegerField(default=90)
    soglia_temperatura_celsius = models.SmallIntegerField(default=70)
    fallimenti_consecutivi_per_offline = models.PositiveSmallIntegerField(default=3)
    cooldown_minuti = models.PositiveIntegerField(
        default=60,
        help_text='Tempo minimo tra due notifiche ripetute dello stesso alert ancora aperto.',
    )

    telegram_abilitato = models.BooleanField(default=False)
    telegram_chat_id = models.CharField(max_length=100, blank=True)

    email_abilitata = models.BooleanField(default=False)
    email_destinatario = models.EmailField(blank=True)

    modificato_il = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Impostazioni alert'
        verbose_name_plural = 'Impostazioni alert'

    def __str__(self):
        return 'Impostazioni alert'

    @classmethod
    def get_solo(cls) -> 'AlertSettings':
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
