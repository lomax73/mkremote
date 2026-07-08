import asyncio
import json

import asyncssh
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from routers.models import Router

from .models import SessioneTerminale


class TerminalConsumer(AsyncWebsocketConsumer):
    """Terminale SSH nel browser: apre una sessione SSH verso l'IP VPN del
    router usando le credenziali cifrate salvate in Fase 1 e inoltra I/O
    bidirezionale via WebSocket. Ogni apertura/chiusura è loggata per audit."""

    async def connect(self):
        self.user = self.scope['user']
        self.ssh_conn = None
        self.ssh_process = None
        self.reader_task = None
        self.sessione = None

        if not self.user.is_authenticated:
            await self.close()
            return

        router_pk = self.scope['url_route']['kwargs']['pk']
        self.router = await self._get_router(router_pk)
        if self.router is None or not self.router.ip_vpn:
            await self.close()
            return

        await self.accept()
        self.sessione = await self._crea_sessione()

        try:
            self.ssh_conn = await asyncssh.connect(
                self.router.ip_vpn,
                port=self.router.porta_ssh,
                username=self.router.username,
                password=self.router.password,
                known_hosts=None,
            )
            self.ssh_process = await self.ssh_conn.create_process(term_type='xterm')
        except Exception as exc:
            await self._chiudi_sessione(errore=str(exc))
            await self._send_output(f'\r\n[Errore di connessione SSH: {exc}]\r\n')
            await self.close()
            return

        self.reader_task = asyncio.create_task(self._read_ssh_output())

    async def _read_ssh_output(self):
        try:
            while True:
                data = await self.ssh_process.stdout.read(4096)
                if not data:
                    break
                await self._send_output(data)
        except Exception:
            pass
        finally:
            await self.close()

    async def _send_output(self, data: str) -> None:
        await self.send(text_data=json.dumps({'type': 'output', 'data': data}))

    async def receive(self, text_data=None, bytes_data=None):
        if self.ssh_process is None or text_data is None:
            return
        try:
            message = json.loads(text_data)
        except ValueError:
            return

        if message.get('type') == 'input':
            self.ssh_process.stdin.write(message.get('data', ''))
        elif message.get('type') == 'resize':
            cols = int(message.get('cols', 80))
            rows = int(message.get('rows', 24))
            self.ssh_process.change_terminal_size(cols, rows)

    async def disconnect(self, close_code):
        if self.reader_task:
            self.reader_task.cancel()
        if self.ssh_process:
            self.ssh_process.close()
        if self.ssh_conn:
            self.ssh_conn.close()
        await self._chiudi_sessione()

    @database_sync_to_async
    def _get_router(self, pk):
        return Router.objects.filter(pk=pk).first()

    @database_sync_to_async
    def _crea_sessione(self):
        return SessioneTerminale.objects.create(router=self.router, utente=self.user)

    @database_sync_to_async
    def _chiudi_sessione(self, errore=''):
        if self.sessione is None:
            return
        self.sessione.refresh_from_db()
        if self.sessione.chiusa_il:
            return
        self.sessione.chiusa_il = timezone.now()
        if errore:
            self.sessione.errore = errore
        self.sessione.save()
