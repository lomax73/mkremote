#!/bin/bash
# Wrapper SSH forced-command: esegue SOLO la sequenza wg set/showconf/syncconf
# per l'interfaccia wg0, validando rigorosamente i parametri ricevuti.
# Installato sul VPS in /usr/local/sbin/mkremote-wg-peer.sh (vedi authorized_keys).
# Non deve mai eseguire comandi arbitrari anche se la chiave viene compromessa.
#
# Tre varianti accettate, tutte generate da vpn/hub_client.py:
#   1) registrazione peer (allowed-ips = solo IP VPN /32)
#   2) registrazione peer con LAN: allowed-ips = IP VPN /32 + subnet LAN, più
#      `ip route replace <subnet LAN> dev wg0` (wg set non aggiunge la route)
#   3) rimozione peer (revoca dispositivi VPN personali)
#
# La subnet LAN è l'unico valore "pericoloso": una rete errata instradata su un
# peer potrebbe dirottare traffico (VPN, wg1, rete pubblica del VPS). Per questo
# viene validata con python3 ipaddress oltre che con la regex.
# Tenere allineato con RESERVED_LAN_NETWORKS in vpn/services.py.
set -euo pipefail

CMD="${SSH_ORIGINAL_COMMAND:-}"

KEY='[A-Za-z0-9+/]{43}='
CIDR='[0-9]{1,3}(\.[0-9]{1,3}){3}/[0-9]{1,2}'
TAIL='wg showconf wg0 > /etc/wireguard/wg0\.conf && wg syncconf wg0 /etc/wireguard/wg0\.conf'

REGISTER_PATTERN="^wg set wg0 peer ${KEY} allowed-ips 10\.10\.0\.[0-9]{1,3}/32 && ${TAIL}\$"
REGISTER_LAN_PATTERN="^wg set wg0 peer ${KEY} allowed-ips 10\.10\.0\.[0-9]{1,3}/32,(${CIDR}) && ip route replace (${CIDR}) dev wg0 && ${TAIL}\$"
REMOVE_PATTERN="^wg set wg0 peer ${KEY} remove && ${TAIL}\$"

if [[ "$CMD" =~ $REGISTER_PATTERN ]] || [[ "$CMD" =~ $REMOVE_PATTERN ]]; then
    exec bash -c "$CMD"
elif [[ "$CMD" =~ $REGISTER_LAN_PATTERN ]]; then
    LAN_A="${BASH_REMATCH[1]}"
    # gruppi: 1=CIDR allowed-ips, 2=ultimo ottetto (dentro CIDR), 3=CIDR route, 4=ottetto
    LAN_B="${BASH_REMATCH[3]}"
    [[ "$LAN_A" == "$LAN_B" ]] || { echo 'Subnet incoerenti' >&2; exit 1; }
    python3 -I - "$LAN_A" 2>/dev/null <<'PY' || { echo 'Subnet LAN non consentita' >&2; exit 1; }
import ipaddress, sys
net = ipaddress.ip_network(sys.argv[1], strict=True)
reserved = [ipaddress.ip_network(n) for n in ('10.10.0.0/24', '10.20.0.0/24', '94.177.161.0/24')]
ok = (net.version == 4 and net.is_private and 16 <= net.prefixlen <= 30
      and not any(net.overlaps(r) for r in reserved))
sys.exit(0 if ok else 1)
PY
    exec bash -c "$CMD"
else
    echo 'Comando non consentito' >&2
    exit 1
fi
