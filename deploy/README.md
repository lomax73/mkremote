# Deploy — note aggiuntive

Il deploy completo di MKRemote (systemd, Nginx, sequenza di aggiornamento)
non è ancora tracciato in questo repo; vedi la memoria di sessione
`reference_vps_deploy` per la procedura attuale sul VPS.

## API interna di gestione utenti (per il Portale)

Da questa versione, MKRemote espone `accounts/` sotto `api/internal/`
(vedi `mkremote/urls.py`) per permettere al Portale FBO di
creare/modificare/eliminare utenti da remoto. **Va esposta solo in
locale**, mai pubblicamente:

1. Aggiungere `INTERNAL_API_TOKEN` a `.env` (vedi `.env.example`):
   ```
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Aggiungere al vhost Nginx esistente di MKRemote un location block
   dedicato **prima** di quello generico `location /`, con l'accesso
   limitato a localhost:
   ```nginx
   location /api/internal/ {
       allow 127.0.0.1;
       deny all;
       proxy_pass http://unix:/run/mkremote/daphne.sock;
       proxy_set_header Host $http_host;
   }
   ```
3. `systemctl restart mkremote-web.service` dopo aver aggiornato `.env`.
4. Configurare lo stesso token nel Portale (admin → AppLink di MKRemote →
   campo "API token"), insieme a `internal_base_url =
   https://127.0.0.1:443` (o la porta usata da MKRemote).
