import re

import librouteros
from celery import shared_task

from routers.models import Router

from .models import AlertEvent, AlertSettings, RouterMetric
from .notifications import close_alert, open_or_get_alert

_UPTIME_RE = re.compile(r'(\d+)([wdhms])')
_UPTIME_UNIT_SECONDS = {'w': 7 * 24 * 3600, 'd': 24 * 3600, 'h': 3600, 'm': 60, 's': 1}


def _parse_uptime(uptime: str) -> int | None:
    """RouterOS ritorna l'uptime come stringa tipo '1w2d3h4m5s'."""
    if not uptime:
        return None
    return sum(int(n) * _UPTIME_UNIT_SECONDS[u] for n, u in _UPTIME_RE.findall(uptime))


def _collect_metric(router: Router) -> RouterMetric:
    api = librouteros.connect(
        host=router.ip_vpn,
        username=router.username,
        password=router.password,
        port=router.porta_api,
    )
    try:
        resource = next(iter(api.path('/system/resource')), {})

        temperatura = None
        try:
            for entry in api.path('/system/health'):
                if entry.get('name') == 'temperature':
                    temperatura = int(float(entry['value']))
                    break
        except Exception:
            pass  # non tutti i modelli hanno sensori di health

        traffico = {}
        for iface in api.path('/interface'):
            if 'rx-byte' not in iface and 'tx-byte' not in iface:
                continue
            traffico[iface.get('name', '?')] = {
                'rx_bytes': iface.get('rx-byte'),
                'tx_bytes': iface.get('tx-byte'),
            }

        ram_totale = resource.get('total-memory')
        ram_libera = resource.get('free-memory')
        ram_usata = (ram_totale - ram_libera) if ram_totale is not None and ram_libera is not None else None

        return RouterMetric(
            router=router,
            cpu_load_percent=resource.get('cpu-load'),
            ram_usata_bytes=ram_usata,
            ram_totale_bytes=ram_totale,
            uptime_secondi=_parse_uptime(resource.get('uptime', '')),
            temperatura_celsius=temperatura,
            traffico_interfacce=traffico,
        )
    finally:
        api.close()


def _handle_success(router: Router, metric: RouterMetric, alert_settings: AlertSettings) -> None:
    metric.save()

    if router.fallimenti_polling_consecutivi > 0 or router.stato_connessione == Router.StatoConnessione.OFFLINE:
        router.fallimenti_polling_consecutivi = 0
        router.stato_connessione = Router.StatoConnessione.CONNESSO
        router.save(update_fields=['fallimenti_polling_consecutivi', 'stato_connessione'])
        close_alert(router, AlertEvent.Tipo.OFFLINE)

    if metric.cpu_load_percent is not None and metric.cpu_load_percent >= alert_settings.soglia_cpu_percent:
        open_or_get_alert(
            router, AlertEvent.Tipo.CPU_ALTA,
            f'CPU al {metric.cpu_load_percent}% (soglia {alert_settings.soglia_cpu_percent}%)',
        )
    else:
        close_alert(router, AlertEvent.Tipo.CPU_ALTA)

    if metric.temperatura_celsius is not None and metric.temperatura_celsius >= alert_settings.soglia_temperatura_celsius:
        open_or_get_alert(
            router, AlertEvent.Tipo.TEMPERATURA_ALTA,
            f'Temperatura a {metric.temperatura_celsius}°C (soglia {alert_settings.soglia_temperatura_celsius}°C)',
        )
    else:
        close_alert(router, AlertEvent.Tipo.TEMPERATURA_ALTA)


def _handle_failure(router: Router, alert_settings: AlertSettings, errore: str) -> None:
    router.fallimenti_polling_consecutivi += 1
    update_fields = ['fallimenti_polling_consecutivi']

    if router.fallimenti_polling_consecutivi >= alert_settings.fallimenti_consecutivi_per_offline:
        if router.stato_connessione != Router.StatoConnessione.OFFLINE:
            router.stato_connessione = Router.StatoConnessione.OFFLINE
            update_fields.append('stato_connessione')
        open_or_get_alert(router, AlertEvent.Tipo.OFFLINE, f'Router irraggiungibile: {errore}')

    router.save(update_fields=update_fields)


def _poll_one(router: Router, alert_settings: AlertSettings) -> None:
    try:
        metric = _collect_metric(router)
    except Exception as exc:
        _handle_failure(router, alert_settings, str(exc))
    else:
        _handle_success(router, metric, alert_settings)


@shared_task
def poll_routers_task() -> None:
    alert_settings = AlertSettings.get_solo()
    routers = Router.objects.exclude(ip_vpn__isnull=True).exclude(
        stato_connessione=Router.StatoConnessione.NON_CONFIGURATO,
    )
    for router in routers:
        _poll_one(router, alert_settings)


@shared_task
def ping_task():
    return 'pong'
