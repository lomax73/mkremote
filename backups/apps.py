from django.apps import AppConfig
from django.db.models.signals import post_save


class BackupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backups'

    def ready(self):
        from routers.models import Router

        from .signals import router_post_save

        # weak=False: router_post_save è comunque un riferimento a livello di
        # modulo (non raccolto dal GC), ma esplicito è meglio che affidarsi al
        # comportamento di default — un bug analogo con una closure locale in
        # questo stesso punto disconnetteva il segnale in silenzio.
        post_save.connect(
            router_post_save, sender=Router,
            dispatch_uid='backups_sync_periodic_task', weak=False,
        )
