# Report sessioni redflag

Report generati dalla skill `redflag`: segnalazioni FBOFlag esaminate e verifica rapida del codice.

## 2026-08-08 — sessione redflag

### Verifica rapida del codice
Nessun problema evidente in una prima occhiata (indagine più approfondita fatta per la nota #19, vedi sotto).

### Segnalazioni FBOFlag
- [Conclusa] "reset allert bottone" (pagina `/monitoraggio/`) — aggiunto pulsante "Reset" per chiudere manualmente un `AlertEvent` aperto, sia nella dashboard sia nel dettaglio router. Nuovo endpoint `POST /monitoraggio/alert/<pk>/reset/`, redirect verso l'origine validato con `url_has_allowed_host_and_scheme` (niente open redirect via header Referer). File: `monitoring/urls.py`, `monitoring/views.py`, `monitoring/templates/monitoring/dashboard.html`, `monitoring/templates/monitoring/router_detail.html`.
- [Conclusa] "link pagina dei backup sulla barra di destra" — non esisteva un elenco globale dei backup (solo per singolo router). Aggiunta una pagina di overview (`/backup/`) con tutti i router e l'esito dell'ultimo backup di ciascuno, più il link "Backup" nella sidebar principale. File: `backups/views.py`, `backups/urls.py`, nuovo template `backups/templates/backups/backup_overview.html`, `templates/base.html`.
- [Approvata, da fare in seguito] "lentezza nel cambio pagina e anche nel inviare bug" — causa plausibile individuata: **Daphne gira in un solo processo/event-loop** (`ExecStart` in `/etc/systemd/system/mkremote-web.service` senza parallelismo). Django instrada le viste sincrone (praticamente tutte) su un unico thread dedicato quando servite via ASGI — le richieste si accodano una alla volta sotto carico concorrente (pagine + WebSocket del terminale + task di monitoraggio in background). Soluzione proposta: passare da `daphne` a `gunicorn -k uvicorn.workers.UvicornWorker` con più worker — il layer Channels usa già Redis, quindi supporta nativamente il multi-processo per HTTP e WebSocket. L'utente ha chiesto di rimandare (tocca l'infrastruttura di produzione, da fare con calma).

### Per chi riprende questo progetto
Resta aperta la nota #19 (approvata, non implementata): quando si affronta, il cambio è nel file `deploy/` + `/etc/systemd/system/mkremote-web.service` sulla VPS — sostituire `daphne -u /run/mkremote/daphne.sock mkremote.asgi:application` con `gunicorn mkremote.asgi:application -k uvicorn.workers.UvicornWorker --bind unix:/run/mkremote/daphne.sock --workers 3` (o simile), poi verificare che sia le pagine normali sia il terminale SSH via WebSocket (Channels) continuino a funzionare con più worker attivi.
