from django.apps import AppConfig
from django.db.models.signals import post_save


class BackupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backups'

    def ready(self):
        from routers.models import Router

        from .signals import sync_periodic_backup_task

        def _handler(sender, instance, **kwargs):
            sync_periodic_backup_task(instance)

        post_save.connect(_handler, sender=Router, dispatch_uid='backups_sync_periodic_task')
