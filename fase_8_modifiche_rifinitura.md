# Fase 8 — Modifiche e rifinitura

## Cos'è questo file
A differenza delle altre fasi, questo file **non ha un obiettivo unico e non segue
l'ordine numerico**. È un contenitore vivo, aggiornato in continuazione durante tutte
le altre fasi (vedi `fase_-1_workflow.md`, regola 3).

Ogni volta che durante una fase emerge:
- un dubbio tecnico non banale
- una scelta con più alternative valide
- una funzionalità utile ma non bloccante da rimandare

...va annotata qui invece di essere decisa in modo definitivo e silenzioso durante lo
sviluppo della fase corrente.

## Formato di una voce

Per ogni voce aggiunta, usare questo schema minimo:

```
### [Fase di origine] Titolo breve del dubbio/rimando
- Contesto: perché è emerso
- Opzioni valutate: elenco alternative con pro/contro
- Scelta di default adottata (se presa per non bloccare la fase): quale e perché
- Stato: da decidere / rimandato / risolto
```

## Rifiniture note già previste da subito

Queste sono rifiniture individuate in fase di progettazione iniziale, da affrontare
qui quando le fasi 0-7 sono stabili:

### [Generale] Autenticazione a due fattori (2FA) sul login dashboard
- Stato: da decidere (quale libreria/metodo: TOTP standard consigliato)

### [Generale] Audit log
- Traccia di chi ha fatto cosa e quando (creazione/modifica router, esecuzione
  backup manuale, apertura terminale, modifiche a soglie di alert)
- Stato: da decidere

### [Generale] Ruoli utente
- Da valutare solo se in futuro l'accesso alla dashboard viene condiviso con
  collaboratori (oggi non è un requisito, uso singolo utente)
- Stato: rimandato, non necessario allo stato attuale

---

## Voci aggiunte durante lo sviluppo

*(Claude Code aggiunge qui le nuove voci man mano che emergono durante le fasi 0-7,
seguendo il formato sopra)*

### [Fase 0] Hosting: stesso VPS di Squadfy o VPS dedicato
- Contesto: la fase 0 richiede di scegliere se ospitare MKRemote sullo stesso VPS
  Hetzner già usato per Squadfy oppure su un VPS dedicato separato.
- Opzioni valutate:
  - VPS dedicato: isolamento completo, firewall/subnet VPN dedicati, nessun rischio
    di impatto su Squadfy, ma costo aggiuntivo e setup infrastrutturale da rifare.
  - Stesso VPS di Squadfy: nessun costo aggiuntivo, infrastruttura (Postgres/Redis/
    Nginx) già presente, ma rischio di impatto reciproco tra i due progetti e
    perimetro di sicurezza condiviso (rilevante qui perché il progetto gestisce
    accesso privilegiato a router in produzione).
- Scelta di default adottata: nessuna, esplicitamente rimandata dall'utente.
  Procediamo con lo scaffolding locale del progetto Django, che non dipende da
  questa scelta; la decisione infrastrutturale va presa prima di eseguire i task
  di setup server (punto 2 di fase_0_fondamenta.md).
- Stato: da decidere

### [Fase 0] Verifica end-to-end locale (Postgres/Redis/Celery) rimandata
- Contesto: Postgres e Redis non sono installati sul Mac di sviluppo. L'utente ha
  scelto di non installarli localmente (né nativamente né via Docker) e di
  rimandare il test end-to-end direttamente al VPS.
- Scelta di default adottata: lo scaffolding del progetto (settings, app, Celery,
  requirements) è stato completato e validato solo staticamente (`manage.py check`,
  import di `mkremote.celery` e autodiscovery del task di prova
  `monitoring.tasks.ping_task`). La connessione reale a Postgres/Redis, le
  migrazioni, la creazione del superuser e l'esecuzione effettiva di Celery
  worker+beat vanno verificate quando sarà disponibile il VPS (o un ambiente con
  Postgres/Redis attivi).
