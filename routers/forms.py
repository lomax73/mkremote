from datetime import timedelta

from django import forms

from .models import Router


class RouterForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
        required=False,
        help_text='Lascia vuoto per non modificare la password esistente.',
    )
    intervallo_backup_ore = forms.IntegerField(
        label='Intervallo backup (ore)',
        min_value=1,
        required=False,
        help_text='Ogni quante ore eseguire il backup automatico. Lascia vuoto per avere '
                   'solo backup manuali.',
    )

    class Meta:
        model = Router
        # 'password' e 'intervallo_backup' non sono in questo elenco: sono gestiti
        # esplicitamente in __init__()/save() (vedi help_text dei rispettivi campi).
        fields = [
            'nome', 'location', 'note',
            'modello_hardware', 'versione_routeros',
            'ip_pubblico_o_ddns', 'ip_lan', 'porta_ssh', 'porta_api',
            'username',
            'backup_retention_count',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['password'].required = True
        if self.instance.pk:
            self.fields['intervallo_backup_ore'].initial = self.instance.intervallo_backup_ore
        self.order_fields([
            'nome', 'location', 'note',
            'modello_hardware', 'versione_routeros',
            'ip_pubblico_o_ddns', 'ip_lan', 'porta_ssh', 'porta_api',
            'username', 'password',
            'intervallo_backup_ore', 'backup_retention_count',
        ])

    def save(self, commit=True):
        router = super().save(commit=False)
        new_password = self.cleaned_data.get('password')
        if new_password:
            router.password = new_password
        ore = self.cleaned_data.get('intervallo_backup_ore')
        router.intervallo_backup = timedelta(hours=ore) if ore else None
        if commit:
            router.save()
        return router
