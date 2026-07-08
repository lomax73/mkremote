import base64
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from routers.models import Router

from .connectivity import test_router_vpn_connection
from .hub_client import (
    VpsCommandFailed,
    VpsNotConfigured,
    register_peer_on_hub,
    remove_peer_from_hub,
)
from .models import PersonalVpnDevice
from .scripts import VpnHubNotConfigured, generate_personal_client_conf, generate_wireguard_setup_script
from .services import VpnSubnetExhausted, assign_personal_vpn_ip, assign_vpn_ip, generate_wireguard_keypair


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


class PersonalDeviceListView(LoginRequiredMixin, View):
    def get(self, request):
        dispositivi = PersonalVpnDevice.objects.filter(utente=request.user)
        return render(request, 'vpn/device_list.html', {'dispositivi': dispositivi})


class AddPersonalDeviceView(LoginRequiredMixin, View):
    def post(self, request):
        nome = request.POST.get('nome', '').strip()
        if not nome:
            messages.error(request, 'Dai un nome al dispositivo (es. "iPhone di Fabrizio").')
            return redirect('vpn-device-list')

        try:
            ip_vpn = assign_personal_vpn_ip()
            private_key, public_key = generate_wireguard_keypair()
            register_peer_on_hub(public_key, ip_vpn)
            conf = generate_personal_client_conf(private_key, ip_vpn)
        except (VpnSubnetExhausted, VpsNotConfigured, VpsCommandFailed, VpnHubNotConfigured) as exc:
            messages.error(request, f'Impossibile creare il dispositivo: {exc}')
            return redirect('vpn-device-list')

        device = PersonalVpnDevice.objects.create(
            utente=request.user, nome=nome, chiave_pubblica=public_key, ip_vpn=ip_vpn,
        )

        qr_img = qrcode.make(conf)
        buf = BytesIO()
        qr_img.save(buf, format='PNG')
        qr_base64 = base64.b64encode(buf.getvalue()).decode()
        conf_base64 = base64.b64encode(conf.encode()).decode()

        return render(request, 'vpn/device_created.html', {
            'device': device, 'conf': conf, 'qr_base64': qr_base64, 'conf_base64': conf_base64,
        })


class RevokePersonalDeviceView(LoginRequiredMixin, View):
    def post(self, request, pk):
        device = get_object_or_404(PersonalVpnDevice, pk=pk, utente=request.user)
        if device.attivo:
            try:
                remove_peer_from_hub(device.chiave_pubblica)
            except (VpsNotConfigured, VpsCommandFailed) as exc:
                messages.error(request, f'Revoca fallita: {exc}')
                return redirect('vpn-device-list')
            device.revocato_il = timezone.now()
            device.save(update_fields=['revocato_il'])
            messages.success(request, f'Dispositivo "{device.nome}" revocato: accesso disattivato.')
        return redirect('vpn-device-list')