- Stato: rimandato

### [Fase 1] django-cryptography incompatibile con Django 5.2, sostituito con Fernet diretto
- Contesto: `django-cryptography` 1.1 (l'unica versione disponibile) importa
  `django.utils.baseconv`, rimosso in Django 5.2. Il pacchetto non è più
  mantenuto e non ha una versione compatibile.
- Opzioni valutate:
  - Fissare Django a una versione <5.2 pur di usare django-cryptography: scarterebbe
    funzionalità/fix più recenti e comunque lega il progetto a una libreria non
    mantenuta.
  - Implementare un campo custom (`routers.fields.EncryptedCharField`) basato
    direttamente su `cryptography.fernet.Fernet`: nessuna dipendenza aggiuntiva
    oltre `cryptography` (già transitiva), piena compatibilità con Django 5.2,
    logica di cifratura sotto il nostro controllo diretto.
- Scelta di default adottata: implementato il campo custom con Fernet. La chiave
  master (`MASTER_ENCRYPTION_KEY` in `.env`) deve ora essere generata con
  `Fernet.generate_key()` (documentato in `.env.example`), non più con
  `secrets.token_urlsafe`. Verificato con test isolato (SQLite in-memory) che
  cifratura/decrittazione e round-trip su `username`/`password` funzionano
  correttamente.
- Stato: risolto

### [Fase 2] Verifica end-to-end reale rimandata al VPS (nessun hub WireGuard disponibile)
- Contesto: la Fase 2 richiede un VPS con hub WireGuard (`wg0`) attivo e
  raggiungibile via SSH (Fase 0, non ancora fatta). Senza VPS reale non è
  possibile eseguire lo script su un router vero né registrare davvero un peer.
- Scelta di default adottata: implementata tutta la logica applicativa
  (assegnazione IP idempotente, generatore script `.rsc`, client SSH verso il
  VPS con `wg set` + `wg showconf` + `wg syncconf` per evitare downtime, test
  di connessione via API RouterOS) dietro configurazione esplicita in `.env`
  (`VPN_HUB_PUBLIC_ENDPOINT`, `VPN_HUB_PUBLIC_KEY`, `VPS_SSH_HOST`, ecc.), tutta
  vuota per ora. Se mancante, le viste falliscono con un messaggio chiaro invece
  di dare un falso successo. Verificato l'intero flusso (comprese le due
  modalità di fallimento: hub non configurato, VPS non raggiungibile) con
  Django test client su SQLite in-memory.
- Aggiornamento 2026-07-08: il VPS Aruba è stato provisionato (vedi voce
  "Cambio provider VPS" sotto). Hub WireGuard `wg0` attivo, servizi systemd
  (`mkremote-web`, `mkremote-celery-worker`, `mkremote-celery-beat`) attivi.
  Verificato con un peer di prova (chiave WireGuard generata al volo,
  rimossa subito dopo il test): `assign_vpn_ip` assegna IP reale dal DB
  Postgres, `generate_wireguard_setup_script` produce uno script valido,
  `register_peer_on_hub` registra davvero il peer su `wg0` (verificato con
  `wg show wg0` e persistenza in `/etc/wireguard/wg0.conf`) passando
  attraverso una chiave SSH dedicata con forced-command ristretto (vedi
  `/usr/local/sbin/mkremote-wg-peer.sh` sul VPS), non root pieno.
- Aggiornamento 2026-07-08 (2): testato con un Mikrotik fisico reale
  ("router-lab", `10.0.0.122` sulla LAN dell'utente, non raggiungibile da
  internet). Flusso completo end-to-end tramite l'app vera (non shell/test
  isolato): script generato e incollato su WinBox dall'utente, chiave privata
  generata sul router e mai trasmessa, chiave pubblica incollata nell'app,
  peer registrato sul VPS, handshake WireGuard confermato (`wg show wg0` →
  peer con handshake riuscito), "Test connessione" ha eseguito una chiamata
  API RouterOS reale su `10.10.0.10:8728` e aggiornato `stato_connessione` a
  `connesso`. Il router non ha bisogno di IP pubblico né porte inoltrate:
  si collega in uscita al VPS, pattern standard hub-and-spoke.
