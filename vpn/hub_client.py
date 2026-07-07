import asyncio
import shlex

import asyncssh
from django.conf import settings


class VpsNotConfigured(Exception):
    """Manca la configurazione di accesso SSH al VPS (vedi fase_8: VPS non ancora provisionato)."""


class VpsCommandFailed(Exception):
    pass


def _require_vps_config():
    if not settings.VPS_SSH_HOST or not settings.VPS_SSH_PRIVATE_KEY_PATH:
        raise VpsNotConfigured(
            'Accesso SSH al VPS non configurato (VPS_SSH_HOST / '
            'VPS_SSH_PRIVATE_KEY_PATH mancanti in .env).'
        )


async def _register_peer(peer_public_key: str, peer_vpn_ip: str) -> None:
    iface = settings.VPN_WG_INTERFACE
    conf_path = settings.VPN_WG_CONF_PATH

    # 1) wg set: aggiunge il peer a runtime, nessun downtime per i peer esistenti.
    # 2) wg showconf: cattura lo stato corrente dell'interfaccia (compreso il nuovo
    #    peer) e lo scrive come nuova config persistente su disco.
    # 3) wg syncconf: riconcilia l'interfaccia con quella config (no-op perché è la
    #    stessa già applicata), garantendo che runtime e file su disco restino
    #    coerenti per il prossimo riavvio del servizio.
    remote_command = (
        f"wg set {shlex.quote(iface)} peer {shlex.quote(peer_public_key)} "
        f"allowed-ips {shlex.quote(peer_vpn_ip)}/32 && "
        f"wg showconf {shlex.quote(iface)} > {shlex.quote(conf_path)} && "
        f"wg syncconf {shlex.quote(iface)} {shlex.quote(conf_path)}"
    )

    async with asyncssh.connect(
        settings.VPS_SSH_HOST,
        port=settings.VPS_SSH_PORT,
        username=settings.VPS_SSH_USER,
        client_keys=[settings.VPS_SSH_PRIVATE_KEY_PATH],
        known_hosts=None,
    ) as conn:
        result = await conn.run(remote_command, check=False)
        if result.exit_status != 0:
            raise VpsCommandFailed(
                f'Comando fallito sul VPS (exit {result.exit_status}): {result.stderr}'
            )


def register_peer_on_hub(peer_public_key: str, peer_vpn_ip: str) -> None:
    """Registra la chiave pubblica del router come peer WireGuard sul VPS hub.

    Solleva VpsNotConfigured se il VPS non è ancora raggiungibile/configurato
    (stato attuale del progetto, vedi fase_8), o VpsCommandFailed se il comando
    remoto fallisce.
    """
    _require_vps_config()
    asyncio.run(_register_peer(peer_public_key, peer_vpn_ip))
