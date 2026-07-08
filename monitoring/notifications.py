from datetime import timedelta

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import AlertEvent, AlertSettings


def _send_telegram(message: str, alert_settings: AlertSettings) -> None:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or not alert_settings.telegram_chat_id:
        return
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    requests.post(
        url,
        data={'chat_id': alert_settings.telegram_chat_id, 'text': message},
        timeout=10,
    )


def _send_email(message: str, alert_settings: AlertSettings) -> None:
    if not alert_settings.email_destinatario:
        return
    send_mail(
        subject='MKRemote — Alert router',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[alert_settings.email_destinatario],
        fail_silently=True,
    )


def _should_notify(alert: AlertEvent, alert_settings: AlertSettings, appena_creato: bool) -> bool:
    """Anti-spam: notifica sempre alla creazione/cambio di stato; altrimenti solo
    se è passato almeno `cooldown_minuti` dall'ultima notifica per lo stesso alert."""
    if appena_creato:
        return True
    if alert.ultima_notifica_il is None:
        return True
    cooldown = timedelta(minutes=alert_settings.cooldown_minuti)
    return timezone.now() - alert.ultima_notifica_il >= cooldown


def notify_alert(alert: AlertEvent, appena_creato: bool) -> None:
    alert_settings = AlertSettings.get_solo()
    if not _should_notify(alert, alert_settings, appena_creato):
        return

    messaggio = f'[MKRemote] {alert.router.nome}: {alert.get_tipo_display()} — {alert.messaggio}'

    if alert_settings.telegram_abilitato:
        _send_telegram(messaggio, alert_settings)
    if alert_settings.email_abilitata:
        _send_email(messaggio, alert_settings)

    alert.ultima_notifica_il = timezone.now()
    alert.save(update_fields=['ultima_notifica_il'])


def open_or_get_alert(router, tipo: str, messaggio: str) -> None:
    """Apre un nuovo AlertEvent per (router, tipo) se non ce n'è già uno aperto,
    altrimenti lo lascia com'è (l'anti-spam decide se rinotificare)."""
    alert, creato = AlertEvent.objects.get_or_create(
        router=router, tipo=tipo, stato=AlertEvent.Stato.APERTO,
        defaults={'messaggio': messaggio},
    )
    notify_alert(alert, appena_creato=creato)


def close_alert(router, tipo: str) -> None:
    AlertEvent.objects.filter(
        router=router, tipo=tipo, stato=AlertEvent.Stato.APERTO,
    ).update(stato=AlertEvent.Stato.CHIUSO, chiuso_il=timezone.now())
