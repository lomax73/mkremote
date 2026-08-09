import re

import librouteros
from django.conf import settings


class RouterProbeError(Exception):
    """Sollevata quando non è possibile interrogare il router via API RouterOS."""


_VERSION_RE = re.compile(r'(\d+)\.(\d+)(?:\.(\d+))?')


def _parse_versione(versione_str: str) -> tuple[int, int, int] | None:
    if not versione_str:
        return None
    match = _VERSION_RE.search(versione_str)
    if not match:
        return None
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch or 0)


def stato_aggiornamento_routeros(versione_str: str) -> str:
    """Confronta la versione RouterOS di un router con l'ultima stabile nota
    (ROUTEROS_LATEST_STABLE in settings, da aggiornare a mano quando esce una
    nuova release — MikroTik non espone un endpoint pubblico documentato/stabile
    per interrogarla in automatico). Ritorna 'aggiornato', 'leggero_ritardo',
    'molto_indietro' o 'sconosciuto' (versione non rilevata o non confrontabile)."""
    attuale = _parse_versione(versione_str)
    ultima = _parse_versione(getattr(settings, 'ROUTEROS_LATEST_STABLE', ''))
    if attuale is None or ultima is None:
        return 'sconosciuto'

    if attuale >= ultima:
        return 'aggiornato'

    major_att, minor_att, _ = attuale
    major_ult, minor_ult, _ = ultima
    if major_att < major_ult:
        return 'molto_indietro'

    deficit_minor = minor_ult - minor_att
    if deficit_minor <= 1:
        return 'leggero_ritardo'
    return 'molto_indietro'


def probe_router(*, host: str, port: int, username: str, password: str, timeout: float = 5.0) -> dict:
    """Si connette al router via API RouterOS e ne legge modello hardware e versione firmware.

    Serve anche da test di connettività: se la connessione riesce, l'host/porta/credenziali
    inseriti nel form sono corretti.
    """
    try:
        api = librouteros.connect(
            host=host, username=username, password=password, port=port, timeout=timeout,
        )
    except Exception as exc:
        raise RouterProbeError(str(exc)) from exc

    try:
        resource = next(iter(api.path('/system/resource')), {})
    finally:
        api.close()

    return {
        'modello_hardware': resource.get('board-name', ''),
        'versione_routeros': resource.get('version', ''),
    }
