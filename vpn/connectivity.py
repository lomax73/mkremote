import librouteros
from routers.models import Router
from routers.services import RouterProbeError, probe_router


def test_router_vpn_connection(router: Router, timeout: float = 5.0) -> bool:
    """Prova una chiamata API minimale sull'IP VPN del router e aggiorna
    stato_connessione di conseguenza. Ritorna True se raggiungibile.
    """
    if not router.ip_vpn:
        router.stato_connessione = Router.StatoConnessione.IN_ATTESA_VPN
        router.save(update_fields=['stato_connessione'])
        return False

    try:
        api = librouteros.connect(
            host=router.ip_vpn,
            username=router.username,
            password=router.password,
            port=router.porta_api,
            timeout=timeout,
        )
        try:
            tuple(api.path('/system/identity').select('name'))
        finally:
            api.close()
    except Exception:
        router.stato_connessione = Router.StatoConnessione.OFFLINE
        router.save(update_fields=['stato_connessione'])
        return False

    router.stato_connessione = Router.StatoConnessione.CONNESSO
    router.save(update_fields=['stato_connessione'])
    return True


def fetch_router_hardware_info(router: Router, timeout: float = 5.0) -> dict:
    """Si collega al router sul suo IP VPN e ne legge modello hardware e versione firmware,
    aggiornandoli sul record. Richiede che il tunnel VPN sia già configurato: serve anche da
    test di connettività, aggiornando stato_connessione come test_router_vpn_connection.
    """
    if not router.ip_vpn:
        raise RouterProbeError(
            'Il router non ha ancora un IP VPN assegnato: completa prima il collegamento VPN.'
        )

    try:
        info = probe_router(
            host=router.ip_vpn, port=router.porta_api,
            username=router.username, password=router.password, timeout=timeout,
        )
    except RouterProbeError:
        router.stato_connessione = Router.StatoConnessione.OFFLINE
        router.save(update_fields=['stato_connessione'])
        raise

    router.modello_hardware = info['modello_hardware']
    router.versione_routeros = info['versione_routeros']
    router.stato_connessione = Router.StatoConnessione.CONNESSO
    router.save(update_fields=['modello_hardware', 'versione_routeros', 'stato_connessione'])
    return info
