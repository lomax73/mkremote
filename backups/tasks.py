import asyncio
import os
import tempfile
from datetime import datetime, timezone

import asyncssh
import librouteros
from celery import shared_task
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.utils import timezone as django_timezone

from monitoring.models import AlertEvent
from monitoring.notifications import close_alert, open_or_get_alert
from routers.models import Router

from .models import Backup, BackupRun
from .storage import ObjectStorageNotConfigured, upload_backup_file


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M')


def _log(run_id: int, msg: str) -> None:
    line = f'[{django_timezone.now().strftime("%H:%M:%S")}] {msg}\n'
    BackupRun.objects.filter(pk=run_id).update(log=Concat(F('log'), Value(line)))


async def _download_and_remove(router: Router, remote_filename: str, local_path: str) -> None:
    async with asyncssh.connect(
        router.ip_vpn,
        port=router.porta_ssh,
        username=router.username,
        password=router.password,
        known_hosts=None,
    ) as conn:
        async with conn.start_sftp_client() as sftp:
            await sftp.get(remote_filename, local_path)
            await sftp.remove(remote_filename)


def _generate_remote_file(router: Router, tipo: str, basename: str) -> str:
    """Chiede al router (via API RouterOS) di generare il file di backup/export
    e ritorna il nome del file remoto risultante."""
    api = librouteros.connect(
        host=router.ip_vpn,
        username=router.username,
        password=router.password,
        port=router.porta_api,
    )
    try:
        if tipo == Backup.Tipo.BINARIO:
            remote_filename = f'{basename}.backup'
            tuple(api.path('/system/backup')('save', name=basename))
        else:
            remote_filename = f'{basename}.rsc'
            tuple(api.path('/export')('', file=basename))
        return remote_filename
    finally:
        api.close()


def _run_backup_one(router: Router, tipo: str, run_id: int) -> None:
    label = 'binario' if tipo == Backup.Tipo.BINARIO else 'export'
    basename = f'{router.nome}_{_timestamp()}'
    _log(run_id, f'Backup {label}: connessione all\'API RouterOS di {router.nome} ({router.ip_vpn}:{router.porta_api})...')
    try:
        remote_filename = _generate_remote_file(router, tipo, basename)
        _log(run_id, f'Backup {label}: file generato sul router ({remote_filename}). Scaricamento via SFTP...')
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = os.path.join(tmp_dir, remote_filename)
            asyncio.run(_download_and_remove(router, remote_filename, local_path))
            size = os.path.getsize(local_path)
            _log(run_id, f'Backup {label}: scaricato ({size} byte). Caricamento sullo storage...')
            storage_path = upload_backup_file(local_path, router.nome, remote_filename)
    except ObjectStorageNotConfigured as exc:
        _log(run_id, f'Backup {label}: ERRORE — storage non configurato: {exc}')
        Backup.objects.create(router=router, run_id=run_id, tipo=tipo, esito=Backup.Esito.FALLITO, errore=str(exc))
        open_or_get_alert(router, AlertEvent.Tipo.BACKUP_FALLITO, str(exc))
    except Exception as exc:  # connessione router, SFTP, backup RouterOS falliti, ecc.
        _log(run_id, f'Backup {label}: ERRORE — {exc}')
        Backup.objects.create(router=router, run_id=run_id, tipo=tipo, esito=Backup.Esito.FALLITO, errore=str(exc))
        open_or_get_alert(router, AlertEvent.Tipo.BACKUP_FALLITO, str(exc))
    else:
        _log(run_id, f'Backup {label}: completato con successo ({size} byte caricati).')
        Backup.objects.create(
            router=router, run_id=run_id, tipo=tipo, esito=Backup.Esito.RIUSCITO,
            storage_path=storage_path, dimensione_bytes=size,
        )
        close_alert(router, AlertEvent.Tipo.BACKUP_FALLITO)


@shared_task
def backup_router_task(router_id: int, run_id: int | None = None) -> None:
    router = Router.objects.get(pk=router_id)
    if run_id is not None:
        run = BackupRun.objects.get(pk=run_id)
    else:
        run = BackupRun.objects.create(router=router)
        run_id = run.pk

    _log(run_id, f'Avvio backup di {router.nome}.')
    for tipo in (Backup.Tipo.BINARIO, Backup.Tipo.EXPORT):
        _run_backup_one(router, tipo, run_id)

    _log(run_id, 'Terminato.')
    BackupRun.objects.filter(pk=run_id).update(
        stato=BackupRun.Stato.COMPLETATO, concluso_il=django_timezone.now(),
    )


@shared_task
def cleanup_old_backups_task() -> None:
    from .retention import cleanup_old_backups
    cleanup_old_backups()
