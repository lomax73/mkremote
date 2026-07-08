import json

from django_celery_beat.models import IntervalSchedule, PeriodicTask


def _task_name(router) -> str:
    return f'backup-router-{router.pk}'


def sync_periodic_backup_task(router) -> None:
    """Crea/aggiorna/disabilita il PeriodicTask di backup automatico per un
    router in base al suo `intervallo_backup`, senza richiedere il riavvio di
    Celery beat (DatabaseScheduler rilegge la tabella periodicamente)."""
    name = _task_name(router)

    if not router.intervallo_backup:
        PeriodicTask.objects.filter(name=name).update(enabled=False)
        return

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=int(router.intervallo_backup.total_seconds()),
        period=IntervalSchedule.SECONDS,
    )
    PeriodicTask.objects.update_or_create(
        name=name,
        defaults={
            'task': 'backups.tasks.backup_router_task',
            'interval': schedule,
            'args': json.dumps([router.pk]),
            'enabled': True,
        },
    )


def router_post_save(sender, instance, **kwargs):
    sync_periodic_backup_task(instance)
