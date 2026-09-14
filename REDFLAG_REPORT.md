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

## 2026-08-08 — richiesta diretta dell'utente: "molti backup falliscono ma non capisco perché"

### Cosa è stato fatto
1. **Log dal vivo per i backup** (`backups/models.py` — nuovo modello `BackupRun`; `backups/tasks.py`, `backups/views.py`, `backups/urls.py`, nuovo template `backup_run_detail.html`, migrazione `0004`). "Backup manuale ora" ora porta a una pagina di log che si aggiorna da sola passo passo (connessione API, generazione file, download SFTP, upload storage), invece di un messaggio generico "controlla lo storico". Aggiunto anche un elenco delle esecuzioni recenti con link al log di ciascuna nella pagina backup del router.
2. **Il log ha subito rivelato due cause concrete** dei fallimenti, indagate e corrette nello stesso `backups/tasks.py`:
   - **Timeout API troppo stretto**: `librouteros.connect()` usava il default di 10s. Il comando `/export` su router con configurazioni corpose può metterci di più, causando "timed out" anche a router funzionante. Alzato a `API_TIMEOUT_SECONDS = 60`.
   - **Nessun timeout sul download SFTP** (`asyncssh`): su una VPN instabile la connessione poteva restare bloccata **a tempo indeterminato**, occupando un worker Celery per sempre. Aggiunto `SFTP_TIMEOUT_SECONDS = 90` via `asyncio.wait_for`.
   - Aggiunto anche un **ritentativo automatico** (3 tentativi, pausa 5s) per errori di connessione/SFTP — non per errori di configurazione (es. storage non configurato), dove ritentare non ha senso.

### Verifica reale
Testato dal vivo su due router in produzione:
- **AP_Casa_Lomax**: backup binario riuscito, export in timeout — primo indizio del bug del timeout a 10s.
- **Camping del sole**: VPN chiaramente instabile verso questo sito. Prima del fix, il download SFTP restava bloccato **a tempo indeterminato** (osservato: worker Celery fermo per minuti sulla stessa riga di log, nessun errore, nessun timeout). Dopo il fix: sia binario sia export falliscono in modo **pulito e prevedibile** (esattamente ~90s per tentativo × 3 tentativi = ~5 minuti totali), con un errore chiaro nel log invece di un blocco silenzioso.

