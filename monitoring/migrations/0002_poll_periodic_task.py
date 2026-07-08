from django.conf import settings
from django.db import migrations


def create_poll_task(apps, schema_editor):
    IntervalSchedule = apps.get_model('django_celery_beat', 'IntervalSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=settings.MONITORING_POLL_INTERVAL_SECONDS,
        period='seconds',  # IntervalSchedule.SECONDS non esiste sul modello storico/congelato
    )
    PeriodicTask.objects.get_or_create(
        name='monitoring-poll-routers',
        defaults={
            'task': 'monitoring.tasks.poll_routers_task',
            'interval': schedule,
            'enabled': True,
        },
    )


def remove_poll_task(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    PeriodicTask.objects.filter(name='monitoring-poll-routers').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0001_initial'),
        ('django_celery_beat', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_poll_task, remove_poll_task),
    ]
