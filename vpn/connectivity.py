import librouteros
from routers.models import Router


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
