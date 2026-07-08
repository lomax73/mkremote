from django import forms

from .models import AlertSettings


class AlertSettingsForm(forms.ModelForm):
    class Meta:
        model = AlertSettings
        fields = [
            'soglia_cpu_percent', 'soglia_temperatura_celsius',
            'fallimenti_consecutivi_per_offline', 'cooldown_minuti',
            'telegram_abilitato', 'telegram_chat_id',
            'email_abilitata', 'email_destinatario',
        ]
