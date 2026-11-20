import base64
import ipaddress

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from django.conf import settings
from django.core.exceptions import ValidationError

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


# Reti che una LAN di router non può mai coprire: la VPN stessa, l'hub FBOAIGate
# (wg1) e la rete pubblica del VPS. Tenere allineato con deploy/mkremote-wg-peer.sh.
RESERVED_LAN_NETWORKS = ('10.10.0.0/24', '10.20.0.0/24', '94.177.161.0/24')


def validate_lan_subnet(value: str, exclude_pk=None) -> str:
    """Valida e normalizza la subnet LAN di un router (CIDR IPv4 privato).

    Restituisce '' se vuota. Rifiuta reti non private, troppo ampie (< /16) o
    troppo strette (> /30), sovrapposte a reti riservate o a quella già
    dichiarata da un altro router: WireGuard non può instradare la stessa
    rete verso due peer, il secondo sovrascriverebbe silenziosamente il primo."""
    value = (value or '').strip()
    if not value:
        return ''
    try:
        net = ipaddress.ip_network(value, strict=True)
    except ValueError:
        raise ValidationError(
            'Subnet non valida: usa la notazione CIDR con indirizzo di rete, es. 10.0.0.0/24.'
        )
    if net.version != 4 or not net.is_private:
        raise ValidationError('La subnet LAN deve essere una rete IPv4 privata.')
    if not 16 <= net.prefixlen <= 30:
        raise ValidationError('La subnet LAN deve avere prefisso tra /16 e /30.')
    for reserved in RESERVED_LAN_NETWORKS + (settings.VPN_SUBNET_CIDR,):
        if net.overlaps(ipaddress.ip_network(reserved)):
            raise ValidationError(f'La subnet si sovrappone a una rete riservata ({reserved}).')
    others = Router.objects.exclude(subnet_lan='')
    if exclude_pk is not None:
        others = others.exclude(pk=exclude_pk)
    for other in others:
        if net.overlaps(ipaddress.ip_network(other.subnet_lan)):
            raise ValidationError(
                f'La subnet si sovrappone a quella del router "{other.nome}" ({other.subnet_lan}): '
                f'una rete può essere raggiunta tramite un solo router.'
            )
    return str(net)


def personal_client_lan_subnets() -> list[str]:
    """Subnet LAN dei router da aggiungere agli AllowedIPs dei dispositivi personali."""
    return list(
        Router.objects.exclude(subnet_lan='').order_by('subnet_lan').values_list('subnet_lan', flat=True)
    )
