import librouteros


class RouterProbeError(Exception):
    """Sollevata quando non è possibile interrogare il router via API RouterOS."""


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
