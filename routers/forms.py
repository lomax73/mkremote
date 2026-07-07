from django import forms

from .models import Router


class RouterForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(render_value=False, attrs={'autocomplete': 'new-password'}),
        required=False,
        help_text='Lascia vuoto per non modificare la password esistente.',
    )

    class Meta:
        model = Router
        # 'password' non è in questo elenco: è gestita esplicitamente in save()
        # per evitare che Django la sovrascriva con una stringa vuota quando
        # l'utente la lascia bianca in modifica (vedi help_text del campo).
        fields = [
            'nome', 'location', 'note',
            'modello_hardware', 'versione_routeros',
            'ip_pubblico_o_ddns', 'porta_ssh', 'porta_api',
            'username',
            'intervallo_backup', 'backup_retention_count',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['password'].required = True

    def save(self, commit=True):
        router = super().save(commit=False)
        new_password = self.cleaned_data.get('password')
        if new_password:
            router.password = new_password
        if commit:
            router.save()
        return router
