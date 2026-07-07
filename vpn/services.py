import ipaddress

from django.conf import settings

from routers.models import Router


class VpnSubnetExhausted(Exception):
    pass


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