- Cosa resta da fare: verificare che un secondo router non rompa il
  collegamento del primo (serve un secondo apparato Mikrotik).
- Stato: risolto per i criteri raggiungibili con un solo router; il test
  "secondo router non rompe il primo" resta aperto in attesa di hardware
  aggiuntivo

### [Fase 4] Saltata la Fase 3, prerequisiti formali non soddisfatti
- Contesto: l'utente ha chiesto esplicitamente di procedere con la Fase 4 senza
  aver affrontato la Fase 3 (blocco accesso pubblico) e senza che Fase 1/Fase 2
  siano "terminate" (sono entrambe `_da_finire` per il blocco VPS).
- Scelta di default adottata: proceduto come richiesto (fase_-1 regola 5 lo
  consente su richiesta esplicita). Il task di backup usa comunque solo
  `router.ip_vpn` per contattare il router (mai l'IP pubblico), come prescritto
  dalla nota della Fase 3, anche se il blocco firewall vero e proprio non è
  stato applicato.
- Stato: risolto (nel senso che non blocca — resta comunque da fare la Fase 3
  quando si vorrà davvero irrigidire la sicurezza)

### [Fase 4] Retention: scelta "ultimi N backup" invece di "ultimi X giorni"
- Contesto: la fase permette due criteri di retention alternativi validi.
- Scelta di default adottata: implementato solo `backup_retention_count`
  (ultimi N backup riusciti, per tipo binario/export separatamente), non anche
  una soglia a giorni, per non introdurre due meccanismi paralleli senza una
  richiesta esplicita.
- Stato: risolto (si può aggiungere in seguito un criterio a giorni se serve)

### [Fase 4] Object Storage non configurato, upload/retention S3 non testati con credenziali reali
- Contesto: l'utente ha scelto di procedere con placeholder `.env` vuoti per
  Hetzner Object Storage invece di fornire le credenziali reali subito.
- Scelta di default adottata: implementato il client S3 (boto3) dietro
  `ObjectStorageNotConfigured`, che fa fallire il backup con un errore
  registrato in `Backup.errore` invece di un falso successo. Verificato con
  test isolati (SQLite in-memory + Celery eager) che: la sincronizzazione del
  `PeriodicTask` su `intervallo_backup` funziona, il task di backup fallisce
  gestendo l'eccezione senza crashare quando il router non è raggiungibile, e
  la pulizia per retention rimuove correttamente i backup più vecchi oltre la
  soglia. Non verificato: upload/delete reali su Hetzner Object Storage (serve
  credenziali reali) e l'intero flusso con un router Mikrotik reale in VPN.
- Aggiornamento 2026-07-08: ritestando la sincronizzazione `PeriodicTask` sul
  VPS reale (Postgres + Celery veri, non SQLite in-memory), il segnale
  **non scattava**: bug reale, non emerso nel test isolato precedente. Causa:
  `post_save.connect()` usa per default una referenza debole (`weak=True`) al
  receiver; il receiver era una closure locale definita dentro
  `BackupsConfig.ready()`, senza nessun riferimento forte sopravvissuto dopo
  il return di `ready()` — il garbage collector la raccoglieva, disconnettendo
  il segnale in silenzio (probabilmente sopravvissuta per caso nel test breve
  precedente, prima che il GC ciclico girasse). Corretto spostando il
  receiver a livello di modulo (`backups.signals.router_post_save`) e
  aggiungendo `weak=False` per sicurezza. Riverificato sul VPS reale: ora
  funziona. Lezione: i test su SQLite in-memory/processi brevi non bastano a
  scovare bug di garbage collection sui signal — serve un ambiente a lungo
  termine come quello reale.
- Stato: object storage ancora rimandato (serve credenziali reali); resto
  del flusso backup verificato/corretto su infrastruttura reale

### [Fase 0] Cambio provider VPS: Aruba invece di Hetzner
- Contesto: i documenti di fase (fase_0, fase_4) indicano esplicitamente "VPS
  Hetzner Ubuntu 24.04" e "Hetzner Object Storage". L'utente ha deciso di usare
  un VPS Aruba invece di Hetzner.
- Scelta di default adottata: procediamo con il provisioning su Aruba. La
  questione dell'Object Storage per i backup (Fase 4) resta esplicitamente
  rimandata (nessun servizio scelto ancora: Aruba Object Storage, altro
  provider S3-compatibile, o Hetzner Object Storage lasciato separato). Nessun
  riferimento a "Hetzner" è hardcoded nel codice: i parametri (endpoint S3,
  IP/host VPS) sono tutti letti da `.env`, quindi il cambio provider non
  richiede modifiche al codice, solo ai valori di configurazione.
- Aggiornamento 2026-07-08: risolto anche l'Object Storage, vedi voce
  "[Fase 4] Storage backup: FTPS Aruba invece di Object Storage S3" più sotto.
- Stato: risolto

### [Fase 4] Storage backup: FTPS Aruba invece di Object Storage S3
- Contesto: l'utente ha uno spazio FTP già disponibile su Aruba
  (`ftp.fbosolution.it`) e ha chiesto di valutarlo al posto di un vero Object
  Storage S3-compatibile (mai provisionato).
- Opzioni valutate:
  - FTP semplice: sconsigliato, protocollo in chiaro, i backup contengono
    config router (potenzialmente dati sensibili) — avrebbe indebolito la
    postura di sicurezza del progetto (VPN-only, credenziali cifrate, SSH
    forced-command).
  - FTPS (FTP con `AUTH TLS` esplicito, stessa porta 21): verificato che il
    server Aruba lo supporta. Scelto perché cifra sia canale di controllo che
    dati (`prot_p()`), usa `ftplib` della standard library (nessuna nuova
    dipendenza), e lo spazio è già pagato/disponibile.
  - SFTP vero (porta 22, su SSH): non disponibile su questo spazio hosting
    condiviso Aruba (solo FTP/FTPS su porta 21).
- Problema emerso e risolto: l'account FTP non permette di creare cartelle
  nella root né nelle cartelle di backup automatico Aruba (sola lettura,
  probabilmente mirror del sito). L'unica area scrivibile è
  `www.fbosolution.it`, cioè la **webroot pubblica del sito aziendale** —
  salvarci i backup senza protezione li avrebbe resi scaricabili da chiunque
  via browser. Creata una sottocartella `mikrotik-backups/` con un
  `.htaccess` (`Require all denied` + `Deny from all`, doppia sintassi per
  compatibilità Apache 2.2/2.4) e **verificato con una richiesta HTTPS reale**
  che risulta `403 Forbidden` prima di caricare alcun backup vero.
- Implementazione: `backups/storage.py` riscritto con `ftplib.FTP_TLS` al
  posto di `boto3`; rimossa la dipendenza `boto3` da `requirements.txt`;
  campo modello `Backup.s3_key` rinominato in `storage_path` (migrazione di
  rename, non drop+create, nessun dato perso); `.env` aggiornato con
  `BACKUP_FTP_*` al posto di `BACKUP_S3_*`. Verificato upload+delete reali
  tramite il codice dell'app (non solo `ftplib` grezzo) contro lo spazio
  Aruba vero.
- Stato: risolto

### [Fase 4] Bug reale: sintassi errata chiamate librouteros in backup/export
- Contesto: testando il backup manuale su router-lab (hardware reale), tutti
  i tentativi fallivano con `'Path' object has no attribute 'call'`. Bug mai
  emerso prima perché senza VPS/router reale il task non era mai stato
  eseguito contro un router vero.
- Causa: `backups/tasks.py` usava `api.path('/system/backup').call('save',
  {'name': basename})`, ma `librouteros.api.Path` non ha un metodo `.call()`:
  è direttamente chiamabile (`__call__(self, cmd, **kwargs)`), quindi la
  sintassi corretta è `api.path('/system/backup')('save', name=basename)`
  (kwargs, non un dict posizionale).
- Verificato con chiamate dirette contro router-lab reale (`/system/backup
  save` e `/export file=...`) prima di correggere il codice, poi ripulito i
  file di test dal router.
- Stato: risolto

### [Fase 4] Chiusura fase: mancava il download, verificato l'automatico reale
- Contesto: verificando i criteri di completamento con router-lab reale, è
  emerso che la vista storico backup non aveva mai avuto il link di download
  richiesto esplicitamente da `fase_4_backup_automatici.md` — implementato
  ora (`backups/storage.py:download_backup_file`, vista
  `BackupDownloadView`), confermato funzionante dall'utente scaricando un
  backup vero dal browser.
- Verificato anche l'ultimo criterio rimasto aperto: backup **automatico**
  all'intervallo configurato (finora testato solo manualmente). Impostato
  temporaneamente `intervallo_backup=2 minuti` su router-lab, osservato nei
  log di Celery worker che il task è partito da solo alle 14:37:42 (nessun
  trigger manuale) ed è riuscito, poi ripristinato un intervallo di 24 ore.
- Tutti i criteri di completamento della Fase 4 sono ora verificati con dati
  reali: backup automatico, backup manuale, cifratura N/A qui (il file non è
  cifrato lato app, solo in transito via FTPS — vedi nota sotto), retention
  (verificata su SQLite in-memory in precedenza, logica invariata), download.
- Nota per il futuro: i file di backup su Aruba non sono cifrati a riposo
  (solo protetti da `.htaccess` + non pubblicati). Se in futuro serve difesa
  in profondità, valutare cifratura lato applicazione prima dell'upload.
- Stato: risolto — Fase 4 chiusa (`fase_4_backup_automatici_terminato.md`)

### [Fase 6] 2FA/conferma per l'apertura del terminale (dubbio rimandato dalla fase)
- Contesto: la fase suggerisce di "valutare un secondo fattore/conferma
  esplicita prima di aprire la sessione", trattandosi di un accesso
  privilegiato.
- Scelta di default adottata: implementata solo la conferma esplicita
  (pulsante "Apri sessione terminale" con avviso, nessuna connessione finché
  non viene cliccato), non un vero secondo fattore (TOTP). Coerente con la
  decisione già rimandata per il login stesso (2FA generale, vedi sezione
  "Rifiniture note già previste da subito" in cima a questo file).
- Stato: rimandato (2FA generale del progetto)

### [Fase 6] Bug reale: incompatibilità redis-py 8.x con channels_redis
- Contesto: testando il terminale su router-lab reale, la sessione WebSocket
  crashava dopo pochi secondi con `redis.exceptions.TimeoutError: Timeout
  reading from localhost:6379`, anche se il comando SSH non c'entrava nulla
  con Redis.
- Causa: `channels_redis` 4.3.0 implementa il proprio meccanismo di attesa
  messaggi con un `BZPOPMIN` a timeout 5s; `redis-py` 8.0.1 (versione molto
  recente, installata perché `requirements.txt` non aveva un limite
  superiore) genera un `TimeoutError` non gestito da channels_redis in
  quello scenario, che si propaga e termina il consumer — chiudendo la
  sessione SSH attiva in modo del tutto imprevedibile (non al primo comando,
  ma al primo momento di inattività >5s).
- Non emerso prima perché nessun test precedente (SQLite in-memory, Celery
  eager) usava realmente Channels/Redis in un processo a lunga esecuzione.
- Risolto fissando `redis>=5.0,<6.0` in `requirements.txt` (stessa libreria
  già usata con successo da Celery). Verificato con un test isolato che
  `channel_layer.receive()` non solleva più eccezioni oltre il timeout
  interno di 5s.
- Stato: risolto

### [Fase 6] Bug reale: sessioni SSH orfane su navigazione via dalla pagina
- Contesto: dopo aver navigato via dalla pagina del terminale (senza un
  pulsante di chiusura esplicito, che ancora non esisteva), la connessione
  SSH tra il VPS e il router restava aperta a tempo indeterminato
  (verificato con `ss -tnp` sul VPS: connessione ESTABLISHED persistente
  verso `10.10.0.10:22`), e il record di audit non risultava mai chiuso
  (`chiusa_il` restava `None`).
- Causa: il browser non invia sempre un frame di chiusura WebSocket pulito
  alla navigazione (bfcache e simili), quindi Django Channels non riceveva
  mai l'evento `websocket.disconnect` e il consumer restava vivo
  indefinitamente con la connessione SSH aperta.
- Risolto aggiungendo un listener `pagehide` (più affidabile di
  `beforeunload`, copre anche i casi di bfcache) che chiama esplicitamente
  `socket.close()`, più un pulsante "Chiudi sessione" per la chiusura
  manuale. Verificato in entrambi i casi (click esplicito e navigazione via)
  che: il record di audit risulta `chiusa_il` valorizzato, e `ss -tnp` sul
  VPS non mostra più connessioni residue verso il router.
- Stato: risolto

### [Fase 6] Chiusura fase
Tutti i criteri di completamento verificati su hardware reale (router-lab):
terminale funzionante con comandi reali eseguiti e risposta ricevuta, link
WebFig raggiungibile sull'IP VPN, sessioni chiuse correttamente senza
lasciare processi SSH orfani sul router (verificato sia con chiusura
esplicita che con navigazione via).

### [Fase 5] Verifica con hardware reale rimandata: prerequisito Fase 2 non chiuso
- Contesto: la Fase 5 richiede "Fase 2 (VPN) terminata almeno per i router da
  monitorare", ma `fase_2_script_wireguard` è ancora `_esecuzione_da_finire`.
  Su indicazione esplicita dell'utente si è comunque implementata tutta la
  logica applicativa (modelli, task Celery di polling, alert Telegram/email,
  dashboard e grafici), lasciando come sospeso solo ciò che richiede un
  router realmente raggiungibile in VPN.
- Cosa NON è stato ancora verificato con hardware reale: raccolta metriche via
  `librouteros` su un router vero, notifica effettiva entro il tempo atteso
  spegnendo/scollegando un router di test, comportamento di `/system/health`
  su modelli senza sensore di temperatura (gestito con `try/except` ma mai
  osservato su un router reale).
- Scelta di default adottata: implementazione completa e coerente con i
  pattern già in uso (stesso schema di `backups/tasks.py` per la connessione
  API, stesso schema di `backups/signals.py`+migration dati per la
  registrazione del `PeriodicTask` in `django-celery-beat`).
- Stato: rimandato — la fase resta `_esecuzione_da_finire` finché non è
  possibile ripetere la verifica fatta per Fase 4 su router-lab reale
  (idealmente dopo che Fase 2 sarà a sua volta chiusa).

### [Fase 5] Bug reale trovato in migrazione: `IntervalSchedule.SECONDS` non esiste sul modello storico
- Contesto: `monitoring/migrations/0002_poll_periodic_task.py` usa
  `apps.get_model('django_celery_beat', 'IntervalSchedule')` per registrare
  il `PeriodicTask` del polling, seguendo lo stesso schema già usato in
  `backups/migrations/0002_cleanup_periodic_task.py`. A differenza di
  quest'ultima (che usa solo stringhe letterali per `CrontabSchedule`), la
  migrazione di Fase 5 referenziava `IntervalSchedule.SECONDS`, una costante
  di classe definita solo sul modello Python reale — il modello "storico"
  restituito da `apps.get_model()` è una ricostruzione a partire dallo stato
  delle migrazioni e non porta con sé costanti di classe non serializzate,
  causando `AttributeError: type object 'IntervalSchedule' has no attribute
  'SECONDS'` al primo `migrate` sul VPS.
- Non emerso prima perché mai eseguito contro un database reale: gli unici
  controlli pre-merge erano stati `manage.py check` e
  `makemigrations --check`, che non eseguono le `RunPython` delle migrazioni
  dati.
- Fix: sostituita la costante con il valore letterale `'seconds'` (verificato
  in `django_celery_beat/models.py: SECONDS = 'seconds'`), coerente con
  l'approccio già in uso per `CrontabSchedule`.
- Stato: risolto e verificato — `migrate` applicato con successo sul VPS,
  `PeriodicTask` "monitoring-poll-routers" creato correttamente (ogni 120s).

### [Fase 5] Chiusura fase: verifica end-to-end su hardware reale (router-lab)
- Prerequisito Fase 2 nel frattempo soddisfatto (router-lab collegato via
  WireGuard, `ip_vpn=10.10.0.10`): eseguita la verifica end-to-end rimandata
  in precedenza.
- Merge di PR #1 (lavoro della sessione parallela sulla worktree
  `fase5-monitoraggio`), deploy sul VPS (`git pull`, `migrate`,
  `collectstatic`, restart `mkremote-web`/`mkremote-celery-worker`/
  `mkremote-celery-beat`).
