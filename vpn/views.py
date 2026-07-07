from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from routers.models import Router

from .connectivity import test_router_vpn_connection
from .hub_client import VpsCommandFailed, VpsNotConfigured, register_peer_on_hub
from .scripts import VpnHubNotConfigured, generate_wireguard_setup_script
from .services import VpnSubnetExhausted, assign_vpn_ip


class GenerateVpnScriptView(LoginRequiredMixin, View):
    def get(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        try:
            assign_vpn_ip(router)
            script = generate_wireguard_setup_script(router)
        except (VpnSubnetExhausted, VpnHubNotConfigured) as exc:
            messages.error(request, str(exc))
            return redirect('router-detail', pk=router.pk)
        return render(request, 'vpn/script.html', {'router': router, 'script': script})


class SaveWireguardPublicKeyView(LoginRequiredMixin, View):
    def post(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        public_key = request.POST.get('chiave_pubblica_wireguard', '').strip()
        if not public_key:
            messages.error(request, 'Incolla la chiave pubblica restituita dal router.')
        else:
            router.chiave_pubblica_wireguard = public_key
            router.save(update_fields=['chiave_pubblica_wireguard'])
            messages.success(request, 'Chiave pubblica salvata.')
        return redirect('router-detail', pk=router.pk)


class RegisterPeerView(LoginRequiredMixin, View):
    def post(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        if not router.chiave_pubblica_wireguard or not router.ip_vpn:
            messages.error(request, 'Servono sia la chiave pubblica che un IP VPN assegnato prima di registrare il peer.')
            return redirect('router-detail', pk=router.pk)
        try:
            register_peer_on_hub(router.chiave_pubblica_wireguard, router.ip_vpn)
        except (VpsNotConfigured, VpsCommandFailed) as exc:
            messages.error(request, f'Registrazione peer fallita: {exc}')
        else:
            router.stato_connessione = Router.StatoConnessione.IN_ATTESA_VPN
            router.save(update_fields=['stato_connessione'])
            messages.success(request, 'Peer registrato sul VPS. Esegui ora il test connessione.')
        return redirect('router-detail', pk=router.pk)


class TestVpnConnectionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        router = get_object_or_404(Router, pk=pk)
        ok = test_router_vpn_connection(router)
        if ok:
            messages.success(request, "Connessione VPN riuscita: il router risponde sull'IP VPN.")
        else:
            messages.error(request, "Connessione VPN fallita: il router non risponde sull'IP VPN.")
        return redirect('router-detail', pk=router.pk)
