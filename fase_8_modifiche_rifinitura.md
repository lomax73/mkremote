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
