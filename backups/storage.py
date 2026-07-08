from ftplib import FTP_TLS, error_perm

from django.conf import settings


class ObjectStorageNotConfigured(Exception):
    """Manca la configurazione dello spazio FTPS per i backup (vedi fase_8)."""


def _require_config():
    if not all([
        settings.BACKUP_FTP_HOST,
        settings.BACKUP_FTP_USER,
        settings.BACKUP_FTP_PASSWORD,
    ]):
        raise ObjectStorageNotConfigured(
            'Spazio FTPS non configurato (BACKUP_FTP_* mancanti in .env).'
        )


def _connect() -> FTP_TLS:
    ftp = FTP_TLS(timeout=30)
    ftp.connect(settings.BACKUP_FTP_HOST, settings.BACKUP_FTP_PORT)
    ftp.auth()
    ftp.login(settings.BACKUP_FTP_USER, settings.BACKUP_FTP_PASSWORD)
    ftp.prot_p()  # cifra anche il canale dati, non solo quello di controllo
    return ftp


def _ensure_dir(ftp: FTP_TLS, path: str) -> None:
    """Crea (se mancante) ogni segmento della directory e ci si posiziona dentro."""
    ftp.cwd('/')
    for segment in path.strip('/').split('/'):
        try:
            ftp.cwd(segment)
        except error_perm:
            ftp.mkd(segment)
            ftp.cwd(segment)


def upload_backup_file(local_path: str, router_nome: str, filename: str) -> str:
    """Carica un file di backup sullo spazio FTPS e ritorna il suo percorso remoto."""
    _require_config()
    remote_dir = f'{settings.BACKUP_FTP_BASE_PATH}/{router_nome}'
    ftp = _connect()
    try:
        _ensure_dir(ftp, remote_dir)
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
    finally:
        ftp.quit()
    return f'{remote_dir}/{filename}'


def delete_backup_file(storage_path: str) -> None:
    _require_config()
    ftp = _connect()
    try:
        ftp.delete(storage_path)
    finally:
        ftp.quit()
