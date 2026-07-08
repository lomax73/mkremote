from routers.models import Router

from .models import Backup
from .storage import ObjectStorageNotConfigured, delete_backup_file


def cleanup_old_backups() -> None:
    """Per ogni router, tiene solo gli ultimi `backup_retention_count` backup
    riusciti (per tipo) e rimuove i più vecchi, sia dallo storage che dal DB."""
    for router in Router.objects.all():
        for tipo in (Backup.Tipo.BINARIO, Backup.Tipo.EXPORT):
            riusciti = Backup.objects.filter(
                router=router, tipo=tipo, esito=Backup.Esito.RIUSCITO,
            ).order_by('-creato_il')
            da_rimuovere = riusciti[router.backup_retention_count:]
            for backup in da_rimuovere:
                if backup.storage_path:
                    try:
                        delete_backup_file(backup.storage_path)
                    except ObjectStorageNotConfigured:
                        continue
                backup.delete()
