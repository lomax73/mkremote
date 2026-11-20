from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from routers.models import Router

from .hub_client import _register_peer
from .scripts import generate_lan_access_script, generate_personal_client_conf
from .services import personal_client_lan_subnets, validate_lan_subnet


def _router(nome, subnet_lan='', ip_vpn='10.10.0.10'):
    return Router.objects.create(
        nome=nome, username='u', password='p', ip_vpn=ip_vpn, subnet_lan=subnet_lan,
    )


class ValidateLanSubnetTests(TestCase):
    def test_vuota_ok(self):
        self.assertEqual(validate_lan_subnet(''), '')

    def test_valida(self):
        self.assertEqual(validate_lan_subnet('10.0.0.0/24'), '10.0.0.0/24')

    def test_rifiuta_non_valide(self):
        for value in ('10.0.0.5/24', 'pippo', '10.0.0.0/8', '10.0.0.0/31', '8.8.8.0/24', '10.10.0.0/24',
                      '10.10.0.0/16', '10.20.0.0/24', '94.177.161.0/24'):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_lan_subnet(value)

    def test_rifiuta_sovrapposizione_con_altro_router(self):
        _router('Ufficio', '10.0.0.0/24')
        with self.assertRaises(ValidationError):
            validate_lan_subnet('10.0.0.0/24')
        with self.assertRaises(ValidationError):
            validate_lan_subnet('10.0.0.0/16')

    def test_stesso_router_puo_riconfermare(self):
        r = _router('Ufficio', '10.0.0.0/24')
        self.assertEqual(validate_lan_subnet('10.0.0.0/24', exclude_pk=r.pk), '10.0.0.0/24')


class HubCommandTests(TestCase):
    def _command(self, **kwargs):
        conn = mock.MagicMock()
        conn.run = mock.AsyncMock(return_value=mock.Mock(exit_status=0, stderr=''))
        ctx = mock.MagicMock()
        ctx.__aenter__ = mock.AsyncMock(return_value=conn)
        ctx.__aexit__ = mock.AsyncMock(return_value=False)
        with mock.patch('vpn.hub_client.asyncssh.connect', return_value=ctx), \
                self.settings(VPS_SSH_HOST='h', VPS_SSH_PRIVATE_KEY_PATH='k'):
            import asyncio
            asyncio.run(_register_peer('A' * 43 + '=', '10.10.0.10', **kwargs))
        return conn.run.call_args.args[0]

    def test_senza_lan_resta_invariato(self):
        cmd = self._command()
        self.assertIn('allowed-ips 10.10.0.10/32 && wg showconf', cmd)
        self.assertNotIn('ip route', cmd)

    def test_con_lan_aggiunge_allowed_ips_e_route(self):
        cmd = self._command(lan_subnet='10.0.0.0/24')
        self.assertIn('allowed-ips 10.10.0.10/32,10.0.0.0/24 && ip route replace 10.0.0.0/24 dev wg0 && wg showconf', cmd)


class ScriptTests(TestCase):
    def test_script_lan(self):
        script = generate_lan_access_script(_router('Ufficio', '10.0.0.0/24'))
        self.assertIn('src-address=10.10.0.0/24', script)
        self.assertIn('dst-address=10.0.0.0/24 action=masquerade', script)
        self.assertIn('in-interface=wireguard-mkremote', script)

    def test_script_lan_richiede_subnet(self):
        with self.assertRaises(ValueError):
            generate_lan_access_script(_router('Senza LAN'))

    def test_client_conf_include_lan_dei_router(self):
        _router('Ufficio', '10.0.0.0/24')
        _router('Altro', '', ip_vpn='10.10.0.11')
        self.assertEqual(personal_client_lan_subnets(), ['10.0.0.0/24'])
        with self.settings(VPN_HUB_PUBLIC_ENDPOINT='vps', VPN_HUB_PUBLIC_KEY='K'):
            conf = generate_personal_client_conf('priv', '10.10.0.2', personal_client_lan_subnets())
            self.assertIn('AllowedIPs = 10.10.0.0/24, 10.0.0.0/24\n', conf)
            self.assertIn('AllowedIPs = 10.10.0.0/24\n', generate_personal_client_conf('priv', '10.10.0.2'))


class LanAccessTestTests(TestCase):
    def _run(self, router, *, tunnel=True, lan=True, hosts=None, discovered=('10.0.0.20', '10.0.0.21'), extra=''):
        from .lan_test import test_lan_access

        def fake_ping(ip, count=2, timeout_s=2):
            if ip == router.ip_vpn:
                ok = tunnel
            elif ip == router.ip_lan:
                ok = lan
            else:
                ok = ip in (hosts or ())
            return {'ok': ok, 'output': '', 'perdita_percento': 0.0 if ok else 100.0, 'rtt_medio_ms': 5.0 if ok else None}

        with mock.patch('vpn.lan_test.ping', fake_ping), \
                mock.patch('vpn.lan_test._discover_lan_hosts', return_value=(list(discovered), '')):
            return test_lan_access(router, extra)

    def _r(self):
        r = _router('Ufficio', '10.0.0.0/24', ip_vpn='10.10.0.12')
        r.ip_lan = '10.0.0.1'
        return r

    def test_ok(self):
        res = self._run(self._r(), hosts=('10.0.0.21',))
        self.assertTrue(res['ok'])
        self.assertEqual([h['ok'] for h in res['hosts']], [False, True])

    def test_tunnel_giu(self):
        res = self._run(self._r(), tunnel=False)
        self.assertFalse(res['ok'])
        self.assertIn('tunnel non è attivo', res['verdetto'])

    def test_router_ok_host_no(self):
        res = self._run(self._r(), hosts=())
        self.assertFalse(res['ok'])
        self.assertIn('masquerade', res['verdetto'])

    def test_nessun_host(self):
        res = self._run(self._r(), discovered=())
        self.assertIn('Inserisci', res['verdetto'])

    def test_senza_subnet(self):
        from .lan_test import test_lan_access
        with self.assertRaises(ValueError):
            test_lan_access(_router('X'))
