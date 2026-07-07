import asyncio
import os
import tempfile
from datetime import datetime, timezone

import asyncssh
import librouteros
from celery import shared_task

from routers.models import Router

from .models import Backup
from .storage import ObjectStorageNotConfigured, upload_backup_file


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M')


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
            tuple(api.path('/system/backup').call('save', {'name': basename}))
        else:
            remote_filename = f'{basename}.rsc'
            tuple(api.path('/export').call('', {'file': basename}))
        return remote_filename
    finally:
        api.close()


def _run_backup_one(router: Router, tipo: str) -> None:
    basename = f'{router.nome}_{_timestamp()}'
    try:
        remote_filename = _generate_remote_file(router, tipo, basename)
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = os.path.join(tmp_dir, remote_filename)
            asyncio.run(_download_and_remove(router, remote_filename, local_path))
            size = os.path.getsize(local_path)
            s3_key = upload_backup_file(local_path, router.nome, remote_filename)
    except ObjectStorageNotConfigured as exc:
        Backup.objects.create(router=router, tipo=tipo, esito=Backup.Esito.FALLITO, errore=str(exc))
    except Exception as exc:  # connessione router, SFTP, backup RouterOS falliti, ecc.
        Backup.objects.create(router=router, tipo=tipo, esito=Backup.Esito.FALLITO, errore=str(exc))
    else:
        Backup.objects.create(
            router=router, tipo=tipo, esito=Backup.Esito.RIUSCITO,
            s3_key=s3_key, dimensione_bytes=size,
        )


@shared_task
def backup_router_task(router_id: int) -> None:
    router = Router.objects.get(pk=router_id)
    for tipo in (Backup.Tipo.BINARIO, Backup.Tipo.EXPORT):
        _run_backup_one(router, tipo)


@shared_task
def cleanup_old_backups_task() -> None:
    from .retention import cleanup_old_backups
    cleanup_old_backups()
