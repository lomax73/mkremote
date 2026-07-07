import ipaddress

from django.conf import settings


class VpnHubNotConfigured(Exception):
    """Il VPS hub non è ancora provisionato (endpoint/chiave pubblica mancanti)."""


def generate_wireguard_setup_script(router) -> str:
    """Genera lo script RouterOS (.rsc) da incollare sul router per attivare il
    tunnel WireGuard verso il VPS hub.

    La chiave privata del router non lascia mai il router: viene generata
    localmente dallo script stesso. Solo la chiave pubblica, stampata a schermo,
    torna manualmente all'app (campo "Registra peer sul server").
    """
    if not settings.VPN_HUB_PUBLIC_ENDPOINT or not settings.VPN_HUB_PUBLIC_KEY:
        raise VpnHubNotConfigured(
            'Il VPS hub non è ancora configurato (VPN_HUB_PUBLIC_ENDPOINT / '
            'VPN_HUB_PUBLIC_KEY mancanti in .env). Vedi fase_8 per lo stato.'
        )

    if not router.ip_vpn:
        raise ValueError('Il router non ha ancora un ip_vpn assegnato.')

    prefixlen = ipaddress.ip_network(settings.VPN_SUBNET_CIDR).prefixlen

    return f"""\
# === MKRemote - Setup tunnel WireGuard verso il VPS hub ===
# Router: {router.nome}
# Da eseguire in un terminale RouterOS (WinBox o SSH). Non tocca il firewall:
# il blocco dell'accesso pubblico si fa solo dopo aver verificato il tunnel
# (vedi Fase 3), da un'altra sessione con accesso di riserva aperta.

# Crea l'interfaccia WireGuard e genera la coppia di chiavi direttamente qui:
# la chiave privata resta sul router, non viene mai trasmessa altrove.
/interface wireguard add name=wireguard1 listen-port=51820 comment="MKRemote hub tunnel"

# Assegna l'IP privato riservato a questo router nella subnet VPN.
/ip address add address={router.ip_vpn}/{prefixlen} interface=wireguard1 comment="MKRemote VPN IP"

# Configura il peer verso il VPS hub (chiave pubblica del server, fissa).
/interface wireguard peers add interface=wireguard1 \\
    public-key="{settings.VPN_HUB_PUBLIC_KEY}" \\
    endpoint-address={settings.VPN_HUB_PUBLIC_ENDPOINT} \\
    endpoint-port={settings.VPN_HUB_PUBLIC_PORT} \\
    allowed-address={settings.VPN_SUBNET_CIDR} \\
    persistent-keepalive=25s \\
    comment="MKRemote hub"

# Stampa la chiave pubblica generata: copiala nel campo "Chiave pubblica router"
# nell'app e premi "Registra peer sul server".
:put [/interface wireguard get [find name=wireguard1] public-key]
"""
