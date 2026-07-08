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


def generate_firewall_lockdown_script(router) -> str:
    """Genera lo script RouterOS (.rsc) per bloccare l'esposizione pubblica di
    SSH/API/WebFig, lasciandoli raggiungibili solo dalla subnet VPN (Fase 3).

    Le regole vengono inserite in cima alla chain input con `place-before`
    crescente (0, 1, 2, ...): ogni nuova regola sfila in quella posizione
    esatta, quindi l'ordine finale rispecchia l'ordine testuale dello script
    (prima gli accept dalla VPN, poi i drop generali) senza toccare o
    riordinare le regole già presenti sul router."""
    if not router.ip_vpn:
        raise ValueError('Il router non ha ancora un ip_vpn assegnato: completa prima la Fase 2.')

    return f"""\
# === MKRemote - Blocco accesso pubblico ===
# Router: {router.nome}
# ATTENZIONE: esegui questo script SOLO se il router risulta "Connesso"
# (tunnel VPN già verificato con successo). Tieni aperta una sessione
# WinBox/SSH separata come rete di sicurezza mentre lo applichi: se qualcosa
# va storto potresti perdere l'accesso remoto al router.

# 1) Accetta SSH/API/WebFig SOLO dalla subnet VPN (valutate per prime).
/ip firewall filter add chain=input action=accept protocol=tcp dst-port={router.porta_ssh} \\
    src-address={settings.VPN_SUBNET_CIDR} place-before=0 comment="MKRemote: consenti SSH da VPN"
/ip firewall filter add chain=input action=accept protocol=tcp dst-port={router.porta_api} \\
    src-address={settings.VPN_SUBNET_CIDR} place-before=1 comment="MKRemote: consenti API da VPN"
/ip firewall filter add chain=input action=accept protocol=tcp dst-port=80,443 \\
    src-address={settings.VPN_SUBNET_CIDR} place-before=2 comment="MKRemote: consenti WebFig da VPN"

# 2) Droppa le stesse porte da qualunque altra sorgente (arrivano dopo gli
#    accept di cui sopra, quindi non bloccano il traffico VPN).
/ip firewall filter add chain=input action=drop protocol=tcp dst-port={router.porta_ssh} \\
    place-before=3 comment="MKRemote: blocca SSH pubblico"
/ip firewall filter add chain=input action=drop protocol=tcp dst-port={router.porta_api} \\
    place-before=4 comment="MKRemote: blocca API pubblico"
/ip firewall filter add chain=input action=drop protocol=tcp dst-port=80,443 \\
    place-before=5 comment="MKRemote: blocca WebFig pubblico"

# Non tocca nessun'altra regola firewall già presente: solo aggiunte in cima.
# Dopo aver verificato che SSH/API/WebFig non rispondono più sull'IP
# pubblico ma continuano a rispondere su {router.ip_vpn}, torna nell'app e
# premi "Conferma blocco applicato".
"""


def generate_personal_client_conf(private_key: str, ip_vpn: str) -> str:
    """Genera il file .conf per un dispositivo personale (Fase 7): laptop o
    telefono, da importare nell'app WireGuard ufficiale (anche via QR code).

    AllowedIPs è l'intera subnet VPN (non solo l'IP del peer): così il
    dispositivo raggiunge sia l'hub sia tutti i router già collegati con un
    solo profilo, senza dover elencare ogni router singolarmente."""
    if not settings.VPN_HUB_PUBLIC_ENDPOINT or not settings.VPN_HUB_PUBLIC_KEY:
        raise VpnHubNotConfigured(
            'Il VPS hub non è ancora configurato (VPN_HUB_PUBLIC_ENDPOINT / '
            'VPN_HUB_PUBLIC_KEY mancanti in .env). Vedi fase_8 per lo stato.'
        )

    return f"""\
[Interface]
PrivateKey = {private_key}
Address = {ip_vpn}/32

[Peer]
PublicKey = {settings.VPN_HUB_PUBLIC_KEY}
Endpoint = {settings.VPN_HUB_PUBLIC_ENDPOINT}:{settings.VPN_HUB_PUBLIC_PORT}
AllowedIPs = {settings.VPN_SUBNET_CIDR}
PersistentKeepalive = 25
"""
