import base64
import ipaddress

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from django.conf import settings

from routers.models import Router

from .models import PersonalVpnDevice


class VpnSubnetExhausted(Exception):
    pass


def generate_wireguard_keypair() -> tuple[str, str]:
    """Genera una coppia di chiavi WireGuard (Curve25519/X25519), restituendo
    (chiave_privata_b64, chiave_pubblica_b64).

    Il clamping richiesto da RFC 7748 viene applicato dalla funzione X25519 al
    momento dell'uso (derivazione della chiave pubblica, scambio Diffie-Hellman),
    non allo storage della chiave privata: 32 byte casuali sono quindi un input
    valido, esattamente come genera `wg genkey` — nessun bisogno del binario wg
    lato server applicativo (installato solo sul VPS hub)."""
    private_key = X25519PrivateKey.generate()
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(priv_bytes).decode(), base64.b64encode(pub_bytes).decode()


def assign_personal_vpn_ip() -> str:
    """Assegna il prossimo IP libero nella fascia riservata ai dispositivi
    personali (Fase 0), escludendo sia gli IP dei router sia quelli già in uso
    da altri dispositivi personali ancora attivi (non revocati)."""
    used_ips = set(
        Router.objects.exclude(ip_vpn__isnull=True).values_list('ip_vpn', flat=True)
    ) | set(
        PersonalVpnDevice.objects.filter(revocato_il__isnull=True).values_list('ip_vpn', flat=True)
    )

    start = ipaddress.ip_address(settings.VPN_PERSONAL_IP_RANGE_START)
    end = ipaddress.ip_address(settings.VPN_PERSONAL_IP_RANGE_END)

    current = start
    while current <= end:
        ip_str = str(current)
        if ip_str not in used_ips:
            return ip_str
        current += 1

    raise VpnSubnetExhausted(
        f"Nessun IP libero per dispositivi personali tra {start} e {end}."
    )


def assign_vpn_ip(router: Router) -> str:
    """Assegna il prossimo IP libero della subnet VPN al router, se non ne ha già uno.

    Idempotente: se il router ha già un ip_vpn, lo restituisce senza cambiarlo
    (rigenerare lo script VPN non deve mai riassegnare un IP diverso).
    """
    if router.ip_vpn:
        return router.ip_vpn

    used_ips = set(
        Router.objects.exclude(pk=router.pk)
        .exclude(ip_vpn__isnull=True)
        .values_list('ip_vpn', flat=True)
    )

    network = ipaddress.ip_network(settings.VPN_SUBNET_CIDR)
    start = ipaddress.ip_address(settings.VPN_ROUTER_IP_RANGE_START)

    for host in network.hosts():
        if host < start:
            continue
        ip_str = str(host)
        if ip_str not in used_ips:
            router.ip_vpn = ip_str
            router.save(update_fields=['ip_vpn'])
            return ip_str

    raise VpnSubnetExhausted(
        f"Nessun IP libero nella subnet {settings.VPN_SUBNET_CIDR} "
        f"a partire da {settings.VPN_ROUTER_IP_RANGE_START}."
    )