- Verificato con `poll_routers_task()` invocato manualmente: raccolta reale
  via `librouteros` su router-lab — CPU 0%, RAM ~350MB/1GB, uptime ~4h54m,
  temperatura 32°C (quindi `/system/health` con sensore di temperatura
  presente e letto correttamente), contatori traffico per interfaccia
  (`lo`, `ether1-4`, ecc.).
- Verificato il rilevamento offline: simulati 3 fallimenti di polling
  consecutivi (soglia configurata) → router marcato `offline` e
  `AlertEvent` di tipo `offline` aperto; un successivo poll reale riuscito
  riporta lo stato a `connesso`, azzera il contatore e chiude l'alert.
- Verificato l'alert CPU: soglia temporaneamente forzata a 0% → alert
  `cpu_alta` aperto; soglia ripristinata a 90% e nuovo poll → alert chiuso.
  Stessa logica (condivisa) vale per `temperatura_alta` e per
  `backup_fallito` (già agganciato a `backups/tasks.py`).
- Verificato che il `PeriodicTask` gira autonomamente in produzione (non
  solo per invocazione manuale): log di `mkremote-celery-beat` mostra
  "Sending due task monitoring-poll-routers" ogni 120s, log del worker
  mostra il task ricevuto ed eseguito con successo, nuova `RouterMetric`
  salvata nel DB con timestamp coerente.
- Verificate le pagine reali via HTTP autenticato: dashboard
  `/monitoraggio/` mostra router-lab con stato "Connesso" e CPU reale;
  pagina dettaglio `/monitoraggio/router/<pk>/` e endpoint JSON
  `dati.json` (usato dai grafici Chart.js) rispondono con i dati storici
  reali.
- **Non verificato**: invio effettivo di notifiche Telegram/email reali.
  L'utente ha scelto esplicitamente di non fornire credenziali (bot token
  Telegram, SMTP) in questa sessione di verifica; la logica di
  apertura/chiusura alert e di anti-spam a cooldown (`_should_notify`) è
  stata verificata a livello di modello/DB, ma non l'effettiva consegna dei
  messaggi. Da verificare quando saranno disponibili credenziali reali,
  configurabili da interfaccia in "Impostazioni alert".
  router-lab lasciato collegato e in stato "connesso" al termine dei test,
  come da indicazione data per le fasi precedenti.
- Stato: chiusa. Rinominato
  `fase_5_monitoraggio_alert_esecuzione_da_finire.md` →
  `fase_5_monitoraggio_alert_terminato.md`.
