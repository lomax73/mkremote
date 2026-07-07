from django.db import migrations


def create_cleanup_task(apps, schema_editor):
    CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0', hour='3', day_of_week='*', day_of_month='*', month_of_year='*',
    )
    PeriodicTask.objects.get_or_create(
        name='backups-cleanup-retention',
        defaults={
            'task': 'backups.tasks.cleanup_old_backups_task',
            'crontab': schedule,
            'enabled': True,
        },
    )


def remove_cleanup_task(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    PeriodicTask.objects.filter(name='backups-cleanup-retention').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('backups', '0001_initial'),
        ('django_celery_beat', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_cleanup_task, remove_cleanup_task),
    ]
