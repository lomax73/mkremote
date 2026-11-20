"""Test di raggiungibilità della LAN dietro un router, eseguito dal VPS hub.

Il traffico parte dall'hub (10.10.0.1, dentro la subnet VPN): attraversa lo
stesso percorso dei dispositivi personali (route sull'hub -> peer del router ->
masquerade/forward sul router -> host LAN), quindi verifica il lato server e il
lato router. NON verifica il profilo WireGuard del singolo dispositivo
(AllowedIPs del client): per quello serve un ping dal dispositivo stesso."""

import ipaddress
from concurrent.futures import ThreadPoolExecutor

import librouteros
from routers.diagnostics import ping

MAX_HOST_AUTO = 5


def _discover_lan_hosts(router, network, timeout: float = 5.0) -> tuple[list[str], str]:
    """Legge la tabella ARP del router e restituisce fino a MAX_HOST_AUTO host
    della LAN (escluso il router stesso). Ritorna (host, messaggio_errore)."""
    try:
        api = librouteros.connect(
            host=router.ip_vpn, username=router.username, password=router.password,
            port=router.porta_api, timeout=timeout,
        )
    except Exception as exc:
        return [], f'API del router non raggiungibile: {exc}'
    try:
        entries = list(api.path('/ip/arp'))
    except Exception as exc:
        return [], f'Lettura tabella ARP fallita: {exc}'
    finally:
        api.close()

    own = {router.ip_lan} if router.ip_lan else set()
    hosts = []
    for entry in entries:
        address = entry.get('address')
        if not address or address in own or not entry.get('mac-address'):
            continue
        if entry.get('status') in ('failed', 'incomplete'):
            continue
        try:
            if ipaddress.ip_address(address) in network and address not in hosts:
                hosts.append(address)
        except ValueError:
            continue
    return sorted(hosts, key=ipaddress.ip_address)[:MAX_HOST_AUTO], ''


def test_lan_access(router, extra_host: str = '') -> dict:
    """Esegue il test e restituisce un dict con i passi e un verdetto leggibile."""
    if not router.ip_vpn or not router.subnet_lan:
        raise ValueError('Servono un IP VPN assegnato e la subnet LAN del router.')
    network = ipaddress.ip_network(router.subnet_lan)

    steps = {'tunnel': ping(router.ip_vpn, count=2)}
    result = {'subnet': router.subnet_lan, 'tunnel': steps['tunnel'], 'router_lan': None,
              'hosts': [], 'discovery_error': '', 'verdetto': '', 'ok': False}

    if not steps['tunnel']['ok']:
        result['verdetto'] = ('Il router non risponde sull\'IP VPN: il tunnel non è attivo. '
                              'Risolvi prima questo, poi ripeti il test.')
        return result

    targets = []
    if extra_host:
        targets.append(extra_host)
    else:
        discovered, err = _discover_lan_hosts(router, network)
        result['discovery_error'] = err
        targets = discovered

    with ThreadPoolExecutor(max_workers=6) as pool:
        lan_future = pool.submit(ping, router.ip_lan, 2) if router.ip_lan else None
        host_futures = [(h, pool.submit(ping, h, 2)) for h in targets]
        if lan_future:
            result['router_lan'] = {'ip': router.ip_lan, **lan_future.result()}
        result['hosts'] = [{'ip': h, **f.result()} for h, f in host_futures]

    host_ok = any(h['ok'] for h in result['hosts'])
    lan_ok = bool(result['router_lan'] and result['router_lan']['ok'])
    if host_ok:
        result['ok'] = True
        result['verdetto'] = ('LAN raggiungibile: almeno un PC della LAN risponde. Lato server e router a posto. '
                              'Se dal tuo dispositivo non funziona, controlla che il profilo WireGuard '
                              f'abbia {router.subnet_lan} negli AllowedIPs.')
    elif not result['hosts']:
        result['verdetto'] = ('Nessun PC della LAN da provare (tabella ARP vuota o non leggibile). '
                              'Inserisci l\'IP di un PC acceso della LAN e ripeti il test.')
    elif lan_ok:
        result['verdetto'] = ('Il router risponde sul suo IP LAN ma i PC no: manca o non è attiva la regola '
                              'masquerade/forward sul router (esegui lo script "Accesso LAN"), oppure i PC '
                              'bloccano il ping (firewall Windows) — prova con un altro host.')
    else:
        result['verdetto'] = ('Né il router (IP LAN) né i PC rispondono: controlla di aver premuto '
                              '"Registra peer sul server" dopo aver impostato la subnet e che lo script '
                              '"Accesso LAN" sia stato eseguito sul router.')
    return result
