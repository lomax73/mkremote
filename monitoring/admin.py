from django.contrib import admin

from .models import AlertEvent, AlertSettings, RouterMetric


@admin.register(RouterMetric)
class RouterMetricAdmin(admin.ModelAdmin):
    list_display = ('router', 'rilevato_il', 'cpu_load_percent', 'temperatura_celsius')
    list_filter = ('router',)
    ordering = ('-rilevato_il',)


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ('router', 'tipo', 'stato', 'aperto_il', 'chiuso_il')
    list_filter = ('tipo', 'stato', 'router')
    ordering = ('-aperto_il',)


@admin.register(AlertSettings)
class AlertSettingsAdmin(admin.ModelAdmin):
    list_display = ('soglia_cpu_percent', 'soglia_temperatura_celsius', 'telegram_abilitato', 'email_abilitata')