### Per chi riprende questo progetto
Il problema di fondo per "Camping del sole" (rete/VPN instabile verso quel sito, il file si genera sempre correttamente sul router ma il trasferimento SFTP non completa mai) **non è risolto** — non è un bug del software, è un problema di connettività di quel sito specifico. Ora però è diagnosticabile: chi indaga vede subito nel log che fallisce sempre allo stesso punto (SFTP, non l'API), il che restringe la causa a instabilità di rete/MTU sulla VPN verso quel router, non a un problema di RouterOS o di storage.

## 2026-08-08 — seguito: icona elimina backup, diagnostica, fix firewall, WebFig

### Aggiunte dirette (richieste dall'utente, non da FBOFlag)
- Icona 🗑️ per eliminare un backup dalla lista (elimina file su storage se presente + record). `backups/views.py`, `backups/urls.py`, `backups/templates/backups/backup_list.html`.
- Pulsante "📡 Test connessione" nella scheda router: ping + test porte SSH/API, per distinguere un problema di rete generale da una porta/servizio specifico non raggiungibile. Nuovo modulo `routers/diagnostics.py`.
- **Bug corretto in `vpn/scripts.py`** (trovato dall'utente applicando lo script su Ufficio_FBO): `generate_firewall_lockdown_script` usava `place-before=0..5` a indici fissi, assumendo un firewall vuoto — RouterOS rifiuta un `place-before` oltre la lunghezza attuale della lista, quindi lo script falliva a metà ("no such item") a seconda di quante regole erano già presenti. Rimosso `place-before`: le regole vengono ora aggiunte in fondo alla chain, sufficiente perché lo script le scrive già nell'ordine corretto (accept-VPN prima, drop-generali dopo).

### Segnalazioni FBOFlag
- [Conclusa] "webfig non funziona" (pagina `/router/8/`) — causa: il pulsante WebFig era un link diretto del browser a `http://{ip_vpn}/`, un IP privato della subnet WireGuard (10.10.0.0/24) raggiungibile solo dall'interfaccia VPN della VPS. Il browser dell'utente non ha alcuna rotta verso quella subnet — il link non ha **mai** potuto funzionare per un utilizzo reale, indipendentemente dal blocco firewall appena applicato su quel router (coincidenza di tempistiche, non causa). Per farlo funzionare servirebbe un proxy server-side (la VPS ha accesso alla VPN, il browser no) — l'utente ha scelto di rimuovere il pulsante per ora invece di costruire il proxy. File: `routers/templates/routers/router_detail.html`.

### Per chi riprende questo progetto
Se si vuole recuperare WebFig, serve una vista Django che faccia da reverse proxy autenticato verso `http://{router.ip_vpn}/` (la VPS ha accesso alla VPN, il client no) — non un semplice link `<a href>`. Nessuna nota FBOFlag aperta su MKRemote al momento.

## 2026-08-18 — sessione redflag

### Segnalazioni FBOFlag
- [Approvata, da fare in seguito] (id 46) "studiare come poter creare una vpn sul router mk per accedere alla rete utente" — resta approvata (già dal 12/08): feature sostanziosa, da progettare in una sessione dedicata.
- [Approvata, da fare in seguito] (id 47) "sezione per creare regole di firewall a livelli, con opzioni include/escludi" — resta approvata (già dal 12/08), stesso motivo della 46.
- [In test, in attesa di conferma] (id 95) "`TerminalConsumer.connect()` controlla solo `is_authenticated`, nessun controllo di ruolo: chiunque abbia un account MKRemote ottiene terminale SSH completo su ogni router (clienti reali). Stesso schema copiato in FBOAIGate (id 73 di quella sessione)" — aggiunto `SuperuserRequiredMixin` (nuovo `accounts/mixins.py`) su `TerminalConsumer.connect()`, `TerminalView`, `RouterRevealPasswordView` (credenziali in chiaro) e le viste `vpn/` che operano su router specifici. Le viste `PersonalDevice*` (VPN personale self-service, già filtrate per utente) restano invariate. Verificato l'unico utente esistente (admin) già superuser: nessun impatto pratico immediato. Testato in produzione con `Client` Django: staff non-superuser bloccato (403), admin superuser continua a funzionare (200). Deployato (commit `5cdc6bc`).
- [In test, in attesa di conferma] (id 96) "`vpn/scripts.py` inserisce `router.nome` non sanitizzato in una riga di commento `#` degli script RouterOS generati: un newline permetterebbe di far eseguire un comando RouterOS arbitrario incollando lo script su un router cliente" — doppia difesa: `RegexValidator` sul modello (`routers/models.py`, rifiuta newline dal form) + sanitizzazione nel punto di generazione script (rimpiazza newline con spazio, protegge anche bypassando il form). Migrazione `0007_alter_router_nome`. Testato in produzione entrambi i percorsi. Deployato (commit `8b5535e`, dopo un primo commit incompleto `e5cee9d` per un errore di `git add` — corretto subito dopo, notato prima di proseguire).
- [In test, in attesa di conferma] (id 97) "DEBUG=True di default, nessun promemoria esplicito — probabile origine dello schema copiato in tutte le altre app della famiglia FBO" — verificato che in produzione `DJANGO_DEBUG=false` è già impostato correttamente. Aggiunto promemoria esplicito in `.env.example` e `deploy/README.md`. Commit+push (`22febec`), nessun deploy applicativo necessario (solo doc).
- [In test, in attesa di conferma] (id 98) "`routers/portal_client.py`, `verify=False` verso il Portale — probabile origine del client copiato in FBOFiberReport/FBOPreventivi/ecc." — stesso identico fix già applicato alle altre 4 app: pinning del certificato self-signed del Portale invece di disattivare la verifica. Testato in produzione prima del commit. Deployato (commit `90c62f1`).
- [Approvata, da fare in seguito] (id 109) "mettere segnalazione via email o telegram quando un router va giù" — su richiesta dell'utente, rimandata: da implementare in `monitoring/tasks.py` (polling periodico), riusando `TELEGRAM_BOT_TOKEN`/SMTP già configurabili in `.env.example` per gli alert.

### Verifica rapida del codice
- [Trovato durante il deploy, non un bug del codice] La VPS aveva una quantità consistente di modifiche mai committate su git (deploy storicamente fatto via rsync/edit diretto invece che `git pull`), inclusa una feature reale non versionata: un campo `note` su `PersonalVpnDevice` (badge "🌉 ponte" in `vpn/models.py`/`vpn/templates/vpn/device_list.html`/`vpn/migrations/0002_personalvpndevice_note.py`). Non toccato, lasciato intatto in produzione — **da recuperare e committare in una sessione futura**, altrimenti rischia di andare perso al prossimo deploy pulito. Verificato file per file che tutto il resto del divario fosse identico al codice già presente in locale prima di allineare git.

### Per chi riprende questo progetto
Le note 95, 96, 97, 98 restano `testing` su FBOFlag finché l'utente non conferma di persona: in particolare provare login/terminale/generazione script VPN come admin (deve funzionare come prima), e verificare che salvare un router con nome normale funzioni ancora. Le note 46/47 (feature VPN utente e firewall a livelli) e 109 (alert router giù) restano `approvata` per sessioni dedicate. **Priorità per chi riprende**: recuperare su git il campo `note` di `PersonalVpnDevice`, sviluppato solo in produzione (vedi sopra).

## 2026-09-14 — segnalazione diretta dell'utente: VPS in stallo, sospetto monitoraggio MKRemote

### ⚠️ PRIORITÀ ALTA — da verificare alla prossima sessione
VPS1 (94.177.161.127, ospita tutte le app della famiglia FBO sotto `/opt/`, non solo MKRemote) è stato trovato non responsivo: ping regolare, handshake TCP accettato su tutte le porte (22/80/443/8443), ma nessun servizio applicativo rispondeva dopo l'handshake (SSH bloccato allo scambio banner, TLS mai completato) — pattern tipico di CPU al 100%/sistema in stallo, non di un singolo servizio giù. L'utente sospetta che il problema sia scatenato **dal lancio del monitoraggio di MKRemote** (pagina `/monitoraggio/`, probabile task periodico Celery di polling router).

**Da fare alla prossima sessione**: indagare `monitoring/tasks.py` e la relativa configurazione periodica (Celery beat) per un possibile loop senza backoff, polling troppo frequente/senza timeout sui router, o task che si accumulano invece di essere serializzati — verificare se avviare/lasciare attivo il monitoraggio correla con l'aumento di CPU sulla VPS fino allo stallo totale. Vedi anche la nota già aperta su Daphne single-process/single-thread (sessione 2026-08-08 sopra) — potrebbe essere un fattore aggravante ma non spiega da sola uno stallo di CPU al 100% che blocca anche SSH per l'intera VPS (non solo il servizio MKRemote).

### Per chi riprende questo progetto
Non ancora verificato nel codice, solo segnalato dall'utente a seguito dell'incidente osservato. Non toccare la configurazione di produzione finché la causa non è confermata — un riavvio del servizio/VPS può mascherare il problema senza risolverlo.
