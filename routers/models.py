from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from .fields import EncryptedCharField

# router.nome finisce dentro una riga di commento `#` degli script RouterOS
# generati da vpn/scripts.py: un newline non filtrato farebbe terminare il
# commento a metà riga, trasformando quella successiva in un comando
# RouterOS vero e proprio quando l'operatore incolla lo script sul router
# (RedFlag id 96). vpn/scripts.py sanitizza comunque il valore all'uso, ma
# vietarlo già qui evita che un nome "sporco" venga salvato.
_nome_senza_newline = RegexValidator(
    regex=r'^[^\r\n]*$', message='Il nome non può contenere andare a capo.',
)


class Router(models.Model):
    class StatoConnessione(models.TextChoices):
        NON_CONFIGURATO = 'non_configurato', 'Non configurato'
        IN_ATTESA_VPN = 'in_attesa_vpn', 'In attesa VPN'
        CONNESSO = 'connesso', 'Connesso'
        OFFLINE = 'offline', 'Offline'

    nome = models.CharField(max_length=100, unique=True, validators=[_nome_senza_newline])
    location = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)
    cliente_id = models.UUIDField(
        'ID cliente', null=True, blank=True,
        help_text="Riferimento all'anagrafica clienti condivisa del Portale, per raggruppare i router.",
    )

    modello_hardware = models.CharField(max_length=100, blank=True)
    versione_routeros = models.CharField(max_length=50, blank=True)

    ip_pubblico_o_ddns = models.CharField(max_length=255, blank=True)
    ip_lan = models.GenericIPAddressField(
        protocol='IPv4', null=True, blank=True,
        help_text='IP del router nella rete locale, utile per test diretti prima di configurare la VPN.',
    )
    porta_ssh = models.PositiveIntegerField(
        default=22, validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )
    porta_api = models.PositiveIntegerField(
        default=8728, validators=[MinValueValidator(1), MaxValueValidator(65535)]
    )

    username = EncryptedCharField()
    password = EncryptedCharField()

    ip_vpn = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    chiave_pubblica_wireguard = models.CharField(max_length=100, blank=True)

    stato_connessione = models.CharField(
        max_length=20,
        choices=StatoConnessione.choices,
        default=StatoConnessione.NON_CONFIGURATO,
    )

    intervallo_backup = models.DurationField(
        null=True,
        blank=True,
        help_text='Intervallo tra un backup automatico e il successivo (usato dalla Fase 4).',
    )
    backup_retention_count = models.PositiveIntegerField(
        default=10,
        help_text='Numero di backup più recenti da conservare per questo router; i più vecchi vengono eliminati.',
    )

    accesso_pubblico_bloccato = models.BooleanField(default=False)

    fallimenti_polling_consecutivi = models.PositiveSmallIntegerField(
        default=0,
        help_text='Contatore di polling falliti di fila (Fase 5); azzerato al primo successo.',
    )

    creato_il = models.DateTimeField(auto_now_add=True)
    modificato_il = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def intervallo_backup_giorni(self):
        """Intervallo di backup espresso in giorni interi, per un form più intuitivo del
        formato durata di Django (es. '1 00:00:00')."""
        if not self.intervallo_backup:
            return None
        return round(self.intervallo_backup.total_seconds() / 86400)
