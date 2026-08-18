import ipaddress

from django.conf import settings


class VpnHubNotConfigured(Exception):
    """Il VPS hub non è ancora provisionato (endpoint/chiave pubblica mancanti)."""


def _sanitize_comment(text: str) -> str:
    """Rimuove newline/ritorni a capo da un valore prima di inserirlo in una
    riga di commento `#` di uno script RouterOS: un newline non filtrato
    farebbe terminare il commento a metà riga, trasformando quella
    successiva in un comando RouterOS vero e proprio (RedFlag id 96)."""
    return text.replace('\r', ' ').replace('\n', ' ')


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
    nome = _sanitize_comment(router.nome)

    return f"""\
# === MKRemote - Setup tunnel WireGuard verso il VPS hub ===
# Router: {nome}
# Da eseguire in un terminale RouterOS (WinBox o SSH). Non tocca il firewall:
# il blocco dell'accesso pubblico si fa solo dopo aver verificato il tunnel
# (vedi Fase 3), da un'altra sessione con accesso di riserva aperta.

# Crea l'interfaccia WireGuard e genera la coppia di chiavi direttamente qui:
# la chiave privata resta sul router, non viene mai trasmessa altrove.
/interface wireguard add name=wireguard-mkremote listen-port=51820 comment="MKRemote hub tunnel"

# Assegna l'IP privato riservato a questo router nella subnet VPN.
/ip address add address={router.ip_vpn}/{prefixlen} interface=wireguard-mkremote comment="MKRemote VPN IP"

# Configura il peer verso il VPS hub (chiave pubblica del server, fissa).
/interface wireguard peers add interface=wireguard-mkremote \\
    public-key="{settings.VPN_HUB_PUBLIC_KEY}" \\
    endpoint-address={settings.VPN_HUB_PUBLIC_ENDPOINT} \\
    endpoint-port={settings.VPN_HUB_PUBLIC_PORT} \\
    allowed-address={settings.VPN_SUBNET_CIDR} \\
    persistent-keepalive=25s \\
    comment="MKRemote hub"

# Stampa la chiave pubblica generata: copiala nel campo "Chiave pubblica router"
# nell'app e premi "Registra peer sul server".
:put [/interface wireguard get [find name=wireguard-mkremote] public-key]
"""


def generate_firewall_lockdown_script(router) -> str:
    """Genera lo script RouterOS (.rsc) per bloccare l'esposizione pubblica di
    SSH/API/WebFig, lasciandoli raggiungibili solo dalla subnet VPN (Fase 3).

    Le regole vengono semplicemente aggiunte in coda alla chain input, senza
    `place-before`: RouterOS valuta le regole nell'ordine in cui compaiono,
    quindi bastano gli accept-dalla-VPN prima e i drop-generali dopo (stesso
    ordine del testo dello script) per ottenere il comportamento voluto.
    Niente indici di posizione hardcoded — con `place-before=N` a numero
    fisso lo script falliva con "no such item" a seconda di quante regole
    erano già presenti sul router (il numero di regole già esistenti sfasa
    tutte le posizioni successive)."""
    if not router.ip_vpn:
        raise ValueError('Il router non ha ancora un ip_vpn assegnato: completa prima la Fase 2.')

    nome = _sanitize_comment(router.nome)

    return f"""\
# === MKRemote - Blocco accesso pubblico ===
# Router: {nome}
# ATTENZIONE: esegui questo script SOLO se il router risulta "Connesso"
# (tunnel VPN già verificato con successo). Tieni aperta una sessione
# WinBox/SSH separata come rete di sicurezza mentre lo applichi: se qualcosa
# va storto potresti perdere l'accesso remoto al router.
#
# Le regole vengono aggiunte in fondo alla chain input (nessun place-before):
# se sul router esiste già una regola che accetta esplicitamente queste
# porte da altre sorgenti PRIMA di queste, quella regola avrebbe comunque
# precedenza — controlla `/ip firewall filter print` prima di applicare se
# hai dubbi su regole personalizzate già presenti.

# 1) Accetta SSH/API/WebFig SOLO dalla subnet VPN (valutate per prime).
/ip firewall filter add chain=input action=accept protocol=tcp dst-port={router.porta_ssh} \\
    src-address={settings.VPN_SUBNET_CIDR} comment="MKRemote: consenti SSH da VPN"
/ip firewall filter add chain=input action=accept protocol=tcp dst-port={router.porta_api} \\
    src-address={settings.VPN_SUBNET_CIDR} comment="MKRemote: consenti API da VPN"
/ip firewall filter add chain=input action=accept protocol=tcp dst-port=80,443 \\
    src-address={settings.VPN_SUBNET_CIDR} comment="MKRemote: consenti WebFig da VPN"

# 2) Droppa le stesse porte da qualunque altra sorgente (arrivano dopo gli
#    accept di cui sopra, quindi non bloccano il traffico VPN).
/ip firewall filter add chain=input action=drop protocol=tcp dst-port={router.porta_ssh} \\
    comment="MKRemote: blocca SSH pubblico"
/ip firewall filter add chain=input action=drop protocol=tcp dst-port={router.porta_api} \\
    comment="MKRemote: blocca API pubblico"
/ip firewall filter add chain=input action=drop protocol=tcp dst-port=80,443 \\
    comment="MKRemote: blocca WebFig pubblico"

# Non tocca né riordina nessuna regola firewall già presente: solo aggiunte
# in fondo alla lista. Dopo aver verificato che SSH/API/WebFig non
# rispondono più sull'IP pubblico ma continuano a rispondere su
# {router.ip_vpn}, torna nell'app e premi "Conferma blocco applicato".
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
