import boto3
from django.conf import settings


class ObjectStorageNotConfigured(Exception):
    """Manca la configurazione dell'Object Storage (vedi fase_8: non ancora provisionato)."""


def _require_config():
    if not all([
        settings.BACKUP_S3_ENDPOINT_URL,
        settings.BACKUP_S3_ACCESS_KEY,
        settings.BACKUP_S3_SECRET_KEY,
        settings.BACKUP_S3_BUCKET_NAME,
    ]):
        raise ObjectStorageNotConfigured(
            'Object Storage non configurato (BACKUP_S3_* mancanti in .env).'
        )


def _client():
    return boto3.client(
        's3',
        endpoint_url=settings.BACKUP_S3_ENDPOINT_URL,
        aws_access_key_id=settings.BACKUP_S3_ACCESS_KEY,
        aws_secret_access_key=settings.BACKUP_S3_SECRET_KEY,
    )


def upload_backup_file(local_path: str, router_nome: str, filename: str) -> str:
    """Carica un file di backup sull'Object Storage e ritorna la sua chiave S3."""
    _require_config()
    key = f'{settings.BACKUP_S3_PREFIX}/{router_nome}/{filename}'
    _client().upload_file(local_path, settings.BACKUP_S3_BUCKET_NAME, key)
    return key


def delete_backup_file(s3_key: str) -> None:
    _require_config()
    _client().delete_object(Bucket=settings.BACKUP_S3_BUCKET_NAME, Key=s3_key)
