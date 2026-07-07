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
- Cosa resta da fare quando il VPS sarà pronto: valorizzare le variabili env,
  testare lo script su un router Mikrotik reale, verificare che un secondo
  router non rompa il primo, verificare "Test connessione" con un router vero
  raggiungibile in VPN.
- Stato: rimandato
